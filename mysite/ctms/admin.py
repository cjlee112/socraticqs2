from django.contrib import admin

from ctms.models import Invite, BestPractices, BestPractices2


admin.site.register(BestPractices)
admin.site.register(BestPractices2)


@admin.register(*[Invite])
class AdminModel(admin.ModelAdmin):
    list_display = ('code', 'email', 'course', 'get_status_display', 'type')
