from ct.models import FSM

class FSMSpecification(object):
    'convenience class for specifying an FSM graph, loading it'
    def __init__(self, name, title, nodeDict=None, edges=None,
                 pluginNodes=(), attrs=('help', 'path', 'data', 'doLogging'),
                 **kwargs):
        kwargs['name'] = name
        kwargs['title'] = title
        self.fsmData = kwargs
        if not nodeDict:
            nodeDict = {}
        if not edges:
            edges = []
        for node in pluginNodes: # expect list of node class objects
            modName = node.__module__.split('.')[-1]
            name = node.__name__
            d = dict(title=node.title, funcName=modName + '.' + name,
                     description=getattr(node, '__doc__', None))
            for attr in attrs: # save node attributes
                if hasattr(node, attr):
                    d[attr] = getattr(node, attr)
            nodeDict[name] = d
            for e in getattr(node, 'edges', ()):
                e = e.copy() # prevent side effects
                e['fromNode'] = name
                edges.append(e)
        self.nodeData = nodeDict
        self.edgeData = edges
    def save_graph(self, *args, **kwargs):
        'load this FSM specification into the database'
        return FSM.save_graph(self.fsmData, self.nodeData, self.edgeData,
                                   *args, **kwargs)
            
class CallerNode(object):
    'base class for node representing a call to a sub-FSM'
    def exceptCancel_edge(self, edge, fsmStack, request, **kwargs):
        'implements default behavior: if sub-FSM cancelled, we cancel too'
        fsmStack.pop(request, eventName='exceptCancel') # cancel this FSM
        return edge.toNode
    
