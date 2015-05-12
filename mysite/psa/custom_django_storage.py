from django.db import models

from social.apps.django_app.default.models import DjangoStorage, Code


class CustomCode(Code):
    user_id = models.IntegerField(null=True)


class CustomDjangoStorage(DjangoStorage):
    code = CustomCode

