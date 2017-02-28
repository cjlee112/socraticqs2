from django.contrib import admin

from ctms.models import SharedCourse


@admin.register(*[SharedCourse])
class AdminModel(admin.ModelAdmin):
    pass
