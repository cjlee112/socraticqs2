from uuid import uuid4

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from ct.models import CourseUnit
from .utils import enroll_generator


MODEL_CHOISES = (
    ('NoneType', 'NoneType'),
    ('divider', 'divider'),
    ('response', 'response'),
    ('unitlesson', 'unitlesson')
)


class Chat(models.Model):
    """
    Chat model that handles particular student chat.
    """
    next_point = models.OneToOneField('Message', null=True, related_name='base_chat')
    user = models.ForeignKey(User)
    is_open = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']


class Message(models.Model):
    """
    Message model represent chat message.
    """
    chat = models.ForeignKey(Chat, null=True)
    timestamp = models.DateTimeField(null=True)
    contenttype = models.CharField(
        max_length=16, choices=MODEL_CHOISES, null=True, default='NoneType'
    )
    content_id = models.IntegerField(null=True)

    @property
    def content(self):
        model = ContentType.objects.get(app_label="ct", model=self.contenttype).model_class()
        if model:
            return model.objects.filter(id=self.content_id).first()
        else:
            return self.contenttype

    def get_next_point(self):
        return self.chat.next_point.id if self.chat else None


class EnrollUnitCode(models.Model):
    """
    Model contains links between enrollCode and Units.
    """
    enrollCode = models.CharField(max_length=32, default=enroll_generator)
    courseUnit = models.ForeignKey(CourseUnit)

    class Meta:
        unique_together = ('enrollCode', 'courseUnit')

    def create_code(self):
        self.enrollCode = uuid4().hex
        self.save()
