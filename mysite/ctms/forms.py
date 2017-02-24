from django import forms
from ct.models import Course, CourseUnit, Unit, Lesson, UnitLesson


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ('title', 'addedBy')
        widgets = {
            'addedBy': forms.HiddenInput
        }


class CreateUnitForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ('title',)


class EditUnitForm(forms.ModelForm):
    KIND_CHOICES = (
        (Lesson.EXPLANATION, 'long explanation'),
        (Lesson.ORCT_QUESTION, 'Open Response Concept Test question'),
    )
    unit_type = forms.ChoiceField(choices=KIND_CHOICES)

    class Meta:
        model = Lesson
        fields = ('text', 'unit_type')

    def save(self, commit=True):
        self.instance.kind = self.cleaned_data['unit_type']
        return super(EditUnitForm, self).save(commit)

class CreateCourseletForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ('title',)
