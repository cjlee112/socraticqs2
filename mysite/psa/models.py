from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib.auth.signals import user_logged_in

from social_django.models import UserSocialAuth


class AnonymEmail(models.Model):
    """Temporary anonymous user emails

    Model for temporary storing anonymous user emails
    to allow to restore anonymous sessions.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.CharField(max_length=64)
    date = models.DateTimeField()

    class Meta:
        unique_together = ('user', 'email')
        ordering = ['-date']


class SecondaryEmail(models.Model):
    """Model for storing secondary emails

    We can store emails here from social_auth
    or LTI login.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='secondary')
    provider = models.ForeignKey(UserSocialAuth, on_delete=models.CASCADE)
    email = models.EmailField(verbose_name='Secondary Email')

    class Meta:
        unique_together = ('provider', 'email')


class UserSession(models.Model):
    """User<->Session model

    Model for linking user to session.
    Solution from http://gavinballard.com/associating-django-users-sessions/
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)


def user_logged_in_handler(sender, request, user, **kwargs):
    """
    Create UserSession object to store User<=>Session relation.
    """
    if user.groups.filter(name='Temporary').exists():
        if not Session.objects.filter(session_key=request.session.session_key).exists():
            request.session.save()

        UserSession.objects.get_or_create(
            user=user,
            session_id=request.session.session_key
        )


user_logged_in.connect(user_logged_in_handler)
