from django import forms
from ct.models import Question, Response, ErrorModel, CourseQuestion, Courselet, Course, CommonError, Remediation
from django.utils.translation import ugettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout
## from crispy_forms.bootstrap import StrictButton

class QuestionForm(forms.ModelForm):
    submitLabel = 'Update'
    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-questionForm'
        self.helper.form_class = 'form-vertical'
        self.helper.add_input(Submit('submit', self.submitLabel))
    class Meta:
        model = Question
        fields = ['title', 'qtext', 'answer', 'access']
        labels = dict(qtext=_('Question'))

class NewQuestionForm(QuestionForm):
    submitLabel = 'Add'

class QuestionSearchForm(forms.Form):
    search = forms.CharField(label='Search for questions containing')

class ResponseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ResponseForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-responseForm'
        self.helper.form_class = 'form-vertical'
        self.helper.add_input(Submit('submit', 'Save'))
    class Meta:
        model = Response
        fields = ['atext', 'confidence']
        labels = dict(atext=_('Your answer'))

class SelfAssessForm(forms.Form):
    selfeval = forms.ChoiceField(choices=(('', '----'),) + Response.EVAL_CHOICES)
    status = forms.ChoiceField(choices=(('', '----'),)
                               + Response.STATUS_CHOICES)
    emlist = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                       required=False)


class ErrorModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ErrorModelForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-errorModelForm'
        self.helper.form_class = 'form-vertical'
        self.helper.add_input(Submit('submit', 'Save'))
    class Meta:
        model = ErrorModel
        fields = ['description']
        labels = dict(description=_('Add a new error model'))

class ResponseListForm(forms.Form):
    ndisplay = forms.ChoiceField(choices=(('25', '25'), ('50', '50'),
                                          ('100', '100')))
    sortOrder = forms.ChoiceField(choices=(('-atime', 'Most recent first'),
                                           ('atime', 'Least recent first'),
                                           ('-confidence', 'Most confident first'),
                                           ('confidence', 'Least confident first'))) 

class CourseletTitleForm(forms.ModelForm):
    submitLabel = 'Update'
    def __init__(self, *args, **kwargs):
        super(CourseletTitleForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-courseletTitleForm'
        self.helper.form_class = 'form-vertical'
        self.helper.add_input(Submit('submit', self.submitLabel))
    class Meta:
        model = Courselet
        fields = ['title']

class NewCourseletTitleForm(CourseletTitleForm):
    submitLabel = 'Add'

class CourseTitleForm(forms.ModelForm):
    submitLabel = 'Update'
    def __init__(self, *args, **kwargs):
        super(CourseTitleForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-courseTitleForm'
        self.helper.form_class = 'form-vertical'
        self.helper.add_input(Submit('submit', self.submitLabel))
    class Meta:
        model = Course
        fields = ['title', 'access']

class NewCourseTitleForm(CourseTitleForm):
    submitLabel = 'Add'

class CourseQuestionForm(forms.ModelForm):
    def __init__(self, questionSet, *args, **kwargs):
        super(CourseQuestionForm, self).__init__(*args, **kwargs)
        if questionSet:
            self.fields['question'].queryset = questionSet
    class Meta:
        model = CourseQuestion
        fields = ['question']
        labels = dict(question=_('From related concepts or your study-list'))

class ConceptSearchForm(forms.Form):
    search = forms.CharField(label='Search for concepts containing')

class LessonSearchForm(forms.Form):
    ## def __init__(self, *args, **kwargs):
    ##     super(LessonSearchForm, self).__init__(*args, **kwargs)
    ##     self.helper = FormHelper(self)
    ##     self.helper.form_id = 'id-lessonSearchForm'
    ##     self.helper.form_method = 'get'
    ##     self.helper.form_class = 'form-inline'
    ##     self.helper.field_template = 'bootstrap3/layout/inline_field.html'
    ##     self.helper.add_input(StrictButton('Search', css_class='btn-default'))
    sourceDB = forms.ChoiceField(choices=(('wikipedia', 'Wikipedia'),),
                                 label='Search Courselets.org and')
    search = forms.CharField(label='for material containing')
    

class RemediationForm(forms.ModelForm):
    submitLabel = 'Update'
    def __init__(self, *args, **kwargs):
        super(RemediationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-remediationForm'
        self.helper.form_class = 'form-vertical'
        self.helper.add_input(Submit('submit', self.submitLabel))
    class Meta:
        model = Remediation
        fields = ['title', 'advice']
        labels = dict(title=_('Concise suggestion'))
    

class NewRemediationForm(RemediationForm):
    submitLabel = 'Add'
