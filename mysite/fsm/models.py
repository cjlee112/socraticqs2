
from django.utils import timezone
from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Q

from fsm.utils import get_plugin

from ct.ct_util import reverse_path_args
from ct.models import Course, Role
from mixins import JSONBlobMixin, ChatMixin


class FSM(models.Model):
    """
    Finite State Machine top-level state-graph container.
    """
    name = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    help = models.TextField(null=True, blank=True)
    startNode = models.ForeignKey('FSMNode', related_name='+', null=True, blank=True)
    hideTabs = models.BooleanField(default=False)
    hideLinks = models.BooleanField(default=False)
    hideNav = models.BooleanField(default=False)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    addedBy = models.ForeignKey(User)

    def fsm_name_is_one_of(self, *args):
        return self.name in args + tuple(i + "OLD" for i in args)

    @classmethod
    def save_graph(cls, fsmData, nodeData, edgeData, username, fsmGroups=(), oldLabel='OLD'):
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
                old = cls.objects.get(name=oldName)
            except cls.DoesNotExist:
                pass
            else:
                old.delete()
            try:  # rename current to nameOLD
                old = cls.objects.get(name=name)
            except cls.DoesNotExist:
                pass
            else:
                old.name = oldName
                old.save()
                for group in old.fsmgroup_set.all():
                    group.delete()
                # old.fsmgroup_set.clear() # RelatedManager has no attribute clear
            fsm = cls(addedBy=user, **fsmData)  # create new FSM
            fsm.save()
            for groupName in fsmGroups:  # register in specified groups
                fsm.fsmgroup_set.create(group=groupName)
            nodes = {}
            for name, nodeDict in nodeData.items():  # save nodes
                node = FSMNode(name=name, fsm=fsm, addedBy=user, **nodeDict)
                if node.funcName:  # make sure plugin imports successfully
                    get_plugin(node.funcName)
                node.save()
                nodes[name] = node
                if name == 'START':
                    fsm.startNode = node
                    fsm.save()
            for edgeDict in edgeData:  # save edges
                edgeDict = edgeDict.copy()  # don't modify input dict!
                edgeDict['fromNode'] = nodes[edgeDict['fromNode']]
                edgeDict['toNode'] = nodes[edgeDict['toNode']]
                edge = FSMEdge(addedBy=user, **edgeDict)
                edge.save()
        return fsm

    def get_node(self, name):
        """
        Get node in this FSM with specified name.
        """
        return self.fsmnode_set.get(name=name)

    def __unicode__(self):
        return self.name


class FSMGroup(models.Model):
    """
    Groups multiple FSMs into one named UI group.
    """
    fsm = models.ForeignKey(FSM)
    group = models.CharField(db_index=True, max_length=64)

    def __unicode__(self):
        return self.group


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


class FSMNode(JSONBlobMixin, ChatMixin, models.Model):
    """
    Stores one node of an FSM state-graph.
    """
    fsm = models.ForeignKey(FSM)
    name = models.CharField(db_index=True, max_length=64)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    help = models.TextField(null=True, blank=True)
    path = models.CharField(max_length=200, null=True, blank=True)
    data = models.TextField(null=True, blank=True)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    addedBy = models.ForeignKey(User)
    funcName = models.CharField(max_length=200, null=True, blank=True)
    doLogging = models.BooleanField(default=False)
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
            return fsmStack.state.transition(fsmStack, request, eventName, **kwargs)

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

    def __unicode__(self):
        return u'::'.join((self.name, self.funcName))


class FSMDone(ValueError):
    pass


class FSMBadUserError(ValueError):
    """
    Request.user does not match state.user.
    """
    pass


class FSMStackResumeError(ValueError):
    pass


class FSMEdge(JSONBlobMixin, models.Model):
    """
    Stores one edge of an FSM state-graph.
    """
    name = models.CharField(db_index=True, max_length=64)
    fromNode = models.ForeignKey(FSMNode, related_name='outgoing')
    toNode = models.ForeignKey(FSMNode, related_name='incoming')
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    help = models.TextField(null=True, blank=True)
    showOption = models.BooleanField(default=False)
    data = models.TextField(null=True, blank=True)
    atime = models.DateTimeField('time submitted', default=timezone.now)
    addedBy = models.ForeignKey(User)
    _funcDict = {}

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

    def filter_input(self, obj):
        """
        Use plugin code to check whether obj is acceptable input to this edge.
        """
        try:  # see if plugin code provides select_X_filter() call
            func = getattr(self.fromNode._plugin, self.name + '_filter')
        except AttributeError:  # no plugin method, so accept by default
            return True
        else:
            return func(self, obj)

    def __unicode__(self):
        return self.name


