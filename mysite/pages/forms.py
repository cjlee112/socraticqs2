from django.forms import ModelForm
from models import InterestedForm


class InterestedModelForm(ModelForm):

    class Meta:
        model = InterestedForm
