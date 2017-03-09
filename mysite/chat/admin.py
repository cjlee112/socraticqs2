from django.contrib import admin

from models import EnrollUnitCode, Chat, Message

# Register your models here.

admin.site.register(EnrollUnitCode)
admin.site.register(Chat)
# admin.site.register(Message)

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