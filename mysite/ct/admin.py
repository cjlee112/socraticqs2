from django.contrib import admin
import ct.models


@admin.register(ct.models.Role)
class AdminRole(admin.ModelAdmin):
    list_display = ('role', 'course', 'user')


admin.site.register(ct.models.Concept)
admin.site.register(ct.models.ConceptGraph)
admin.site.register(ct.models.Lesson)
admin.site.register(ct.models.ConceptLink)
admin.site.register(ct.models.UnitLesson)
admin.site.register(ct.models.Unit)
admin.site.register(ct.models.Response)
admin.site.register(ct.models.StudentError)
admin.site.register(ct.models.Course)
admin.site.register(ct.models.CourseUnit)
