from django import forms
from ct.models import Question, Response, ErrorModel, UnitQ, Unit, Course, CommonError, Remediation
from django.utils.translation import ugettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout
## from crispy_forms.bootstrap import StrictButton

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['title', 'qtext', 'answer', 'access']
        labels = dict(qtext=_('Question'))

class QuestionSearchForm(forms.Form):
    search = forms.CharField(label='Search for questions containing')

class ResponseForm(forms.ModelForm):
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
    class Meta:
        model = ErrorModel
        fields = ['description']
        labels = dict(description=_('Add a new error model'))

class ErrorModelCEForm(forms.ModelForm):
    def __init__(self, ceSet, *args, **kwargs):
        super(ErrorModelCEForm, self).__init__(*args, **kwargs)
        if ceSet:
            self.fields['commonError'].queryset = ceSet
    class Meta:
        model = ErrorModel
        fields = ['commonError']
        widgets = dict(commonError=forms.RadioSelect)
        labels = dict(commonError=_('Common errors for this concept'))
            
class ResponseListForm(forms.Form):
    ndisplay = forms.ChoiceField(choices=(('25', '25'), ('50', '50'),
                                          ('100', '100')))
    sortOrder = forms.ChoiceField(choices=(('-atime', 'Most recent first'),
                                           ('atime', 'Least recent first'),
                                           ('-confidence', 'Most confident first'),
                                           ('confidence', 'Least confident first'))) 

class UnitTitleForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['title']
    
class CourseTitleForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'access']
    
class UnitQForm(forms.ModelForm):
    def __init__(self, questionSet, *args, **kwargs):
        super(UnitQForm, self).__init__(*args, **kwargs)
        if questionSet:
            self.fields['question'].queryset = questionSet
    class Meta:
        model = UnitQ
        fields = ['question']
        labels = dict(question=_('From your study-list'))

class ConceptSearchForm(forms.Form):
    search = forms.CharField(label='Search for concepts containing')

class CommonErrorForm(forms.ModelForm):
    class Meta:
        model = CommonError
        fields = ['synopsis', 'disproof', 'prescription', 'dangerzone']
        
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
