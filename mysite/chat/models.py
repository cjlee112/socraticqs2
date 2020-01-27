import re
from uuid import uuid4
from functools import reduce
from itertools import starmap
import datetime

from django.db import models
from django.db.models import Q
from django.db.models import Count
from django.utils.text import Truncator
from django.utils.functional import cached_property
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.conf import settings

from core.common import onboarding
from core.common.mongo import c_chat_context, c_faq_data
from core.common.utils import update_onboarding_step
from .utils import enroll_generator
from ct.models import (
    CourseUnit,
    UnitLesson,
    Response,
    Unit,
    NEED_REVIEW_STATUS,
    Lesson,
    STATUS_CHOICES,
    StudentError,
    NEED_HELP_STATUS,
    NEED_REVIEW_STATUS
)
from ct.templatetags.ct_extras import md2html


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
    ('ask_faq_understanding', 'ask_faq_understanding'),
    ('chatdivider', 'chatdivider'),
    ('uniterror', 'uniterror'),
    ('response', 'response'),
    ('add_faq', 'add_faq'),
    ('message', 'message'),
    ('button', 'button'),
    ('abort', 'abort'),
    ('faqs', 'faqs'),
    ('faq', 'faq'),
)

SUB_KIND_CHOICES = (
    ('add_faq', 'add_faq'),
    ('transition', 'transition'),
)


EVAL_OPTIONS = {
    'close': 'It was very close',
    'different': 'No similarities at all',
    'correct': 'Essentially the same'
}

STATUS_OPTIONS = {
    'help': 'Still confused, need help',
    'review': 'OK, but flag this for me to review',
    'done': 'Solidly',
}

YES_NO_OPTIONS = (
    ('yes', 'Yes!'),
    ('no', 'No!')
)


