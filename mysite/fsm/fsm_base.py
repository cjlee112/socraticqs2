"""Module contains FSMStack object - main interface to our current FSM if any

FSMStack methods:
  * ``event`` - top-level interface for passing event to a running FSM instance
  * ``push`` - start running a new FSM instance (layer)
  * ``pop`` - pop current FSM state and pass event to next stack state if any
  * ``resume`` - resume an orphaned activity
  * ``get_current_url`` - get URL for resuming at current FSM state
"""
from fsm.models import FSM, FSMState, FSMBadUserError, FSMStackResumeError


class FSMStack(object):
    """
    Main interface to our current FSM if any.
    """
    def __init__(self, request, **kwargs):
        try:
            fsmID = request.session['fsmID']
        except KeyError:
            self.state = None
            return
        try:
            self.state = FSMState.objects.select_related('fsmNode')\
                             .prefetch_related('fsmNode__outgoing').get(pk=fsmID)
        except FSMState.DoesNotExist:
            del request.session['fsmID']
            self.state = None
            return
        for edge in self.state.fsmNode.outgoing.all():  # detect selection edges
            if edge.name.startswith('select_'):
                setattr(self, edge.name, edge)  # make available to HTML templates

    def event(self, request, eventName='next', pageData=None, **kwargs):
        """Top-level interface for passing event to a running FSM instance

        If FSM handles this event, return a redirect that over-rides
        the generic UI behavior.  Otherwise return None,
        indicating NO over-ride of generic UI behavior.
        """
        if self.state is None:  # no ongoing activity
            return
        state = self.state  # remember current state
        path = self.state.event(
            self, request, eventName, pageData=pageData, **kwargs
        )
        if self.state and self.state != state:  # pushed or popped
            path = self.state.path  # use path of new FSM
        if self.state.fsmNode.name == 'END':  # reached terminal state
            pageData.set_refresh_timer(request, False)  # reset timer if on
            if self.state.fsmNode.help:  # save its help message
                request.session['statusMessage'] = self.state.fsmNode.help
            parentPath = self.pop(request, pageData=pageData)
            if parentPath:  # let parent FSM redirect us to its current state
                return parentPath
        return path

    def push(self, request, fsmName, stateData=None, startArgs=None,
             activity=None, **kwargs):
        """
        Start running a new FSM instance (layer).
        """
        stateData = stateData or {}
        startArgs = startArgs or {}
        fsm = FSM.objects.select_related('startNode').get(name=fsmName)
        activity = None
        if not activity and self.state and fsmName not in ('chat', 'additional'):
            activity = self.state.activity
        self.state = FSMState(
            user=request.user,
            fsmNode=fsm.startNode,
            parentState=self.state,
            activity=activity,
            title=fsm.title,
            hideTabs=fsm.hideTabs,
            hideLinks=fsm.hideLinks,
            hideNav=fsm.hideNav,
            **kwargs
        )
        # if fsmName == 'live_chat':
        #     #NOTE: do we really should use .first() here?
        #     self.state.linkState = self.state.find_live_sessions(request.user).first()
        path = self.state.start_fsm(self, request, stateData, **startArgs)
        if fsmName not in ('chat', 'additional'):
            request.session['fsmID'] = self.state.pk
        return path

    def pop(self, request, eventName='return', pageData=None, **kwargs):
        """
        Pop current FSM state and pass event to next stack state if any.
        """
        nextState = self.state.parentState
        self.state.delete()
        self.state = nextState
        if nextState is not None:
            request.session['fsmID'] = nextState.pk
            return self.event(request, eventName, pageData, **kwargs)
        else:
            del request.session['fsmID']

    def resume(self, request, stateID):
        """
        Resume an orphaned activity.
        """
        state = FSMState.objects.get(pk=int(stateID))
        if state.user_id != request.user.id:
            raise FSMBadUserError('user mismatch!!')
        elif state.children.count() > 0:
            raise FSMStackResumeError('can only resume innermost stack level')
        self.state = state
        request.session['fsmID'] = self.state.pk
        return self.get_current_url()

    def get_current_url(self):
        """
        Get URL for resuming at current FSM state.
        """
        if self.state:
            return self.state.path
