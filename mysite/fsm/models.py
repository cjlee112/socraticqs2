import json

from django.utils import timezone
from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from ct.ct_util import reverse_path_args
from ct.models import (
    Role,
    Unit,
    Course,
    Lesson,
    Concept,
    Response,
    CourseUnit,
    UnitStatus,
    UnitLesson,
    ConceptLink,
    StudentError,
    ConceptGraph
)


def dump_json_id(o, name=None):
    """
    Produce tuple of form ("NAME_Response_id", o.pk).
    """
    l = []
    if name:
        l.append(name)
    name = '_'.join(l + [o.__class__.__name__, 'id'])
    return (name, o.pk)


def dump_json_id_dict(d):
    """
    Get json representation of dict of db objects.
    """
    data = {}
    for k, v in d.items():
        if v.__class__.__name__ in klassNameDict:  # save db object id
            name, pk = dump_json_id(v, k)
            data[name] = pk
        else:  # just copy literal value, assuming JSON can serialize it
            data[k] = v
    return json.dumps(data)


def save_json_data(self, d=None, attr='data', doSave=True):
    """
    Save dict of object refs back to db blob field.
    """
    dictAttr = '_%s_dict' % attr
    if d is None:  # save cached data
        d = getattr(self, dictAttr)
    else:  # save specified dict
        setattr(self, dictAttr, d)  # cache on local object
    if d:
        s = dump_json_id_dict(d)
    else:
        s = None
    setattr(self, attr, s)
    if doSave:  # immediately write to db
        self.save()


# index of types that can be saved in json blobs
klassNameDict = dict(
    Unit=Unit,
    Role=Role,
    Course=Course,
    Lesson=Lesson,
    Concept=Concept,
    Response=Response,
    UnitLesson=UnitLesson,
    ConceptLink=ConceptLink,
    ConceptGraph=ConceptGraph,
    StudentError=StudentError,
    CourseUnit=CourseUnit,
    UnitStatus=UnitStatus,
)


def load_json_id(name, pk):
    """
    Get the specified object as (label, obj) tuple.
    """
    l = name.split('_')
    klassName = l[-2]
    o = klassNameDict[klassName].objects.get(pk=pk)
    return (l[0], o)


def load_json_id_dict(s):
    """
    Get dict of db objects from json blob representation.
    """
    data = json.loads(s)
    d = {}
    for k, v in data.items():
        if k.endswith('_id'):  # retrieve db object
            name, obj = load_json_id(k, v)
            d[name] = obj
        else:  # just copy literal value
            d[k] = v
    return d


def load_json_data(self, attr='data'):
    """
    Get dict of db objects from json blob field.
    """
    dictAttr = '_%s_dict' % attr
    try:
        return getattr(self, dictAttr)
    except AttributeError:
        pass
    s = getattr(self, attr)
    if s:
        d = load_json_id_dict(s)
    else:
        d = {}
    setattr(self, dictAttr, d)
    return d


def set_data_attr(self, attr, v):
    """Set a single data attribute

    Must later call save_json_data() to serialize.
    """
    d = self.load_json_data()
    d[attr] = v


def get_data_attr(self, attr):
    """
    Get a single data attribute from json data.
    """
    d = self.load_json_data()
    return d[attr]


def get_plugin(funcName, prefix='fsm.fsm_plugin.'):
    """
    Import and call plugin func for this object.
    """
    import importlib
    if not funcName:
        raise ValueError('invalid call_plugin() with no funcName!')
    i = funcName.rindex('.')
    modName = prefix + funcName[:i]
    funcName = funcName[i + 1:]
    mod = importlib.import_module(modName)
    return getattr(mod, funcName)


