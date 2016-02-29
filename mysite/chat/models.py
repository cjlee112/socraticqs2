from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from ct.models import Unit
from .utils import enroll_generator


MODEL_CHOISES = (
    ('NoneType', 'NoneType'),
    ('divider', 'divider'),
    ('response', 'response'),
    ('lesson', 'lesson')
)


class Chat(models.Model):
    """
    Chat model that handles particular student chat.
    """
    next_step = models.OneToOneField('Message', null=True, related_name='base_chat')
    user = models.ForeignKey(User)
    is_open = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']


class Message(models.Model):
    """
    Message model represent chat message.
    """
    chat = models.OneToOneField(Chat, null=True)
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


class EnrollUnitCode(models.Model):
    """
    Model contains links between enrollCode and Units.
    """
    enrollCode = models.CharField(max_length=32, default=enroll_generator)
    unit = models.ForeignKey(Unit)

    class Meta:
        unique_together = ('enrollCode', 'unit')
