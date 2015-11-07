from django.contrib import admin
from models import InterestedForm


class InterestedFormAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'timezone')


admin.site.register(InterestedForm, InterestedFormAdmin)
