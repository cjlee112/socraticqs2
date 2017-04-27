from django.contrib import admin

from models import EnrollUnitCode, Chat, Message

# Register your models here.

@admin.register(EnrollUnitCode)
class EnrollUnitCodeAdmin(admin.ModelAdmin):
    list_display = ('enrollCode', 'isLive', 'isPreview', 'courseUnit')
# admin.site.register(Chat)
# admin.site.register(Message)

def get_property_if_exist(*args, **kwargs):
    '''
    Return property of object if exist, otherwise return None
    :param args: property path
    :param kwargs: ...
    :return: obj.<property args[0]>.<property args[1]>.<property args[n]>
    '''
    def get_obj_prop(obj):
        for prop in args:
            obj = getattr(obj, prop, None)
        return obj

    get_obj_prop.__name__ = '.'.join(args)
    return get_obj_prop



def next_point_text(obj):
    return obj.next_point.text if obj.next_point else None

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    pass
    list_display = (
        'user', 'is_open', 'is_preview',
        'is_test', 'state', get_property_if_exist('next_point', 'text'),
        get_property_if_exist('next_point', 'kind'),
        get_property_if_exist('next_point', 'contenttype'),
        get_property_if_exist('next_point', 'content_id'),
    )


def chat_id(obj):
    if obj.chat:
        return obj.chat.id

def chat_state(obj):
    if obj.chat:
        return obj.chat.state

@admin.register(Message)
class AdminRole(admin.ModelAdmin):
    list_display = (
        'id', chat_id, chat_state, 'timestamp',  'text', 'owner', 'contenttype', 'content_id',
        'input_type', 'type', 'kind', 'userMessage'
    )

