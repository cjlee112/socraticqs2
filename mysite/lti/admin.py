from django.contrib import admin

from lti.models import LTIUser, CourseRef


class LTIUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'consumer', 'django_user', 'course_id')


class CourseRefAdmin(admin.ModelAdmin):
    list_display = ('context_id', 'course', 'date')
    filter_horizontal = ('instructors',)


admin.site.register(LTIUser, LTIUserAdmin)
admin.site.register(CourseRef, CourseRefAdmin)
