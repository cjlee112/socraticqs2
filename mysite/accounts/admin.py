from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Instructor


class InstructorInline(admin.StackedInline):
    model = Instructor
    can_delete = False
    verbose_name_plural = 'instructor'


class UserAdmin(BaseUserAdmin):
    inlines = (InstructorInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