class FSMState(JSONBlobMixin, models.Model):
    """
    Stores current state of a running FSM instance.
    """
    user = models.ForeignKey(User)
    fsmNode = models.ForeignKey(FSMNode)
    parentState = models.ForeignKey('FSMState', null=True, blank=True,
                                    related_name='children')
    linkState = models.ForeignKey('FSMState', null=True, blank=True,
                                  related_name='linkChildren')
    unitLesson = models.ForeignKey('ct.UnitLesson', null=True, blank=True)
    title = models.CharField(max_length=200)
    path = models.CharField(max_length=200)
    data = models.TextField(null=True, blank=True)
    hideTabs = models.BooleanField(default=False)
    hideLinks = models.BooleanField(default=False)
    hideNav = models.BooleanField(default=False)
    isLiveSession = models.BooleanField(default=False)
    atime = models.DateTimeField('time started', default=timezone.now)
    activity = models.ForeignKey('ActivityLog', null=True, blank=True)
    activityEvent = models.ForeignKey('ActivityEvent', null=True, blank=True)

    def get_all_state_data(self):
        """
        Get dict of all our state data including unitLesson.
        """
        objects_dict = self.load_json_data().copy()  # copy to avoid side-effects
        if self.unitLesson:
            objects_dict['unitLesson'] = self.unitLesson
        return objects_dict

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
            edge = self.fsmNode.outgoing.get(name=name)
        except FSMEdge.DoesNotExist:
            return None  # FSM does not handle this event, return control
        if self.activityEvent:  # record exit from this node
            self.activityEvent.log_exit_event(name)
            self.activityEvent = None
        self.fsmNode = edge.transition(fsmStack, request, **kwargs)
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
    def find_live_sessions(cls, user):
        """
        Get live sessions relevant to this user.
        """
        # QuerySet should return only Instructor FSMState's
        return cls.objects.filter(
            ~Q(fsmNode__funcName__contains='live_chat'),
            isLiveSession=True,
            activity__course__role__user=user,
            activity__course__role__in=Role.objects.filter(
                role__in=[Role.ENROLLED, Role.SELFSTUDY], user=user
            )
        ).distinct()

    def __unicode__(self):
        return u'::'.join((self.user.username, str(self.fsmNode)))


class ActivityLog(models.Model):
    """
    A category of FSM activity to log.
    """
    fsmName = models.CharField(max_length=64)
    startTime = models.DateTimeField('time created', default=timezone.now)
    endTime = models.DateTimeField('time ended', null=True, blank=True)
    course = models.ForeignKey(Course, null=True, blank=True)

    @classmethod
    def log_node_entry(cls, fsmNode, user, unitLesson=None):
        """
        Record entry to this node, creating ActivityLog if needed.
        """
        activity_log, created = cls.objects.get_or_create(fsmName=fsmNode.fsm.name)
        activity_event = ActivityEvent(
            activity=activity_log,
            user=user,
            nodeName=fsmNode.name,
            unitLesson=unitLesson
        )
        activity_event.save()
        return activity_event

    def __unicode__(self):
        return u'::'.join((self.fsmName, str(self.startTime)))


class ActivityEvent(models.Model):
    """
    Log FSM node entry/exit times.
    """
    activity = models.ForeignKey(ActivityLog)
    nodeName = models.CharField(max_length=64)
    user = models.ForeignKey(User)
    unitLesson = models.ForeignKey('ct.UnitLesson', null=True, blank=True)
    startTime = models.DateTimeField('time created', default=timezone.now)
    endTime = models.DateTimeField('time ended', null=True, blank=True)
    exitEvent = models.CharField(max_length=64)

    def log_exit_event(self, eventName):
        """
        Log exit event.
        """
        self.exitEvent = eventName
        self.endTime = timezone.now()
        self.save()

    def __unicode__(self):
        return u'::'.join((self.user.username, self.nodeName, str(self.startTime)))
