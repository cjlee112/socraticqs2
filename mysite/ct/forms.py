from django import forms
from ct.models import Question, Response, ErrorModel
from django.utils.translation import ugettext_lazy as _

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['title', 'qtext', 'answer', 'access']


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
    
class ResponseListForm(forms.Form):
    ndisplay = forms.ChoiceField(choices=(('25', '25'), ('50', '50'),
                                          ('100', '100')))
    sortOrder = forms.ChoiceField(choices=(('-atime', 'Most recent first'),
                                           ('atime', 'Least recent first'),
                                           ('-confidence', 'Most confident first'),
                                           ('confidence', 'Least confident first'))) 

