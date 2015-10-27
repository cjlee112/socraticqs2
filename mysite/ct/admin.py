from django.contrib import admin
from django.forms.models import ModelForm

import ct.models


class BaseForm(ModelForm):
    """
    Base class for admin forms.
    """
    def __init__(self, *args, **kwargs):
        super(BaseForm, self).__init__(*args, **kwargs)

        for field_name in ('addedBy', 'author'):
            if field_name in self.fields and not self.initial.get(field_name):
                self.initial[field_name] = self.current_user


class ConceptForm(BaseForm):
    """
    Form for AdminConcept.
    """
    class Meta:
        models = ct.models.Concept


class ConceptGraphForm(BaseForm):
    """
    Form for AdminConceptGraph.
    """
    class Meta:
        models = ct.models.ConceptGraph


class LessonForm(BaseForm):
    """
    Form for AdminLesson.
    """
    class Meta:
        models = ct.models.Lesson


class ConceptLinkForm(BaseForm):
    """
    Form for AdminConceptLink.
    """
    class Meta:
        models = ct.models.ConceptLink


class UnitLessonForm(BaseForm):
    """
    Form for AdminUnitLesson.
    """
    class Meta:
        models = ct.models.UnitLesson


class UnitForm(BaseForm):
    """
    Form for AdminUnit.
    """
    class Meta:
        models = ct.models.Unit


class ResponseForm(BaseForm):
    """
    Form for AdminResponse.
    """
    class Meta:
        models = ct.models.Response


class StudentErrorForm(BaseForm):
    """
    Form for AdminStudentError.
    """
    class Meta:
        models = ct.models.StudentError


class CourseForm(BaseForm):
    """
    Form for AdminCourse.
    """
    class Meta:
        models = ct.models.Course


class CourseUnitForm(BaseForm):
    """
    Form for AdminCourseUnit.
    """
    class Meta:
        models = ct.models.CourseUnit


class BaseAdmin(admin.ModelAdmin):
    """
    Base class for admin models.
    """
    def get_form(self, request, obj=None, **kwargs):
        form = super(BaseAdmin, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form


@admin.register(ct.models.Concept)
class AdminConcept(BaseAdmin):
    form = ConceptForm


@admin.register(ct.models.ConceptGraph)
class AdminConceptGraph(BaseAdmin):
    form = ConceptGraphForm


@admin.register(ct.models.Lesson)
class AdminLesson(BaseAdmin):
    form = LessonForm


@admin.register(ct.models.ConceptLink)
class AdminConceptLink(BaseAdmin):
    form = ConceptLinkForm


@admin.register(ct.models.UnitLesson)
class AdminUnitLesson(BaseAdmin):
    form = UnitLessonForm


@admin.register(ct.models.Unit)
class AdminUnit(BaseAdmin):
    form = UnitForm


@admin.register(ct.models.Response)
class AdminResponse(BaseAdmin):
    form = ResponseForm


@admin.register(ct.models.StudentError)
class AdminStudentError(BaseAdmin):
    form = StudentErrorForm


@admin.register(ct.models.Course)
class AdminCourse(BaseAdmin):
    form = CourseForm


@admin.register(ct.models.CourseUnit)
class AdminCourseUnit(BaseAdmin):
    form = CourseUnitForm


@admin.register(ct.models.Role)
class AdminRole(admin.ModelAdmin):
    list_display = ('role', 'course', 'user')
