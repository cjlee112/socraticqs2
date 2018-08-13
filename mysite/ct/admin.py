from django.contrib import admin
from ct.models import Liked

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
    Role,
    Liked
)


MODELS = (
    Concept,
    ConceptGraph,
    ConceptLink,
    Unit,
    Course,
    CourseUnit
)

@admin.register(UnitLesson)
class UnitLessonAdmin(admin.ModelAdmin):
    list_display = ('unit', 'lesson', 'order', 'addedBy', 'kind')


class BaseAdmin(admin.ModelAdmin):
    """
    Base class for admin models.
    """
    def get_form(self, request, obj=None, **kwargs):
        form = super(BaseAdmin, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form

    form = BaseForm


@admin.register(Lesson)
class AdminLesson(admin.ModelAdmin):
    list_display = ('title', 'text', 'kind', 'sub_kind', 'enable_auto_grading', 'parent')


@admin.register(*MODELS)
class AdminModel(BaseAdmin):
    pass


@admin.register(Role)
class AdminRole(admin.ModelAdmin):
    list_display = ('role', 'course', 'user')
    exclude = ('trial_mode',)


def short_text(obj):
    return obj.text[:25] + " ..."

@admin.register(Response)
class AdminResponse(admin.ModelAdmin):
    list_display = ('author', 'kind', 'course', 'lesson', 'text', 'attachment', 'is_preview', 'is_test', short_text)
    list_filter = ('author', 'unitLesson')
    raw_id_fields = ('lesson', 'unitLesson', 'author', 'parent')


@admin.register(StudentError)
class AdminStudentError(admin.ModelAdmin):
    raw_id_fields = ('response', 'errorModel')


def user_username(obj):
    return obj.addedBy.username
user_username.short_description = 'Username'


def lesson_title(obj):
    return obj.unitLesson.lesson.title
lesson_title.short_description = 'Lesson title'


@admin.register(Liked)
class AdminLiked(admin.ModelAdmin):
    list_display = (user_username, lesson_title, 'atime')
    list_filter = ('addedBy__username', 'unitLesson__lesson__title')
