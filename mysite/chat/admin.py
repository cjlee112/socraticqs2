from django.contrib import admin

from models import EnrollUnitCode, Chat, Message

# Register your models here.

admin.site.register(EnrollUnitCode)
admin.site.register(Chat)
# admin.site.register(Message)

def chat_id(obj):
    if obj.chat:
        return obj.chat.id


@admin.register(Message)
class AdminRole(admin.ModelAdmin):
    list_display = (
        'id', chat_id, 'text', 'owner', 'contenttype',
        'input_type', 'type', 'kind'
    )