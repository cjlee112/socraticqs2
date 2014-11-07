import models
from django.http import HttpResponseRedirect

class FSMStack(object):
    def __init__(self, request, **kwargs):
        try:
            fsmID = request.session['fsmID']
        except KeyError:
            self.state = None
            return
        self.state = models.FSMState.objects.get(pk=fsmID)
    def transition(self, request, name='next', **kwargs):
        if self.state is None: # no ongoing activity
            return
        try:
            path = self.state.transition(name, **kwargs)
        except models.FSMDone:
            return self.pop(request, **kwargs)
        if path:
            return HttpResponseRedirect(path)
    def push(self, request, fsmName, stateArgs, **kwargs):
        fsm = models.FSM.objects.get(name=fsmName)
        state = models.FSMState(user=request.user, fsmNode=fsm.startNode,
                                parentState=self.state, **stateArgs)
        state.save()
        self.state = state
        request.session['fsmID'] = state.pk
        path = fsm.startNode.get_path(**kwargs)
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
        
        
