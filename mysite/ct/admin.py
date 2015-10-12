from django.contrib import admin
from django.forms.models import ModelForm

import ct.models


class ConceptForm(ModelForm):
    """
    Form for AdminConcept.
    """
    def __init__(self, *args, **kwargs):
        super(ConceptForm, self).__init__(*args, **kwargs)

        if not self.initial.get('addedBy'):
            self.initial['addedBy'] = self.current_user

    class Meta:
        models = ct.models.Concept


class ConceptGraphForm(ModelForm):
    """
    Form for AdminConceptGraph.
    """
    def __init__(self, *args, **kwargs):
        super(ConceptGraphForm, self).__init__(*args, **kwargs)

        if not self.initial.get('addedBy'):
            self.initial['addedBy'] = self.current_user

    class Meta:
        models = ct.models.ConceptGraph


class LessonForm(ModelForm):
    """
    Form for AdminLesson.
    """
    def __init__(self, *args, **kwargs):
        super(LessonForm, self).__init__(*args, **kwargs)

        if not self.initial.get('addedBy'):
            self.initial['addedBy'] = self.current_user

    class Meta:
        models = ct.models.Lesson


class ConceptLinkForm(ModelForm):
    """
    Form for AdminConceptLink.
    """
    def __init__(self, *args, **kwargs):
        super(ConceptLinkForm, self).__init__(*args, **kwargs)

        if not self.initial.get('addedBy'):
            self.initial['addedBy'] = self.current_user

    class Meta:
        models = ct.models.ConceptLink


class UnitLessonForm(ModelForm):
    """
    Form for AdminUnitLesson.
    """
    def __init__(self, *args, **kwargs):
        super(UnitLessonForm, self).__init__(*args, **kwargs)

        if not self.initial.get('addedBy'):
            self.initial['addedBy'] = self.current_user

    class Meta:
        models = ct.models.UnitLesson


class UnitForm(ModelForm):
    """
    Form for AdminUnit.
    """
    def __init__(self, *args, **kwargs):
        super(UnitForm, self).__init__(*args, **kwargs)

        if not self.initial.get('addedBy'):
            self.initial['addedBy'] = self.current_user

    class Meta:
        models = ct.models.Unit


class ResponseForm(ModelForm):
    """
    Form for AdminResponse.
    """
    def __init__(self, *args, **kwargs):
        super(ResponseForm, self).__init__(*args, **kwargs)

        if not self.initial.get('author'):
            self.initial['author'] = self.current_user

    class Meta:
        models = ct.models.Response


class StudentErrorForm(ModelForm):
    """
    Form for AdminStudentError.
    """
    def __init__(self, *args, **kwargs):
        super(StudentErrorForm, self).__init__(*args, **kwargs)

        if not self.initial.get('author'):
            self.initial['author'] = self.current_user

    class Meta:
        models = ct.models.StudentError


class CourseForm(ModelForm):
    """
    Form for AdminCourse.
    """
    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)

        if not self.initial.get('addedBy'):
            self.initial['addedBy'] = self.current_user

    class Meta:
        models = ct.models.Course


class CourseUnitForm(ModelForm):
    """
    Form for AdminCourseUnit.
    """
    def __init__(self, *args, **kwargs):
        super(CourseUnitForm, self).__init__(*args, **kwargs)

        if not self.initial.get('addedBy'):
            self.initial['addedBy'] = self.current_user

    class Meta:
        models = ct.models.CourseUnit


@admin.register(ct.models.Concept)
class AdminConcept(admin.ModelAdmin):
    form = ConceptForm

    def get_form(self, request, obj=None, **kwargs):
        form = super(AdminConcept, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form


@admin.register(ct.models.ConceptGraph)
class AdminConceptGraph(admin.ModelAdmin):
    form = ConceptGraphForm

    def get_form(self, request, obj=None, **kwargs):
        form = super(AdminConceptGraph, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form


@admin.register(ct.models.Lesson)
class AdminLesson(admin.ModelAdmin):
    form = LessonForm

    def get_form(self, request, obj=None, **kwargs):
        form = super(AdminLesson, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form


@admin.register(ct.models.ConceptLink)
class AdminConceptLink(admin.ModelAdmin):
    form = ConceptLinkForm

    def get_form(self, request, obj=None, **kwargs):
        form = super(AdminConceptLink, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form


@admin.register(ct.models.UnitLesson)
class AdminUnitLesson(admin.ModelAdmin):
    form = UnitLessonForm

    def get_form(self, request, obj=None, **kwargs):
        form = super(AdminUnitLesson, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form


@admin.register(ct.models.Unit)
class AdminUnit(admin.ModelAdmin):
    form = UnitForm

    def get_form(self, request, obj=None, **kwargs):
        form = super(AdminUnit, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form


@admin.register(ct.models.Response)
class AdminResponse(admin.ModelAdmin):
    form = ResponseForm

    def get_form(self, request, obj=None, **kwargs):
        form = super(AdminResponse, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form


@admin.register(ct.models.StudentError)
class AdminStudentError(admin.ModelAdmin):
    form = StudentErrorForm

    def get_form(self, request, obj=None, **kwargs):
        form = super(AdminStudentError, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form


@admin.register(ct.models.Course)
class AdminCourse(admin.ModelAdmin):
    form = CourseForm

    def get_form(self, request, obj=None, **kwargs):
        form = super(AdminCourse, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form


@admin.register(ct.models.CourseUnit)
class AdminCourseUnit(admin.ModelAdmin):
    form = CourseUnitForm

    def get_form(self, request, obj=None, **kwargs):
        form = super(AdminCourseUnit, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form


@admin.register(ct.models.Role)
class AdminRole(admin.ModelAdmin):
    list_display = ('role', 'course', 'user')
