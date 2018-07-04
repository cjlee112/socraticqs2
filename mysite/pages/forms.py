from django.forms import ModelForm
from django import forms

from models import InterestedForm
from accounts.models import Instructor


class InterestedModelForm(ModelForm):

    class Meta:
        model = InterestedForm
        fields = '__all__'


class BecomeInstructorForm(forms.ModelForm):
    agree = forms.BooleanField(label="I agree to become instructor")

    class Meta:
        model = Instructor
        fields = ('agree',)
