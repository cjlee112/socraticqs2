import os

from django.contrib.auth.models import User
from django.db import models
from django.utils.deconstruct import deconstructible

from ct.models import Course


@deconstructible
class UploadTo(object):
    """
    Deconstructible class as function to serialize in migrations,
    compatibility for python 2

    Path generation to store reports or errors.
    This function receive base path where to store files and return
    new function which add user ID to this path.
    We need it to personalize reports and store them in separate
    folders (folder named as user ID).

    :param folder: where to put report file
    """
    def __init__(self, folder=''):
        self.folder = folder

    def __call__(self, instance, filename):
        user_id = str(instance.addedBy.id) if instance.addedBy else ''
        return os.path.join(self.folder, user_id, filename)


class CourseReport(models.Model):
    """
    Handles Course reports.
    """
    addedBy = models.ForeignKey(User, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    course = models.ForeignKey(Course)
    response_report = models.FileField(upload_to=UploadTo('reports/responses'), blank=True, null=True)
    error_report = models.FileField(upload_to=UploadTo('reports/errors/'), blank=True, null=True)
