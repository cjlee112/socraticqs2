from uuid import uuid4

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe


from ct.models import CourseUnit, UnitLesson, Response, Unit, NEED_REVIEW_STATUS, Lesson
from ct.templatetags.ct_extras import md2html


from .utils import enroll_generator


TYPE_CHOICES = (
    ('text', 'text'),
    ('options', 'options'),
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
    ('message', 'message'),
    ('user', 'user'),
    ('breakpoint', 'breakpoint'),
)

KIND_CHOICES = (
    (Lesson.BASE_EXPLANATION, Lesson.BASE_EXPLANATION),
    (Lesson.ORCT_QUESTION, Lesson.ORCT_QUESTION),
    (Lesson.ANSWER, Lesson.ANSWER),
    (Lesson.ERROR_MODEL, Lesson.ERROR_MODEL),
    ('chatdivider', 'chatdivider'),
    ('uniterror', 'uniterror'),
    ('response', 'response'),
    ('message', 'message'),
)

EVAL_OPTIONS = {
    'close': 'It was very close',
    'different': 'No similarities at all',
    'correct': 'Essentially the same'
}



class Chat(models.Model):
    """
    Chat model that handles particular student chat.
    """
    next_point = models.OneToOneField('Message', null=True, related_name='base_chat')
    user = models.ForeignKey(User)
    is_open = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)
    enroll_code = models.ForeignKey('EnrollUnitCode', null=True)
    state = models.OneToOneField('fsm.FSMState', null=True)

    class Meta:
        ordering = ['-timestamp']

    def get_options(self):
        options = None
        if self.next_point.input_type == 'options':
            options = self.next_point.get_options()
        return options


class Message(models.Model):
    """
    Message model represent chat message.
    """
    chat = models.ForeignKey(Chat, null=True, on_delete=models.SET_NULL)
    text = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(null=True)
    contenttype = models.CharField(
        max_length=16, choices=MODEL_CHOISES, null=True, default='NoneType'
    )
    content_id = models.IntegerField(null=True)
    input_type = models.CharField(max_length=16, choices=TYPE_CHOICES, null=True, default='options')
    lesson_to_answer = models.ForeignKey(UnitLesson, null=True)
    response_to_check = models.ForeignKey(Response, null=True)
    type = models.CharField(max_length=16, default='message', choices=MESSAGE_TYPES)
    owner = models.ForeignKey(User, null=True)
    is_additional = models.BooleanField(default=False)
    kind = models.CharField(max_length=32, choices=KIND_CHOICES, null=True)
    userMessage = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    @property
    def content(self):
        print('content')
        if self.contenttype == 'NoneType':
            return self.text
        app_label = 'chat' if self.contenttype == 'uniterror' or self.contenttype == 'chatdivider' else 'ct'
        model = ContentType.objects.get(app_label=app_label, model=self.contenttype).model_class()
        if model:
            return model.objects.filter(id=self.content_id).first()
        else:
            return self.contenttype

    def get_next_point(self):
        print('get_next_point')
        return self.chat.next_point.id if self.chat and self.chat.next_point else None

    def get_next_input_type(self):
        print('get_next_input_type')
        if self.chat:
            if self.chat.next_point:
                input_type = self.chat.next_point.input_type
            else:
                input_type = 'custom'
        else:
            input_type = None
        return input_type

    def get_next_url(self):
        print('get_next_url')
        return reverse('chat:messages-detail', args=(self.chat.next_point.id,)) if self.chat and self.chat.next_point else None

    def get_errors(self):
        print('get_errors')
        error_list = UnitError.objects.get(id=self.content_id).get_errors()
        checked_errors = UnitError.objects.get(id=self.content_id).response.studenterror_set.all()\
                                                                  .values_list('errorModel', flat=True)
        error_str = '<li><div class="chat-check chat-selectable %s" data-selectable-attribute="errorModel" ' \
                    'data-selectable-value="%d"></div><h3>%s</h3></li>'
        errors = reduce(lambda x, y: x+y, map(lambda x: error_str %
                                              ('chat-selectable-selected' if x.id in checked_errors else '',
                                               x.id, x.lesson.title), error_list))
        return '<ul class="chat-select-list">'+errors+'</ul>'

    def get_options(self):
        print('get_options')
        options = None
        if (self.chat and self.chat.next_point and
            self.chat.next_point.input_type == 'options'):
            if isinstance(self.chat.next_point.content, UnitError):
                options = [{"value": 1, "text": "Continue"}]
            else:
                options = [dict(value=i[0], text=i[1]) for i in Response.EVAL_CHOICES]
        return options

    def get_html(self):
        html = None
        if self.content_id:
            if self.contenttype == 'chatdivider':
                html = self.content.text
            elif self.contenttype == 'response':
                if self.input_type == 'text':
                    html = self.content.text
                else:
                    html = EVAL_OPTIONS[self.content.selfeval]
            elif self.contenttype == 'unitlesson':
                html = mark_safe(md2html(self.content.lesson.text))
            elif self.contenttype == 'uniterror':
                html = self.get_errors()
        else:
            html = self.text
        return html

    def get_name(self):
        name = "Kris Lee"
        if self.content_id:
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
    """
    Model contains links between unit and user error models.
    """
    unit = models.ForeignKey(Unit)
    response = models.ForeignKey(Response)

    def get_errors(self):
        return list(self.response.unitLesson.get_errors()) + self.unit.get_aborts()

    def save_response(self, user, response_list):
        print response_list
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
        message_with_content = Message.objects.filter(chat=message.chat,
                                                      kind='response',
                                                      timestamp__lte=message.timestamp)\
                                              .order_by('-timestamp').first()
        if message.chat and isinstance(message_with_content.content, Response):
            return cls.objects.get_or_create(
                unit=message_with_content.chat.enroll_code.courseUnit.unit,
                response=message_with_content.content
            )[0]
        else:
            raise AttributeError


class ChatDivider(models.Model):
    text = models.CharField(max_length=64)
