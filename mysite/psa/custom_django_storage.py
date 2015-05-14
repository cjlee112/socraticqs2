from django.db import models

from social.apps.django_app.default.models import DjangoStorage, Code


class CustomCode(Code):
    """Custom Code object to track user_id through different sessions"""
    user_id = models.IntegerField(null=True)


class CustomDjangoStorage(DjangoStorage):
    """Redefine code field to CustomCode model that add user_id to track"""
    code = CustomCode

