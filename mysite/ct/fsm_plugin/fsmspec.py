from ct.models import FSM

class FSMSpecification(object):
    'convenience class for specifying an FSM graph, loading it'
    def __init__(self, name, title, nodeDict=None, edges=None,
                 pluginNodes=(), **kwargs):
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
            d = dict(title=node.title, funcName=modName + '.' + name)
            d['description'] = getattr(node, '__doc__', None)
            d['help'] = getattr(node, 'help', None)
            d['path'] = getattr(node, 'path', None)
            d['data'] = getattr(node, 'data', None)
            nodeDict[name] = d
            for e in getattr(node, 'edges', ()):
                e['fromNode'] = name
                edges.append(e)
        self.nodeData = nodeDict
        self.edgeData = edges
    def save_graph(self, *args, **kwargs):
        'load this FSM specification into the database'
        return FSM.save_graph(self.fsmData, self.nodeData, self.edgeData,
                                   *args, **kwargs)
            
