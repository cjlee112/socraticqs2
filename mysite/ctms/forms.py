from django import forms
from django.forms import BaseModelFormSet
from django.forms.formsets import DELETION_FIELD_NAME
from django.forms.models import modelformset_factory
from django.template.loader import render_to_string
from django.core.validators import FileExtensionValidator


from ct.models import Course, Unit, Lesson, UnitLesson
from ctms.models import Invite, BestPractice1, BestPractice2, BestPractice
from .fields import SvgAllowedImageField


class CustomFileInput(forms.ClearableFileInput):

    def render(self, name, value, attrs=None, renderer=None):
        print(value)
        final_attrs = self.build_attrs(attrs, {'type': self.input_type, 'name': name})
        attrs.update({
            'name': name,
            'value': value
        }, **final_attrs)
        return render_to_string('forms/widgets/file.html', attrs)


class CustomPdfInput(forms.ClearableFileInput):

    def render(self, name, value, attrs=None, renderer=None):
        print(value)
        final_attrs = self.build_attrs(attrs, {'type': self.input_type, 'name': name})
        attrs.update({
            'name': name,
            'value': value
        }, **final_attrs)
        return render_to_string('forms/widgets/pdf.html', attrs)


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
        fields = ('title', )


class EditUnitForm(forms.ModelForm):
    KIND_CHOICES = (
        (Lesson.ORCT_QUESTION, 'Question'),
        (Lesson.EXPLANATION, 'Introduction'),
    )
    DEFAULT_UNIT_TYPE = Lesson.EXPLANATION

    def __init__(self, *args, **kwargs):
        super(EditUnitForm, self).__init__(*args, **kwargs)
        self.fields['text'].required = True

    unit_type = forms.ChoiceField(
        choices=KIND_CHOICES, widget=forms.RadioSelect, initial=Lesson.EXPLANATION,
        help_text='Questions are interactive threads where your students submit answers and self assess. Introductions are simple messages sent to your students, they can read it but can\'t send anything back. Try to ask questions early and often. An introduction can be helpful when you need to explain something in a bit more detail before asking a question.'
    )

    class Meta:
        model = Lesson
        fields = ('title', 'text', 'unit_type')

    def save(self, commit=True):
        self.instance.kind = self.cleaned_data['unit_type']
        ret = super(EditUnitForm, self).save(commit)
        return ret


class CreateEditUnitForm(EditUnitForm):
    attachment = SvgAllowedImageField(required=False, widget=CustomFileInput)

    class Meta:
        model = Lesson
        fields = ('title', 'text', 'unit_type', 'add_unit_aborts', 'mc_simplified', 'attachment')


class CreateEditUnitAnswerForm(forms.ModelForm):
    answer = forms.CharField(required=True, widget=forms.Textarea)
    attachment = SvgAllowedImageField(required=False, widget=CustomFileInput)

    class Meta:
        model = Lesson
        fields = ('answer', 'attachment')

    def save(self, unit, user, ul, commit=True):
        should_create_ul = not self.instance.id
        self.instance.text = self.cleaned_data['answer']
        self.instance.title = 'Answer'
        self.instance.addedBy = user
        self.instance.kind = Lesson.ANSWER
        self.instance.save_root()
        if should_create_ul:
            ul = UnitLesson.create_from_lesson(self.instance, unit, kind=UnitLesson.ANSWERS, parent=ul)
        lesson = super(CreateEditUnitAnswerForm, self).save(commit)
        return lesson


