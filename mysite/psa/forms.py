from django import forms


class SignUpForm(forms.Form):
    '''Fields to handle on:
        Email
        Re-enter email
        First name
        Last name
        Institution
        Password'''
    next = forms.CharField(widget=forms.HiddenInput(), required=False)
    email = forms.EmailField()
    email_confirmation = forms.EmailField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    institution = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        confirm_email = self.cleaned_data['email_confirmation']
        email = self.cleaned_data['email']
        if confirm_email and email and email == confirm_email:
            return self.cleaned_data
        else:
            self._errors['email_confirmation'] = 'Should be the same as email'
            raise forms.ValidationError(
                "Fields {} and {} should have the same values".format(
                    'email',
                    'email confirmation')
            )

