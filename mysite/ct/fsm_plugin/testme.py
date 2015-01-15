
class Trivial(object):
    'for automated test suite testing only'
    def get_path(self, node, state, request, **kwargs):
        return '/ct/some/where/else/'
    def start(self, node, fsmStack, request, **kwargs):
        return '/ct/trivial/'
