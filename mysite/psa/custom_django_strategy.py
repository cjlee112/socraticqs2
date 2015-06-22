"""Custom Strategy to implement handling user_id attr in Code object"""
from social.strategies.django_strategy import DjangoStrategy


class CustomDjangoStrategy(DjangoStrategy):
    """Custom DjangoStrategy

    Needed to add custom login and fix different session issue.
    """
    def send_email_validation(self, backend, email):
        code = super(CustomDjangoStrategy, self).send_email_validation(backend, email)
        user = self.request.user
        if user and user.is_authenticated():
            code.user_id = user.id
            code.save()
        return code
