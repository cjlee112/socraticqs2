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
    Lesson,
    ConceptLink,
    UnitLesson,
    Unit,
    Response,
    StudentError,
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