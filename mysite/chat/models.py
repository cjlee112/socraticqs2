from uuid import uuid4

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from ct.models import CourseUnit, UnitLesson, Response, Unit, NEED_REVIEW_STATUS
import fsm
from .utils import enroll_generator


TYPE_CHOICES = (
    ('text', 'text'),
    ('options', 'options'),
    ('errors', 'errors'),
    ('custom', 'custom'),
)

MODEL_CHOISES = (
    ('NoneType', 'NoneType'),
    ('chatdivider', 'chatdivider'),
    ('response', 'response'),
    ('unitlesson', 'unitlesson'),
    ('uniterror', 'uniterror'),
)

MESSAGE_TYPES = (
    ('default', 'default'),
    ('user', 'user'),
    ('breakpoint', 'breakpoint'),
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
    fsm_state = models.OneToOneField('fsm.FSMState', null=True)

    class Meta:
        ordering = ['-timestamp']

    # def save(self, request, *args, **kwargs):
    #     if not self.pk:
    #         fsm_stack = fsm.fsm_base.FSMStack(request)
    #         course_unit = self.enroll_code.courseUnit
    #         fsm_stack.push(request, 'chat',
    #                        stateData={'unit': course_unit.unit,
    #                                   'course': course_unit.course})
    #         self.fsm_state = fsm_stack.state
    #     super(Chat, self).save(*args, **kwargs)

    def get_options(self):
        options = None
        if self.next_point.input_type == 'options':
            options = [dict(value=i[0], text=i[1]) for i in Response.EVAL_CHOICES]
        return options


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
    type = models.CharField(max_length=16, default='default', choices=MESSAGE_TYPES)

    @property
    def content(self):
        print('content')
        app_label = 'chat' if self.contenttype == 'uniterror' or self.contenttype == 'chatdivider' else 'ct'
        model = ContentType.objects.get(app_label=app_label, model=self.contenttype).model_class()
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
        if (
            isinstance(self.content, Response) and
            self.chat and
            self.chat.next_point.input_type == 'errors'
        ):
            error_list = UnitError.get_by_message(self).get_errors()
            errors = {error.id: error.lesson.title for error in error_list}
        return errors

    def get_options(self):
        print('get_options')
        options = None
        if (
            isinstance(self.content, UnitLesson) and
            self.chat and
            self.chat.next_point.input_type == 'options'
        ):
            options = self.chat.get_options()
        return options

    def get_html(self):
        html = None
        if self.contenttype in ('chatdivider', 'response'):
            html = self.content.text
        elif self.contenttype == 'unitlesson':
            html = self.content.lesson.text
        return html

    def get_name(self):
        name = None
        if self.contenttype == 'response':
            name = self.content.author.get_full_name()
        elif self.contenttype == 'unitlesson':
            name = self.content.addedBy.get_full_name()
        return name


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


class UnitError(models.Model):
    unit = models.ForeignKey(Unit)
    response = models.ForeignKey(Response)

    def get_errors(self):
        return list(self.response.unitLesson.get_errors()) + self.unit.get_aborts()

    def save_response(self, user, response_list):
        if user == self.response.author:
            status = self.response.status
        else:
            status = NEED_REVIEW_STATUS
        for emID in response_list:
            em = UnitLesson.objects.get(pk=int(emID))
            self.response.studenterror_set.create(
                errorModel=em,
                author=user,
                status=status
            )

    @classmethod
    def get_by_message(cls, message):
        if message.chat and isinstance(message.content, Response):
            return cls.objects.get_or_create(
                unit=message.chat.enroll_code.courseUnit.unit, response=message.content
            )[0]
        else:
            raise AttributeError


class ChatDivider(models.Model):
    text = models.CharField(max_length=64)
