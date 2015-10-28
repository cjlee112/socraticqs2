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


class BaseAdmin(admin.ModelAdmin):
    """
    Base class for admin models.
    """
    def get_form(self, request, obj=None, **kwargs):
        form = super(BaseAdmin, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form

    form = BaseForm


def register_model(model):
    @admin.register(model)
    class AdminModel(BaseAdmin):
        pass


models = [
    ct.models.Concept, ct.models.ConceptGraph, ct.models.Lesson,
    ct.models.ConceptLink, ct.models.UnitLesson, ct.models.Unit,
    ct.models.Response, ct.models.StudentError, ct.models.Course,
    ct.models.CourseUnit
]

map(register_model, models)


@admin.register(ct.models.Role)
class AdminRole(admin.ModelAdmin):
    list_display = ('role', 'course', 'user')
