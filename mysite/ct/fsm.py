import models

class FSMStack(object):
    'main interface to our current FSM if any'
    def __init__(self, request, **kwargs):
        try:
            fsmID = request.session['fsmID']
        except KeyError:
            self.state = None
            return
        try:
            self.state = models.FSMState.objects.get(pk=fsmID)
        except models.FSMState.DoesNotExist:
            del request.session['fsmID']
            self.state = None
    def event(self, request, eventName='next', **kwargs):
        '''top-level interface for passing event to a running FSM instance.
        If FSM handles this event, return a redirect that over-rides
        the generic UI behavior.  Otherwise return None,
        indicating NO over-ride of generic UI behavior.'''
        if self.state is None: # no ongoing activity
            return
        path = self.state.event(self, request, eventName, **kwargs)
        if self.state.fsmNode.name == 'END': # reached terminal state
            self.pop(request)
        return path
    def push(self, request, fsmName, stateData={}, startArgs={}, **kwargs):
        'start running a new FSM instance (layer)'
        fsm = models.FSM.objects.get(name=fsmName)
        self.state = models.FSMState(user=request.user, fsmNode=fsm.startNode,
                                parentState=self.state, **kwargs)
        path = self.state.start_fsm(self, request, stateData, **startArgs)
        request.session['fsmID'] = self.state.pk
        return path
    def pop(self, request, **kwargs):
        nextState = self.state.parentState
        self.state.delete()
        self.state = nextState
        if nextState is not None:
            request.session['fsmID'] = nextState.pk
        else:
            del request.session['fsmID']
    def get_current_url(self):
        'get URL for resuming at current FSM state'
        if self.state:
            return self.state.path
        
