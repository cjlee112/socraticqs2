"""Module define improved entries

CustomCode -> add user_id attr to handle user generated validation link
CustomDjangoStorage -> Storage to use this CustomCode
"""
from django.db import models

from social.apps.django_app.default.models import DjangoStorage, Code


class CustomCode(Code):
    """
    Custom Code object to track user_id through different sessions.
    """
    user_id = models.IntegerField(null=True)
    force_update = models.BooleanField(default=False)

    institution = models.CharField(max_length=255, null=True)
    first_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)

    password = models.CharField(max_length=255, null=True)


class CustomDjangoStorage(DjangoStorage):
    """
    Redefine code field to CustomCode model that add user_id to track.
    """
    code = CustomCode
