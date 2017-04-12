from django.contrib import admin

from .models import CourseReport


class CourseReportAdmin(admin.ModelAdmin):
    list_display = ('course', 'date', 'response_report', 'error_report')


admin.site.register(CourseReport, CourseReportAdmin)
