from django.db import models
from django.contrib.auth.models import User
from filer.fields.file import FilerFileField

from ct.models import Course

def get_upload_function(folder=''):
    def user_dir_path(instance, filename):
        return '{}/{}/{}'.format(folder, instance.addedBy.id, filename)
    return user_dir_path


class CourseReport(models.Model):
    """
    Handles Course reports.
    """
    addedBy = models.ForeignKey(User, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    course = models.ForeignKey(Course)
    response_report = models.FileField(upload_to=get_upload_function('reports/responses'), blank=True, null=True)
    error_report = models.FileField(upload_to=get_upload_function('reports/errors/'), blank=True, null=True)
