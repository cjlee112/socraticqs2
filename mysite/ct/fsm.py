from models import FSM, FSMState, FSMBadUserError, FSMStackResumeError

class FSMStack(object):
    'main interface to our current FSM if any'
    def __init__(self, request, **kwargs):
        try:
            fsmID = request.session['fsmID']
        except KeyError:
            self.state = None
            return
        try:
            self.state = FSMState.objects.get(pk=fsmID)
        except FSMState.DoesNotExist:
            del request.session['fsmID']
            self.state = None
            return
        for e in self.state.fsmNode.outgoing.all(): # detect selection edges
            if e.name.startswith('select_'):
                setattr(self, e.name, e) # make available to HTML templates
    def event(self, request, eventName='next', **kwargs):
        '''top-level interface for passing event to a running FSM instance.
        If FSM handles this event, return a redirect that over-rides
        the generic UI behavior.  Otherwise return None,
        indicating NO over-ride of generic UI behavior.'''
        if self.state is None: # no ongoing activity
            return
        path = self.state.event(self, request, eventName, **kwargs)
        if self.state.fsmNode.name == 'END': # reached terminal state
            if self.state.fsmNode.help: # save its help message
                request.session['statusMessage'] = self.state.fsmNode.help
            parentPath = self.pop(request)
            if parentPath: # let parent FSM redirect us to its current state
                return parentPath
        return path
    def push(self, request, fsmName, stateData={}, startArgs={}, **kwargs):
        'start running a new FSM instance (layer)'
        fsm = FSM.objects.get(name=fsmName)
        self.state = FSMState(user=request.user, fsmNode=fsm.startNode,
                parentState=self.state, title=fsm.title, hideTabs=fsm.hideTabs,
                hideLinks=fsm.hideLinks, hideNav=fsm.hideNav, **kwargs)
        path = self.state.start_fsm(self, request, stateData, **startArgs)
        request.session['fsmID'] = self.state.pk
        return path
    def pop(self, request, eventName='pop', **kwargs):
        'pop current FSM state and pass event to next stack state if any'
        nextState = self.state.parentState
        self.state.delete()
        self.state = nextState
        if nextState is not None:
            request.session['fsmID'] = nextState.pk
            return self.event(request, eventName, **kwargs)
        else:
            del request.session['fsmID']
    def resume(self, request, stateID):
        'resume an orphaned activity'
        state = FSMState.objects.get(pk=int(stateID))
        if state.user != request.user:
            raise FSMBadUserError('user mismatch!!')
        elif state.children.count() > 0:
            raise FSMStackResumeError('can only resume innermost stack level')
        self.state = state
        request.session['fsmID'] = self.state.pk
        return self.get_current_url()
    def get_current_url(self):
        'get URL for resuming at current FSM state'
        if self.state:
            return self.state.path
        
