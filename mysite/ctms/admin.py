from django.contrib import admin

from ctms.models import Invite, BestPractice1, BestPractice2


admin.site.register(BestPractice1)
admin.site.register(BestPractice2)


@admin.register(*[Invite])
class AdminModel(admin.ModelAdmin):
    list_display = ('code', 'email', 'course', 'get_status_display', 'type')
