from django.contrib import admin
from models import InterestedForm


class InterestedFormAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'email', 'role')


admin.site.register(InterestedForm, InterestedFormAdmin)
