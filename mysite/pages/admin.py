from django.contrib import admin
from models import InterestedForm


class InterestedFormAdmin(admin.ModelAdmin):
    pass

admin.register(InterestedFormAdmin, InterestedForm)
# Register your models here.
