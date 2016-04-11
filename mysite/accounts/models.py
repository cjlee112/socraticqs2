from django.db import models
from django.contrib.auth.models import User


class Instructor(models.Model):
    """
    Profile model for Instructors.

    Provide following additionsl fields:
        - `Institution`
        - `Department`
        - `Job`
        - `icon_url`
        - `page_url`
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    institution = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    job = models.CharField(max_length=100)
    icon_url = models.URLField()
    page_url = models.URLField()
