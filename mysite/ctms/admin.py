from django.contrib import admin

# Register your models here.
from ctms.models import SharedCourse


@admin.register(*[SharedCourse])
class AdminModel(admin.ModelAdmin):
    pass