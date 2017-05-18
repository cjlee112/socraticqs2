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
    institution = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    job = models.CharField(max_length=100, blank=True)
    icon_url = models.URLField(blank=True)
    page_url = models.URLField(blank=True)

    def __unicode__(self):
        return self.user.username if not (self.user.last_name or self.user.first_name) else self.user.get_full_name()
