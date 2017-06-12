from django import forms


class CompleteEmailForm(forms.Form):
    # next = forms.CharField()
    email = forms.EmailField()