class ErrorModelForm(forms.ModelForm):
    """ErrorModelForm, validate data in ErrorModelFormset."""
    attachment = SvgAllowedImageField(required=False, widget=CustomFileInput, label='')
    title = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'class': 'ignore'}
    ))
    text = forms.CharField(required=True, widget=forms.Textarea(
        attrs={'class': 'ignore'}
    ))

    def __init__(self, *args, **kwargs):
        super(ErrorModelForm, self).__init__(*args, **kwargs)

        instance = kwargs.get('instance')
        if instance:
            self.fields['ul_id'] = forms.IntegerField(initial=instance.ul_id, widget=forms.HiddenInput())

    class Meta:
        model = Lesson
        fields = ('title', 'text', 'id', 'attachment')

    def save(self, questionUL, user, commit=True):
        self.instance.addedBy = user
        if commit and not self.instance.id:
            return self.instance.save_as_error_model(questionUL.lesson.concept, questionUL)
        return super(ErrorModelForm, self).save(commit=commit)


class BaseErrorModelFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        self.lesson_ul_ids = {}
        if kwargs.get('queryset'):
            # hack to pass original quryset instances with attached ul_id to each form
            self._queryset = kwargs.get('queryset')
            # map lesson id to unitLesson id
            self.lesson_ul_ids = {i.id: i.ul_id for i in self._queryset}
        super(BaseErrorModelFormSet, self).__init__(*args, **kwargs)

    def add_fields(self, form, index):
        super(BaseErrorModelFormSet, self).add_fields(form, index)
        form.fields[DELETION_FIELD_NAME].widget = forms.HiddenInput()

    @property
    def empty_form(self):
        form = self.form(
            auto_id=self.auto_id,
            prefix=self.add_prefix('__prefix__'),
            empty_permitted=True,
            use_required_attribute=False,
            **self.get_form_kwargs(None)
        )
        form.fields.pop('attachment')
        self.add_fields(form, None)
        return form


ErrorModelFormSet = modelformset_factory(
    Lesson, form=ErrorModelForm, formset=BaseErrorModelFormSet, fields=('id', 'title', 'text', 'attachment'),
    extra=0, can_delete=True,
)


class CreateCourseletForm(forms.ModelForm):
    follow_up_assessment_date = forms.CharField(widget=forms.TextInput(attrs={'placeholder': '2019-01-01'}))
    exam_name = forms.CharField()

    class Meta:
        model = Unit
        fields = ('title', 'follow_up_assessment_date', 'exam_name')


class EditCourseletForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = (
            'title',
            'exam_name', 
            'follow_up_assessment_date',
            'follow_up_assessment_grade',
            'question_parts',
            'average_score',
            'courselet_days',
            'graded_assessment_value',
            'error_resolution_days',
            'courselet_completion_credit',
            'late_completion_penalty',
            'is_show_will_learn',
        )


class UploadFileBPForm(forms.ModelForm):

    class Meta:
        model = BestPractice
        fields = ('upload_file',)


class InviteForm(forms.ModelForm):
    def __init__(self, course=None, instructor=None, enroll_unit_code=None, *args, **kwargs):
        self.course = course
        self.instructor = instructor
        self.enroll_unit_code = enroll_unit_code
        super(InviteForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Invite
        fields = ('email', 'type', 'course')
        widgets = {
            'type': forms.HiddenInput,
            'course': forms.HiddenInput,

        }

    def save(self, commit=True):
        existed_invite = Invite.objects.filter(
            instructor=self.instructor,
            course=self.course,
            enroll_unit_code=self.enroll_unit_code,
            email=self.cleaned_data['email'],
            type=self.cleaned_data['type'],
        ).first()
        if existed_invite:
            self.instance = existed_invite
        else:
            self.instance = Invite.create_new(
                commit,
                self.course,
                self.instructor,
                self.cleaned_data['email'],
                self.cleaned_data['type'],
                self.enroll_unit_code
            )
        return super(InviteForm, self).save(commit=commit)


class BestPractice1Form(forms.ModelForm):
    class Meta:
        model = BestPractice1
        fields = '__all__'


class BestPractice1PdfForm(forms.ModelForm):
    pdf = forms.FileField(required=False, widget=CustomPdfInput)

    class Meta:
        model = BestPractice1
        fields = ('pdf',)


class BestPractice2Form(forms.ModelForm):

    class Meta:
        model = BestPractice2
        fields = '__all__'
