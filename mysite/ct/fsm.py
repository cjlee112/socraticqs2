import models
from django.http import HttpResponseRedirect

class FSMStack(object):
    'main interface to our current FSM if any'
    def __init__(self, request, **kwargs):
        try:
            fsmID = request.session['fsmID']
        except KeyError:
            self.state = None
            return
        self.state = models.FSMState.objects.get(pk=fsmID)
    def event(self, request, eventName='next', **kwargs):
        'top-level interface for passing event to a running FSM instance'
        if self.state is None: # no ongoing activity
            return
        try:
            path = self.state.event(self, request, eventName, **kwargs)
        except models.FSMDone:
            return self.pop(request, **kwargs)
        if path:
            return HttpResponseRedirect(path)
    def push(self, request, fsmName, stateData={}, startArgs={}, **kwargs):
        'start running a new FSM instance (layer)'
        fsm = models.FSM.objects.get(name=fsmName)
        self.state = models.FSMState(user=request.user, fsmNode=fsm.startNode,
                                parentState=self.state, **kwargs)
        path = self.state.start_fsm(self, request, stateData, **startArgs)
        request.session['fsmID'] = self.state.pk
        return HttpResponseRedirect(path)
    def pop(self, request, **kwargs):
        if request.user != self.state.user:
            raise ValueError('user mismatch for FSMStack.pop()')
        nextState = self.state.parentState
        self.state.delete()
        self.state = nextState
        if nextState is not None:
            request.session['fsmID'] = nextState.pk
            path = nextState.fsmNode.get_path(**kwargs)
            return HttpResponseRedirect(path)
        else:
            del request.session['fsmID']
        
        
