from django.contrib import admin

from .forms import BaseForm
from .models import (
    Concept,
    ConceptGraph,
    Lesson,
    ConceptLink,
    UnitLesson,
    Unit,
    Response,
    StudentError,
    Course,
    CourseUnit,
    Role
)


MODELS = (
    Concept,
    ConceptGraph,
    Lesson,
    ConceptLink,
    UnitLesson,
    Unit,
    Course,
    CourseUnit
)


class BaseAdmin(admin.ModelAdmin):
    """
    Base class for admin models.
    """
    def get_form(self, request, obj=None, **kwargs):
        form = super(BaseAdmin, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form

    form = BaseForm


@admin.register(*MODELS)
class AdminModel(BaseAdmin):
    pass


@admin.register(Role)
class AdminRole(admin.ModelAdmin):
    list_display = ('role', 'course', 'user')


@admin.register(Response)
class AdminResponse(admin.ModelAdmin):
    raw_id_fields = ('lesson', 'unitLesson')


@admin.register(StudentError)
class AdminStudentError(admin.ModelAdmin):
    raw_id_fields = ('response', 'errorModel')
