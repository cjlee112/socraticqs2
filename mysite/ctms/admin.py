from django.contrib import admin

from ctms.models import Invite


@admin.register(*[Invite])
class AdminModel(admin.ModelAdmin):
    pass
