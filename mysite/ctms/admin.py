from django.contrib import admin

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


@admin.register(BestPractice)
class BestPracticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'courselet', 'active', 'scope')
    list_filter = ('active', 'template__scope')

    def title(self, ob):
        return ob.template.title
    
    def scope(self, ob):
        return ob.template.scope