class FSM(models.Model):
    """
    Finite State Machine top-level state-graph container.
    """
    name = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True)
    help = models.TextField(null=True)
    startNode = models.ForeignKey('FSMNode', related_name='+', null=True)
    hideTabs = models.BooleanField(default=False)
    hideLinks = models.BooleanField(default=False)
    hideNav = models.BooleanField(default=False)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    addedBy = models.ForeignKey(User)

    @classmethod
    def save_graph(klass, fsmData, nodeData, edgeData, username, fsmGroups=(),
                   oldLabel='OLD'):
        """Store FSM specification from node

        Store FSM specification from node, edge graph
        by renaming any existing
        FSM with the same name, and creating new FSM.
        Note that ongoing activities
        using the old FSM will continue to work (following the old FSM spec),
        but any new activities will be created using the new FSM spec
        (since they request it by name).
        """
        user = User.objects.get(username=username)
        name = fsmData['name']
        oldName = name + oldLabel
        with transaction.atomic():  # rollback if db error occurs
            try:  # delete nameOLD FSM if any
                old = klass.objects.get(name=oldName)
            except klass.DoesNotExist:
                pass
            else:
                old.delete()
            try:  # rename current to nameOLD
                old = klass.objects.get(name=name)
            except klass.DoesNotExist:
                pass
            else:
                old.name = oldName
                old.save()
                for g in old.fsmgroup_set.all():
                    g.delete()
                # old.fsmgroup_set.clear() # RelatedManager has no attribute clear
            f = klass(addedBy=user, **fsmData)  # create new FSM
            f.save()
            for groupName in fsmGroups:  # register in specified groups
                f.fsmgroup_set.create(group=groupName)
            nodes = {}
            for name, nodeDict in nodeData.items():  # save nodes
                node = FSMNode(name=name, fsm=f, addedBy=user, **nodeDict)
                if node.funcName:  # make sure plugin imports successfully
                    get_plugin(node.funcName)
                node.save()
                nodes[name] = node
                if name == 'START':
                    f.startNode = node
                    f.save()
            for edgeDict in edgeData:  # save edges
                edgeDict = edgeDict.copy()  # don't modify input dict!
                edgeDict['fromNode'] = nodes[edgeDict['fromNode']]
                edgeDict['toNode'] = nodes[edgeDict['toNode']]
                e = FSMEdge(addedBy=user, **edgeDict)
                e.save()
        return f

    def get_node(self, name):
        """
        Get node in this FSM with specified name.
        """
        return self.fsmnode_set.get(name=name)


class FSMGroup(models.Model):
    """
    Groups multiple FSMs into one named UI group.
    """
    fsm = models.ForeignKey(FSM)
    group = models.CharField(max_length=64)


class PluginDescriptor(object):
    """
    Self-caching plugin access property.
    """
    def __get__(self, obj, objtype):
        try:
            return obj._pluginData
        except AttributeError:
            if not obj.funcName:
                raise AttributeError('no plugin funcName')
            klass = get_plugin(obj.funcName)
            obj._pluginData = klass()
            return obj._pluginData

    def __set__(self, obj, val):
        raise AttributeError('read only attribute!')


