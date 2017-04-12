from django.db import models
from filer.fields.file import FilerFileField

from ct.models import Course


class CourseReport(models.Model):
    """
    Handles Course reports.
    """
    date = models.DateTimeField(auto_now_add=True)
    course = models.ForeignKey(Course)
    response_report = models.FileField(upload_to='reports/responses/', blank=True, null=True)
    error_report = models.FileField(upload_to='reports/errors/', blank=True, null=True)