class Chat(models.Model):
    """
    Chat model that handles particular student chat.
    """
    next_point = models.OneToOneField('Message', null=True, on_delete=models.CASCADE, related_name='base_chat')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_open = models.BooleanField(default=False)
    is_live = models.BooleanField(default=False)
    is_preview = models.BooleanField(default=False)
    is_test = models.BooleanField(default=False)
    enroll_code = models.ForeignKey('EnrollUnitCode', null=True, on_delete=models.CASCADE)
    state = models.OneToOneField('fsm.FSMState', null=True, on_delete=models.SET_NULL)
    instructor = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='course_instructor')
    last_modify_timestamp = models.DateTimeField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    progress = models.IntegerField(default=0, blank=True, null=True)
    is_trial = models.BooleanField(default=False)

    class Meta:
        ordering = ['-last_modify_timestamp']

    def get_options(self):
        options = None
        if self.next_point.input_type == 'options':
            node = self.state.fsmNode if self.state else None
            if node and hasattr(node._plugin, 'get_options'):
                return node._plugin.get_options(self)
            options = self.next_point.get_options()
        return options

    def get_course_unit(self):
        '''
        Return CourseUnit or None if CourseUnit was not found
        :return: CourseUnit instance or None
        '''
        if self.state:
            data = self.state.get_all_state_data()
            if 'course' in data and 'unit' in data:
                return CourseUnit.objects.filter(unit=data['unit'], course=data['course']).first()
        else:
            return self.enroll_code.courseUnit

    def get_spent_time(self):
        '''
        Return timestamp - start_timestamp.
        It's actual time spent for live session.
        :return: datetime.timedelta
        '''
        if not self.last_modify_timestamp:
            last_msg = self.message_set.filter(timestamp__isnull=False).order_by('-timestamp').first()
            if last_msg:
                self.last_modify_timestamp = last_msg.timestamp
                self.save()
            else:
                return datetime.timedelta(0)
        return self.last_modify_timestamp - self.timestamp

    def get_formatted_time_spent(self):
        spent_time = self.get_spent_time()
        return str(spent_time).split('.', 2)[0].replace('-', '')

    @cached_property
    def has_updates(self):
        """
        Return True if current updates count greater then configured threshold.

        Threshold settings: settings.NEW_UPDATES_THRESHOLD
        If there are no updates or insufficient updates count - return None
        """
        threads = self.enroll_code.courseUnit.unit.unitlesson_set.filter(order__isnull=False).order_by('order')
        count = 0
        for thread in threads:
            # TODO: move this to a separate cashed util function
            response_msg = self.message_set.filter(
                lesson_to_answer_id=thread.id,
                kind='response',
                contenttype='response',
                content_id__isnull=False).last()

            if not response_msg:
                continue

            response = response_msg.content
            is_need_help = response.status in (None, NEED_HELP_STATUS, NEED_REVIEW_STATUS) if response else None

            if is_need_help:
                count += thread.updates_count(self)
                if count > settings.NEW_UPDATES_THRESHOLD:
                    return True

    @cached_property
    def is_history(self):
        """
        Return True if chat is a history chat.

        If chat has a state - it is not a history.
        """
        return not self.state


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
    lesson_to_answer = models.ForeignKey(UnitLesson, null=True, on_delete=models.CASCADE)
    response_to_check = models.ForeignKey(Response, null=True, on_delete=models.CASCADE)
    student_error = models.ForeignKey(StudentError, null=True, on_delete=models.CASCADE)
    type = models.CharField(max_length=16, default='message', choices=MESSAGE_TYPES)
    owner = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    is_additional = models.BooleanField(default=False)
    kind = models.CharField(max_length=32, choices=KIND_CHOICES, null=True)
    sub_kind = models.CharField(max_length=32, choices=SUB_KIND_CHOICES, null=True)
    userMessage = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    thread_id = models.IntegerField(null=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return "<Message {}>: chat_id - '{}' user - '{}', kind - '{}', text - '{}'".format(
            self.id,
            self.chat.id if self.chat else None,
            self.owner.username, self.get_kind_display(), self.text
        )

    @property
    def content(self):
        if self.contenttype == 'NoneType':
            return self.text
        app_label = 'chat' if self.contenttype == 'uniterror' or self.contenttype == 'chatdivider' else 'ct'
        model = ContentType.objects.get(app_label=app_label, model=self.contenttype).model_class()
        if self.contenttype == 'response':
            """Filter responses using custom filter_all method.
            Because filter() and all() methods are return only valuable responses
            with is_test=False and is_preview=False."""
            return model.objects.filter_all(id=self.content_id).first()
        return model.objects.filter(id=self.content_id).first()

    def get_next_point(self):
        return self.chat.next_point.id if self.chat and self.chat.next_point else None

    def get_next_input_type(self):
        if self.chat:
            if self.chat.next_point:
                input_type = self.chat.next_point.input_type
            else:
                input_type = 'custom'
        else:
            input_type = None
        return input_type

    def get_next_url(self):
        return reverse(
            'chat:messages-detail',
            args=(self.chat.next_point.id,)
        ) if self.chat and self.chat.next_point else None

    def get_errors(self):
        if self.text:
            return self.text
        node = self.chat.state.fsmNode if self.chat.state else None
        if node and hasattr(node._plugin, 'get_errors'):
            return node._plugin.get_errors(self)
        errors = None
        error_list = UnitError.objects.get(id=self.content_id).get_errors()
        if error_list:
            checked_errors = UnitError.objects.get(
                id=self.content_id
            ).response.studenterror_set.all().values_list('errorModel', flat=True)
            error_str = (
                '<li><div class="chat-check chat-selectable {}" data-selectable-attribute="errorModel" '
                'data-selectable-value="{:d}"></div><h3>{}</h3></li>'
            )
            errors = reduce(
                lambda x, y: x+y, [error_str.format(
                        'chat-selectable-selected' if x.id in checked_errors else '',
                        x.id,
                        x.lesson.title
                    ) for x in error_list]
            )
        return '<ul class="chat-select-list">{}</ul>'.format(
            errors or '<li><h3>There are no misconceptions to display.</h3></li>'
        )

    def render_choices(self, choices, checked_choices):
        """This method renders choices as like ErrorModels.

        :param choices: choices to render
        :param checked_choices: choices to mark as checked
        """
        choices_template = (
            '<li><div class="chat-check chat-selectable %s" data-selectable-attribute="choices" '
            'data-selectable-value="%d"></div><h3>%s</h3></li>'
        )
        choices = list(choices)
        if choices:
            choices_html = reduce(
                lambda x, y: x + y,
                starmap(
                    lambda i, x: choices_template % (
                        'chat-selectable-selected' if i in checked_choices else '',
                        i,
                        x[2:] if x.startswith(Lesson.NOT_CORRECT_CHOICE) else x[3:]),
                    choices
                )
            )
        else:
            choices_html = '<h1 class="text-center">Lesson is not properly configured!</h1>'
        return '<ul class="chat-select-list">{}</ul>'.format(choices_html)

    def render_my_choices(self):
        """Render user's answer choices."""
        choices_template = '<h3>{}</h3>'  # pragma: no cover
        if '[selected_choices]' in self.content.text:
            selected = [int(i) for i in self.content.text.split('[selected_choices] ')[1].split()]
            my_choices = []
            for i, c in self.content.lesson.get_choices():
                if i in selected:
                    my_choices.append(choices_template.format(c.split(' ', 1)[1]))  # pragma: no cover
            if not my_choices:  # in this case we set userMessage to false
                self.userMessage = False
                self.save()
            return ''.join(my_choices) if my_choices else "You've chosen nothing"  # pragma: no cover
        else:
            return self.render_choices([], [])

    def get_choices(self):
        """Use this method to return QUESTION."""
        checked_choices = []
        return self.render_choices(self.content.lesson.get_choices(), checked_choices)

    def get_correct_choices(self):
        """Use this method to return ANSWER."""
        checked_choices = []
        return self.render_choices(self.lesson_to_answer.lesson.get_correct_choices(), checked_choices)

    def should_ask_confidence(self):
        """Use this method to check whether this FSM should ask for CONFIDENCE."""
        if self.chat.state:
            fsm_nodes = [
                i['name']
                for i in self.chat.state.fsmNode.fsm.fsmnode_set.all().values('name')
            ]
            return 'CONFIDENCE' in fsm_nodes or 'ADDITIONAL_CONFIDENCE' in fsm_nodes
        return False

    def get_options(self):
        node = self.chat.state.fsmNode if self.chat.state else None
        if node and hasattr(node._plugin, 'get_options'):
            return node._plugin.get_options(self.chat)
        options = None
        next_point = self.chat.next_point
        CONTINUE_BTN = {"value": 1, "text": "Continue"}
        TRANSITION_BTN = {"value": 1, "text": "Move to the next Thread"}
        if (
            self.chat and next_point and
            next_point.input_type == 'options'
        ):
            if next_point.sub_kind in ('add_faq', 'get_faq_answer'):
                return [dict(value=i[0], text=i[1]) for i in YES_NO_OPTIONS]
            # We need Continue buttom for FAQ
            if next_point.kind == 'button' and next_point.sub_kind == 'transition':
                options = [TRANSITION_BTN]
            elif next_point.kind in ('button', 'faqs'):
                options = [CONTINUE_BTN]
            elif next_point.kind == 'ask_faq_understanding':
                options = [dict(value=i[0], text=i[1]) for i in STATUS_CHOICES]
            elif (next_point.contenttype == 'unitlesson' and
                  next_point.content.lesson.sub_kind != 'choices') or (
                      next_point.contenttype == 'unitlesson' and
                      next_point.content.lesson.sub_kind == 'choices' and
                      self.chat.state.fsmNode.fsm.name == 'additional'
                  ):
                options = [dict(value=i[0], text=i[1]) for i in STATUS_CHOICES]
            elif (next_point.contenttype == 'response'
                  and next_point.lesson_to_answer
                  and next_point.lesson_to_answer.sub_kind == 'choices'
                  and not self.response_to_check
            ):
                options = [CONTINUE_BTN]
            elif next_point.contenttype == 'response' and next_point.content:
                if self.should_ask_confidence():
                    if not next_point.content.confidence:
                        options = [dict(value=i[0], text=i[1]) for i in Response.CONF_CHOICES]
                    else:
                        options = [dict(value=i[0], text=i[1]) for i in Response.EVAL_CHOICES]
                else:
                    options = [dict(value=i[0], text=i[1]) for i in Response.EVAL_CHOICES]
            else:
                options = [CONTINUE_BTN]
        return options

    def is_in_fsm_node(self, node_name):
        return self.chat.state and self.chat.state.fsmNode.fsm.name == node_name

    def get_sidebar_html(self):
        '''
        :return: Return stripped html text (ho html tags)
        '''
        # html = self.get_html()
        # return html.split("\n")[0]
        p = re.compile(r'<.*?>')

        raw_html = self.text or self.content.text

        raw_html = raw_html.split("\n")[0]
        html = mark_safe(md2html(raw_html))
        stripped_text = p.sub('', html)
        return stripped_text

    def get_html(self):
        if self.kind in ('get_faq_answer',) or \
            (self.kind == 'add_faq' and self.input_type == 'options'):
            return self.text.capitalize() + '!' if self.text else 'No!'
        if self.kind in ('ask_faq_understanding',):
            return STATUS_OPTIONS.get(self.text, 'Still confused, need help')
        if self.kind == 'abort':
            return self.get_aborts()
        html = self.text
        if self.content_id:
            if self.contenttype == 'chatdivider':
                html = self.content.text
            elif self.contenttype == 'response' and self.sub_kind == 'faq':
                html = '<b>' + self.content.title + '</b><br>' + self.content.text \
                    if self.content.title else self.content.text
            elif self.contenttype == 'response':
                sub_kind = self.content.sub_kind
                if sub_kind and sub_kind == Lesson.MULTIPLE_CHOICES and not self.content.confidence:
                    # no confidence and no selfeval
                    if sub_kind == Lesson.MULTIPLE_CHOICES:
                        html = self.render_my_choices()
                        return html

                if sub_kind and self.content.confidence and self.content.selfeval and not self.text:
                    # if look history - we already have confidence and selfeval so just return msg text
                    if self.input_type == 'options':
                        html = self.render_my_choices()
                        return html
                if self.input_type == 'text':
                    if self.sub_kind == 'add_faq':
                        html = self.text
                    else:
                        html = mark_safe(md2html(self.content.text))
                        if self.content.attachment:
                            # display svg inline
                            html += mark_safe(self.content.get_html())
                else:
                    CONF_CHOICES = dict(Response.CONF_CHOICES)
                    is_chat_fsm = (
                        self.chat and
                        self.chat.state and
                        self.chat.state.fsmNode.fsm.fsm_name_is_one_of('chat')  # TODO: add livechat here
                    )
                    values = list(CONF_CHOICES.values()) + list(EVAL_OPTIONS.values())
                    text_in_values = self.text in values
                    if is_chat_fsm and not self.text:
                        if self.content.selfeval:  # confidence is before selfeval
                            html = EVAL_OPTIONS.get(
                                self.content.selfeval, 'Self evaluation not completed yet'
                            )
                        elif self.content.confidence:
                            html = CONF_CHOICES.get(
                                self.content.confidence, 'Confidence not settled yet'
                            )
                    elif is_chat_fsm and self.text and not text_in_values:
                        html = EVAL_OPTIONS.get(
                            self.text,
                            dict(Response.CONF_CHOICES).get(
                                self.text,
                                self.text
                            )
                        )
            elif self.contenttype == 'unitlesson':
                # Get FAQ for the UnitLesson
                if self.kind == 'faqs':
                    html = self.get_faqs()
                elif self.content.kind == UnitLesson.MISUNDERSTANDS:
                    html = mark_safe(
                        md2html(
                            '**Re: %s** \n %s' %
                            (self.content.lesson.title, self.content.lesson.text)
                        )
                    )
                elif self.input_type == 'options' and self.text:  # and not self.content.lesson.sub_kind:
                    html = STATUS_OPTIONS[self.text]
                elif self.content.lesson.sub_kind and self.content.lesson.sub_kind == Lesson.MULTIPLE_CHOICES:
                    # render unitlesson (question) - answer
                    if self.content.kind in ('part', 'resol'):
                        html = mark_safe(
                            md2html(
                                self.content.lesson.get_choices_wrap_text()
                            )
                        )
                        html += self.get_choices()
                elif self.content.lesson.sub_kind == Lesson.CANVAS and self.content.lesson.kind == Lesson.ORCT_QUESTION:
                    # adds canvas to draw svg image
                    messages = self.chat.message_set.filter(id__gt=self.id)
                    lesson_kwargs = {}
                    try:
                        response = messages[0].content
                        lesson_kwargs['disabled'] = response.attachment.url
                    except (AttributeError, IndexError, ValueError):
                        pass
                    html = mark_safe(md2html(self.content.lesson.text))
                    html += self.content.lesson.get_html(**lesson_kwargs)
                elif (self.content.kind == 'answers' and
                      self.content.parent.sub_kind and
                      self.content.parent.sub_kind == Lesson.MULTIPLE_CHOICES
                    ):
                    if not self.response_to_check.selfeval:
                        correct = self.content.parent.lesson.get_correct_choices()
                        html = self.render_choices(correct, [])
                    elif self.response_to_check.selfeval and self.response_to_check.confidence:
                        correct = self.content.parent.lesson.get_correct_choices()
                        html = self.render_choices(correct, [])
                elif self.content.kind == 'answers' and self.content.parent.lesson.sub_kind == Lesson.NUMBERS:
                    # TODO add tests for this case
                    html = mark_safe(
                        md2html(
                            "Expected value {value}. \n\n{text}".format(
                                value=self.content.lesson.number_value,
                                text=self.content.lesson.text
                            )
                        )
                    )
                else:
                    if self.content.lesson.url:
                        raw_html = '`Read more <{0}>`_ \n\n{1}'.format(
                            self.content.lesson.url,
                            self.content.lesson.text
                        )
                    else:
                        raw_html = self.content.lesson.text
                    html = mark_safe(md2html(raw_html))

                    if (self.content.lesson.sub_kind == Lesson.CANVAS
                            or (self.content.parent and self.content.parent.sub_kind == Lesson.CANVAS)
                        ) and self.content.lesson.attachment and self.content.lesson.kind != Lesson.ORCT_QUESTION:
                        # append svg attachment to the message
                        html += mark_safe(self.content.lesson.get_html())

                if (
                    self.kind != 'faqs' and self.content.lesson.attachment and self.content.lesson.sub_kind != Lesson.CANVAS and not
                    (self.content.parent and self.content.parent.sub_kind == Lesson.CANVAS)
                ) or (
                    self.kind != 'faqs' and
                    self.content.lesson.kind == Lesson.ERROR_MODEL and
                    self.content.lesson.attachment
                ):
                    html += '<img src="{}" alt=""/>'.format(self.content.lesson.attachment.url)
            elif self.contenttype == 'uniterror':
                html = self.get_errors()
        if html is None:
            html = 'Answer please'

        return html

    def get_name(self):
        name = self.chat.instructor.get_full_name() or self.chat.instructor.username
        if self.content_id and self.content:
            if self.contenttype == 'response':
                name = self.content.author.get_full_name() or self.content.author.username
            elif self.contenttype == 'unitlesson':
                name = self.content.addedBy.get_full_name() or self.content.addedBy.username
            elif self.contenttype == 'chatdivider' and self.content.unitlesson:
                name = (
                    self.content.unitlesson.addedBy.get_full_name() or
                    self.content.unitlesson.addedBy.username
                )
        return name

    def get_aborts(self):
        aborts = None
        aborts_list = self.chat.enroll_code.courseUnit.unit.get_aborts()
        if aborts_list:
            checked_aborts = ()
            abort_str = (
                '<li><div class="chat-check chat-selectable {}" data-selectable-attribute="errorModel" '
                'data-selectable-value="{:d}"></div><h3>{}</h3></li>'
            )
            aborts = reduce(
                lambda x, y: x+y, [abort_str.format(
                        'chat-selectable-selected' if x.id in checked_aborts else '',
                        x.id,
                        x.lesson.title
                    ) for x in aborts_list]
            )
        return '<ul class="chat-select-list">{}</ul>'.format(
            aborts or '<li><h3>There are no aborts to display.</h3></li>'
        )

    def get_faqs(self):
        if self.text:
            return self.text
        # FIXME UPDATE -> FAQ -> get_faqs ['updates', 'new_faqs'], this transition potentially cause bugs
        state = self.chat.state
        updates = state.get_data_attr('updates') if state and 'updates' in state.load_json_data() else None
        new_faqs = state.get_data_attr('new_faqs') if state and 'new_faqs' in state.load_json_data() else None
        faqs = None
        faq_list = self.content.response_set.filter(
            ~Q(author=self.owner),
            kind=Response.STUDENT_QUESTION,
            is_preview=False,
            is_test=False
        ).exclude(title__isnull=True).exclude(title__exact='')\
            .annotate(num_inquiry=Count('inquirycount')).order_by('-num_inquiry')

        if updates and new_faqs:
            faq_list = faq_list.filter(id__in=[faq.get('faq_id') for faq in new_faqs])

        if faq_list:
            checked_faqs = c_faq_data().find_one(
                {'chat_id': self.chat.id, "ul_id": self.content_id},
                {'faqs': 1, '_id': 0}
            )
            faq_str = (
                '<li><div class="chat-check chat-selectable {}" data-selectable-attribute="faqModel" '
                'data-selectable-value="{:d}"></div><h3>{}</h3></li>'
            )
            faqs = reduce(
                lambda x, y: x+y, [faq_str.format(
                        'chat-selectable-selected' if str(x.id) in list(checked_faqs.get('faqs', {}).keys()) else '',
                        x.id,
                        x.title if x.title else Truncator(x.text).words(72, truncate=' ...')
                    ) for x in faq_list]
            )
        return '<ul class="chat-select-list">{}</ul>'.format(
            faqs or '<li><h3>There are no faqs to display.</h3></li>'
        )

    def save(self, *args, **kwargs):
        context = c_chat_context().find_one({"chat_id": self.chat_id}) or dict()
        if not (self.pk or self.thread_id):
            self.thread_id = context.get('thread_id')
        super().save(*args, **kwargs)


class EnrollUnitCode(models.Model):
    """
    Model contains links between enrollCode and Units.
    """
    enrollCode = models.CharField(max_length=32, default=enroll_generator)
    courseUnit = models.ForeignKey(CourseUnit, on_delete=models.CASCADE)
    isLive = models.BooleanField(default=False)
    isPreview = models.BooleanField(default=False)
    isTest = models.BooleanField(default=False)

    class Meta:
        unique_together = ('enrollCode', 'courseUnit', 'isLive')

    @classmethod
    def get_code(cls, course_unit, isLive=False, isPreview=False, isTest=False, give_instance=False):
        enroll_code, cr = cls.objects.get_or_create(
            courseUnit=course_unit,
            isLive=isLive,
            isPreview=isPreview,
            isTest=isTest
        )
        if cr:
            enroll_code.enrollCode = uuid4().hex
            enroll_code.isLive = isLive
            enroll_code.save()
        if give_instance:
            return enroll_code
        return enroll_code.enrollCode

    @classmethod
    def get_code_for_user_chat(cls, course_unit, is_live, user, is_preview=False, isTest=False):
        filter_kw = {
            'isPreview': is_preview,
            'isTest': isTest
        }
        update_onboarding_step(onboarding.STEP_6, user.id)
        enroll = cls.objects.filter(courseUnit=course_unit, isLive=is_live, chat__user=user, **filter_kw).first()
        if enroll:
            return enroll
        enroll = cls(courseUnit=course_unit, isLive=is_live, isPreview=is_preview, isTest=isTest)
        enroll.save()
        return enroll


class UnitError(models.Model):
    """
    Model contains links between unit and user error models.
    """
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    response = models.ForeignKey(Response, on_delete=models.CASCADE)

    def get_errors(self):
        unit_lesson = self.response.unitLesson
        error_list = list(unit_lesson.get_errors())
        # Change this to real check
        if unit_lesson.lesson.add_unit_aborts:
            error_list += self.unit.get_aborts()
        return error_list

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
    text = models.CharField(max_length=200)
    unitlesson = models.ForeignKey(UnitLesson, null=True, on_delete=models.CASCADE)