class FSMNode(models.Model):
    """
    Stores one node of an FSM state-graph.
    """
    fsm = models.ForeignKey(FSM)
    name = models.CharField(max_length=64)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True)
    help = models.TextField(null=True)
    path = models.CharField(max_length=200, null=True)
    data = models.TextField(null=True)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    addedBy = models.ForeignKey(User)
    funcName = models.CharField(max_length=200, null=True)
    doLogging = models.BooleanField(default=False)
    load_json_data = load_json_data
    save_json_data = save_json_data
    get_data_attr = get_data_attr
    set_data_attr = set_data_attr
    _plugin = PluginDescriptor()  # provide access to plugin code if any

    def event(self, fsmStack, request, eventName, **kwargs):
        """
        Process event using plugin if available, otherwise generic processing.
        """
        if self.funcName:  # use plugin to process event
            if eventName:
                func = getattr(self._plugin, eventName + '_event', None)
            else:  # let plugin intercept render event
                func = getattr(self._plugin, 'render_event', None)
            if func is not None:
                return func(self, fsmStack, request, **kwargs)
        if eventName == 'start':  # default: just return our path
            return self.get_path(fsmStack.state, request, **kwargs)
        elif eventName:  # default: call transition with matching name
            return fsmStack.state.transition(fsmStack, request, eventName,
                                             **kwargs)

    def get_path(self, state, request, defaultURL=None, **kwargs):
        """
        Get URL for this page.
        """
        if self.path and self.path.startswith('fsm:fsm_'):  # serve fsm node view
            return reverse(self.path, kwargs=dict(node_id=self.pk))
        try:
            func = self._plugin.get_path
        except AttributeError:  # use self.path with clever reverse()
            if not self.path:  # just use default path
                if defaultURL:
                    return defaultURL
                else:
                    raise ValueError('node has no path, and no defaultURL')
            kwargs.update(state.get_all_state_data())  # pass state data too
            return reverse_path_args(self.path, request.path, **kwargs)
        else:  # use the plugin
            return func(self, state, request, defaultURL=defaultURL, **kwargs)

    def get_help(self, state, request):
        """
        Get FSM help message for current view, if any.
        """
        try:  # use plugin if available
            func = self._plugin.get_help
        except AttributeError:  # no plugin, so use default rule
            if state.fsm_on_path(request.path):  # on current node view?
                return self.help  # use node's help message if any
        else:
            return func(self, state, request)


class FSMDone(ValueError):
    pass


class FSMBadUserError(ValueError):
    """
    Request.user does not match state.user.
    """
    pass


class FSMStackResumeError(ValueError):
    pass


class FSMEdge(models.Model):
    """
    Stores one edge of an FSM state-graph.
    """
    name = models.CharField(max_length=64)
    fromNode = models.ForeignKey(FSMNode, related_name='outgoing')
    toNode = models.ForeignKey(FSMNode, related_name='incoming')
    title = models.CharField(max_length=200)
    description = models.TextField(null=True)
    help = models.TextField(null=True)
    showOption = models.BooleanField(default=False)
    data = models.TextField(null=True)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    addedBy = models.ForeignKey(User)
    _funcDict = {}
    load_json_data = load_json_data
    save_json_data = save_json_data
    get_data_attr = get_data_attr
    set_data_attr = set_data_attr

    def transition(self, fsmStack, request, **kwargs):
        """
        Execute edge plugin code if any and return destination node.
        """
        try:
            func = getattr(self.fromNode._plugin, self.name + '_edge')
        except AttributeError:  # just return target node
            return self.toNode
        else:
            return func(self, fsmStack, request, **kwargs)


