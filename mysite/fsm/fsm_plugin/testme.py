from fsm.fsmspec import FSMSpecification


class START(object):
    """
    Example node plugin for automated test suite testing only.
    We adopt a convention of NODE names in ALL-CAPS and
    edge names in lower-case.
    This represents a START node.
    """
    def get_path(self, node, state, request, **kwargs):
        """
        Provide this method to generate URL for a node programmatically.
        """
        return '/ct/some/where/else/'

    def start_event(self, node, fsmStack, request, **kwargs):
        """
        Example event plugin method to intercept start event.
        """
        # do whatever analysis you want...
        # then if you want to trigger a transition, call it directly
        return fsmStack.state.transition(fsmStack, request, 'next', **kwargs)
        # otherwise just return None to indicate that generic UI
        # behavior should just continue as normal (i.e. your FSM is
        # not intercepting and redirecting this event.

    def next_edge(self, edge, fsmStack, request, **kwargs):
        """
        Example edge plugin method to execute named transition.
        """
        # do whatever processing you want...
        fsm = edge.fromNode.fsm
        mid = fsm.get_node('MID')
        return mid  # finally return whatever destination node you want
    # node specification data goes here
    title = 'start here'
    path = 'ct:home'
    doLogging = True
    edges = (
        dict(name='next', toNode='END', title='go go go'),
    )


class MID(object):
    def next_filter(self, edge, obj):
        """
        Example edge filter_input method to check whether input is acceptable.
        """
        return obj == 'the right stuff'
    def get_help(self, node, state, request):
        path_help = {
            '/ct/about/': 'here here!',
            '/ct/courses/1/': 'there there'
        }
        return path_help.get(request.path, None)

    title = 'in the middle'
    path = 'ct:about'
    edges = (
        dict(name='next', toNode='END', title='go go go'),
    )


def get_specs():
    'get FSM specifications stored in this file'
    spec = FSMSpecification(
        name='test', title='try this',
        pluginNodes=[START, MID],  # nodes w/ plugin code
        nodeDict=dict(  # all other nodes
            END=dict(title='end here', path='ct:home'),
        ),
    )
    return (spec,)


# sub-FSM example code

class CALLER(object):
    def call_edge(self, edge, fsmStack, request, **kwargs):
        node = edge.toNode
        node._path = fsmStack.push(request, 'SUBFSMNAME')
        return node
    edges = (
        dict(name='call', toNode='WAITER', title='start a sub-fsm'),
    )


class WAITER(object):
    def get_path(self, node, state, request, **kwargs):
        """
        Hand back stored URL of our sub-FSM.
        """
        return self._path

    edges = (
        dict(
            name='subfsmdone',
            toNode='SOMENODE',
            title='continue after sub-fsm done'),
    )
