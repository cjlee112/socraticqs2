import os

from django.db import models
from django.contrib.auth.models import User
from filer.fields.file import FilerFileField

from ct.models import Course

def get_upload_function(folder=''):
    '''
    This function receive base path where to store files and return new function
     which add user ID to this path.
     We need it to personalize reports and store them in separate folders (folder named as user ID)
    :param folder: where to put report file
    :return: full path
    '''
    def user_dir_path(instance, filename):
        user_id = str(instance.addedBy.id) if instance.addedBy else ''
        return os.path.join(folder, user_id, filename)
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