class FSMState(models.Model):
    """
    Stores current state of a running FSM instance.
    """
    user = models.ForeignKey(User)
    fsmNode = models.ForeignKey(FSMNode)
    parentState = models.ForeignKey('FSMState', null=True,
                                    related_name='children')
    linkState = models.ForeignKey('FSMState', null=True,
                                  related_name='linkChildren')
    unitLesson = models.ForeignKey('ct.UnitLesson', null=True)
    title = models.CharField(max_length=200)
    path = models.CharField(max_length=200)
    data = models.TextField(null=True)
    hideTabs = models.BooleanField(default=False)
    hideLinks = models.BooleanField(default=False)
    hideNav = models.BooleanField(default=False)
    isLiveSession = models.BooleanField(default=False)
    atime = models.DateTimeField('time started', default=timezone.now)
    activity = models.ForeignKey('ActivityLog', null=True)
    activityEvent = models.ForeignKey('ActivityEvent', null=True)
    load_json_data = load_json_data
    save_json_data = save_json_data
    get_data_attr = get_data_attr
    set_data_attr = set_data_attr

    def get_all_state_data(self):
        """
        Get dict of all our state data including unitLesson.
        """
        d = self.load_json_data().copy()  # copy to avoid side-effects
        if self.unitLesson:
            d['unitLesson'] = self.unitLesson
        return d

    def event(self, fsmStack, request, eventName, unitLesson=False, **kwargs):
        """
        Trigger proper consequences if any for this event, return URL if any.
        """
        if not eventName:  # render event
            self.log_entry(request.user)
        elif unitLesson is not False:  # store new lesson binding
            self.unitLesson = kwargs['unitLesson'] = unitLesson
            self.save()
        elif eventName.startswith('select_'):  # store selected object
            className = eventName[7:]
            attr = className[0].lower() + className[1:]
            self.set_data_attr(attr, kwargs[attr])
            self.save_json_data()
        return self.fsmNode.event(fsmStack, request, eventName, **kwargs)

    def start_fsm(self, fsmStack, request, stateData, **kwargs):
        """
        Initialize new FSM by calling START node and saving state data to db.
        """
        if stateData:
            self.save_json_data(stateData, doSave=False)  # cache
        self.path = self.event(fsmStack, request, 'start', **kwargs)
        self.save_json_data(doSave=False)  # serialize to json blob
        self.save()
        return self.path

    def transition(self, fsmStack, request, name, **kwargs):
        """
        Execute the specified transition and return destination URL.
        """
        try:
            e = self.fsmNode.outgoing.get(name=name)
        except FSMEdge.DoesNotExist:
            return None  # FSM does not handle this event, return control
        if self.activityEvent:  # record exit from this node
            self.activityEvent.log_exit_event(name)
            self.activityEvent = None
        self.fsmNode = e.transition(fsmStack, request, **kwargs)
        self.path = self.fsmNode.get_path(self, request, **kwargs)
        self.save()
        return self.path

    def fsm_on_path(self, path):
        """
        True if we are on same page as current node.
        """
        return self.path == path

    def log_entry(self, user):
        """
        Record entry to this node if fsmNode.doLogging True.
        """
        if not self.fsmNode.doLogging:
            return
        if self.activityEvent and self.activityEvent.nodeName == self.fsmNode.name:
            return
        # NB: should probably extract unitLesson ID from request.path!!
        if self.activity:  # record to existing activity
            self.activityEvent = ActivityEvent(
                activity=self.activity,
                user=user,
                nodeName=self.fsmNode.name,
                unitLesson=self.unitLesson
            )
            self.activityEvent.save()
        else:  # create new activity log
            self.activityEvent = ActivityLog.log_node_entry(
                self.fsmNode, user, self.unitLesson
            )
            self.activity = self.activityEvent.activity
        self.save()

    @classmethod
    def find_live_sessions(klass, user):
        """
        Get live sessions relevant to this user.
        """
        return klass.objects.filter(
            isLiveSession=True, activity__course__role__user=user
        )


class ActivityLog(models.Model):
    """
    A category of FSM activity to log.
    """
    fsmName = models.CharField(max_length=64)
    startTime = models.DateTimeField('time created', default=timezone.now)
    endTime = models.DateTimeField('time ended', null=True)
    course = models.ForeignKey(Course, null=True)

    @classmethod
    def get_or_create(klass, name):
        """
        Get log with specified name if it exists, or create it.
        """
        try:
            return klass.objects.get(fsmName=name)
        except klass.DoesNotExist:
            a = klass(fsmName=name)
            a.save()
            return a

    @classmethod
    def log_node_entry(klass, fsmNode, user, unitLesson=None):
        """
        Record entry to this node, creating ActivityLog if needed.
        """
        a = klass.get_or_create(fsmNode.fsm.name)
        ae = ActivityEvent(
            activity=a,
            user=user,
            nodeName=fsmNode.name,
            unitLesson=unitLesson
        )
        ae.save()
        return ae


class ActivityEvent(models.Model):
    """
    Log FSM node entry/exit times.
    """
    activity = models.ForeignKey(ActivityLog)
    nodeName = models.CharField(max_length=64)
    user = models.ForeignKey(User)
    unitLesson = models.ForeignKey('ct.UnitLesson', null=True)
    startTime = models.DateTimeField('time created', default=timezone.now)
    endTime = models.DateTimeField('time ended', null=True)
    exitEvent = models.CharField(max_length=64)

    def log_exit_event(self, eventName):
        self.exitEvent = eventName
        self.endTime = timezone.now()
        self.save()
