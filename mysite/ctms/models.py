from django.db import models
from django.contrib.auth.models import User

from ct.models import Course


class SharedCourse(models.Model):
    from_user = models.ForeignKey(User, related_name='my_shares')
    to_user = models.ForeignKey(User, related_name='shares_to_me')
    course = models.ForeignKey(Course, related_name='shares')
