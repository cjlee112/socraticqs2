from uuid import uuid4

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from ct.models import CourseUnit, UnitLesson, Response
from .utils import enroll_generator


TYPE_CHOICES = (
    ('text', 'text'),
    ('options', 'options'),
    ('custom', 'custom'),
)

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
    enroll_code = models.ForeignKey('EnrollUnitCode', null=True)

    class Meta:
        ordering = ['-timestamp']


class Message(models.Model):
    """
    Message model represent chat message.
    """
    chat = models.ForeignKey(Chat, null=True, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(null=True)
    contenttype = models.CharField(
        max_length=16, choices=MODEL_CHOISES, null=True, default='NoneType'
    )
    content_id = models.IntegerField(null=True)
    input_type = models.CharField(max_length=16, choices=TYPE_CHOICES, null=True)
    lesson_to_answer = models.ForeignKey(UnitLesson, null=True)
    response_to_check = models.ForeignKey(Response, null=True)
    options = models.CharField(max_length=24, choices=Response.EVAL_CHOICES, null=True)

    @property
    def content(self):
        print('content')
        model = ContentType.objects.get(app_label="ct", model=self.contenttype).model_class()
        if model:
            return model.objects.filter(id=self.content_id).first()
        else:
            return self.contenttype

    def get_next_point(self):
        print('get_next_point')
        return self.chat.next_point.id if self.chat else None

    def get_next_input_type(self):
        print('get_next_input_type')
        return self.chat.next_point.input_type if self.chat else None

    def get_next_url(self):
        print('get_next_input_type')
        return reverse('chat:messages-detail', args=(self.chat.next_point.id,)) if self.chat else None

    def get_errors(self):
        print('get_errors')
        errors = None
        if self.input_type == 'errors':
            error = list(self.content.unitLesson.get_errors()) + \
                    self.chat.enroll_code.courseUnit.unit.get_aborts()
        return errors


class EnrollUnitCode(models.Model):
    """
    Model contains links between enrollCode and Units.
    """
    enrollCode = models.CharField(max_length=32, default=enroll_generator)
    courseUnit = models.ForeignKey(CourseUnit)

    class Meta:
        unique_together = ('enrollCode', 'courseUnit')

    @classmethod
    def get_code(cls, course_unit):
        enroll_code, cr = cls.objects.get_or_create(courseUnit=course_unit)
        if cr:
            enroll_code.enrollCode = uuid4().hex
            enroll_code.save()
        return enroll_code.enrollCode
