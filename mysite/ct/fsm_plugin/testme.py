
class START(object):
    '''example node plugin for automated test suite testing only.
    We adopt a convention of NODE names in ALL-CAPS and
    edge names in lower-case.
    This represents a START node.'''
    def get_path(self, node, state, request, **kwargs):
        'provide this method to generate URL for a node programmatically'
        return '/ct/some/where/else/'
    def start_event(self, node, fsmStack, request, **kwargs):
        'example event plugin method to intercept start event.'
        # do whatever analysis you want...
        # then if you want to trigger a transition, call it directly
        return fsmStack.state.transition(request, 'next', **kwargs)
        # otherwise just return None to indicate that generic UI
        # behavior should just continue as normal (i.e. your FSM is
        # not intercepting and redirecting this event.
    def next_edge(self, edge, state, request, **kwargs):
        'example edge plugin method to execute named transition'
        # do whatever processing you want...
        fsm = edge.fromNode.fsm
        mid = fsm.fsmnode_set.get(name='MID')
        return mid # finally return whatever destination node you want


    
