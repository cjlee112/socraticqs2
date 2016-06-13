from django.contrib import admin

from fsm.models import FSM, FSMGroup, FSMNode, FSMEdge, FSMState, ActivityLog, ActivityEvent


@admin.register(FSM)
class AdminFSM(admin.ModelAdmin):
    list_display = ('name', 'title', 'startNode', 'addedBy', 'atime')


@admin.register(FSMGroup)
class AdminFSMGroup(admin.ModelAdmin):
    list_display = ('fsm', 'group')


@admin.register(FSMNode)
class AdminFSMNode(admin.ModelAdmin):
    list_display = ('name', 'fsm', 'title', 'path', 'funcName', 'doLogging', 'addedBy', 'atime')


@admin.register(FSMEdge)
class AdminFSMEdge(admin.ModelAdmin):
    list_display = ('name', 'fromNode', 'toNode', 'title', 'showOption', 'addedBy', 'atime')


@admin.register(FSMState)
class AdminFSMState(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'fsmNode',
        'parentState',
        'linkState',
        'unitLesson',
        'path',
        'isLiveSession',
        'activity',
        'activityEvent'
    )


@admin.register(ActivityLog)
class AdminActivityLog(admin.ModelAdmin):
    list_display = ('fsmName', 'course', 'startTime', 'endTime')


@admin.register(ActivityEvent)
class AdminActivityEvent(admin.ModelAdmin):
    list_display = ('activity', 'nodeName', 'user', 'unitLesson', 'startTime', 'endTime', 'exitEvent')
