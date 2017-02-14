from django.db import models
from django.contrib.auth.models import User
from ct.models import Course


class SharedCourse(models.Model):
    from_user = models.ForeignKey(User, related_name='shared_for')
    to_user = models.ForeignKey(User, related_name='shared_with')
    course = models.ForeignKey(Course, related_name='shared_courses')