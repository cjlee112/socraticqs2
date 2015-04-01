from django.db import models
from django.contrib.auth.models import User


class AnonymEmail(models.Model):
    """
    Model for temporary storing anonymous user emails
    to allow to restore anonymous sessions
    """
    user = models.ForeignKey(User)
    email = models.CharField(max_length=64)
    date = models.DateTimeField()

    class Meta:
        unique_together = ('user', 'email')
        ordering = ['-date']