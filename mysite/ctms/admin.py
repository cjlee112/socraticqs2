from django.contrib import admin
from django.contrib.postgres import fields
from django_json_widget.widgets import JSONEditorWidget

from ctms.models import Invite, BestPractice1, BestPractice2, BestPractice, BestPracticeTemplate


admin.site.register(BestPractice1)
admin.site.register(BestPractice2)


@admin.register(*[Invite])
class AdminModel(admin.ModelAdmin):
    list_display = ('code', 'email', 'course', 'get_status_display', 'type')


@admin.register(BestPracticeTemplate)
class BestPracticeTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'scope')
    list_filter = ('scope',)
    formfield_overrides = {
        fields.JSONField: {'widget': JSONEditorWidget},
    }
    prepopulated_fields = {"slug": ("title",)}


@admin.register(BestPractice)
class BestPracticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'courselet', 'active', 'scope')
    list_filter = ('active', 'template__scope')
    formfield_overrides = {
        fields.JSONField: {'widget': JSONEditorWidget},
    }

    def title(self, ob):
        return ob.template.title
    
    def scope(self, ob):
        return ob.template.scope
