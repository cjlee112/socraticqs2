"""Rewrited Legacy Email backend.

Original Legacy Email backend docs at:
http://psa.matiasaguirre.net/docs/backends/email.html
"""
from social_core.backends.legacy import LegacyAuth
from social_core.exceptions import AuthMissingParameter
from psa.custom_django_storage import CustomCode


class EmailAuth(LegacyAuth):
    """Legacy EmailAuth backend

    Improved auth_complete method to update data by email
    from code object.
    """
    name = 'email'
    ID_KEY = 'email'
    REQUIRES_EMAIL_VALIDATION = True
    EXTRA_DATA = ['email']

    def auth_complete(self, *args, **kwargs):
        """
        Completes loging process, must return user instance.
        """
        if self.ID_KEY not in self.data:
            code = (self.strategy.request.GET.get('verification_code') or
                    self.strategy.request.POST.get('verification_code'))
            code_object = CustomCode.objects.filter(code=code, verified=False).first()
            if code_object:
                email = code_object.email
                self.data.update({'email': email})
            else:
                raise AuthMissingParameter(self, self.ID_KEY)
        kwargs.update({'response': self.data, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)
