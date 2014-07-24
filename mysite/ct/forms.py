from django import forms
from ct.models import Question, Response
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
    emlist = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                       required=False)


                                       
