from django.contrib import admin

from models import EnrollUnitCode, Chat, Message


def chat_id(obj):
    if obj.chat:
        return obj.chat.id


@admin.register(Message)
class AdminRole(admin.ModelAdmin):
    list_display = (
        'id', chat_id, 'text', 'owner', 'contenttype',
        'input_type', 'type', 'kind'
    )


class ChatAdmin(admin.ModelAdmin):
    list_display = (
        'next_point', 'user', 'is_open', 'is_live', 'state', 'instructor', 'timestamp'
    )


admin.site.register(Chat, ChatAdmin)
admin.site.register(EnrollUnitCode)
