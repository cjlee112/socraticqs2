import logging
import injections
from functools import reduce

import waffle

from rest_framework import serializers
from django.urls import reverse

from lti.models import GradedLaunch
from lti.tasks import send_outcome
from ct.models import UnitLesson
from accounts.models import Instructor
from .models import Message, Chat, ChatDivider
from .services import ProgressHandler


log = logging.getLogger(__name__)


class InternalMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for addMessage list representation.
    """
    html = serializers.CharField(source='get_html', read_only=True)
    name = serializers.CharField(source='get_name', read_only=True)
    avatar = serializers.SerializerMethodField()
    initials = serializers.SerializerMethodField()
    threadId = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = (
            'id',
            'type',
            'name',
            'userMessage',
            'avatar',
            'html',
            'initials',
            'threadId',
        )

    def get_avatar(self, obj):
        if not obj.userMessage:
            try:
                return obj.chat.instructor.instructor.icon_url
            except Instructor.DoesNotExist:
                pass

    def get_initials(self, obj):
        if not obj.userMessage:
            if obj.chat.instructor.first_name and obj.chat.instructor.last_name:
                return '{}{}'.format(obj.chat.instructor.first_name[0], obj.chat.instructor.last_name[0]).upper()
            else:
                return  # Myabe need to add here something like "PR" (professor)?
        return 'me'

    def get_threadId(self, obj):
        return obj.content.unitlesson_id if isinstance(obj.content, ChatDivider) else None


class InputSerializer(serializers.Serializer):
    """
    Serializer for input description for next message.
    """
    type = serializers.CharField(max_length=16, read_only=True)
    subType = serializers.CharField(max_length=16, read_only=True)
    url = serializers.CharField(max_length=64, read_only=True)
    options = serializers.ListField()
    includeSelectedValuesFromMessages = serializers.ListField(
        child=serializers.IntegerField(min_value=0)
    )
    html = serializers.CharField(max_length=300, read_only=True)
    doWait = serializers.BooleanField(default=False)


@injections.has
class MessageSerializer(serializers.ModelSerializer):
    """
    Message serializer.
    """
    next_handler = injections.depends(ProgressHandler)

    input = serializers.SerializerMethodField()
    # errors = serializers.CharField(source='get_errors', read_only=True)
    addMessages = serializers.SerializerMethodField()
    nextMessagesUrl = serializers.CharField(source='get_next_url', read_only=True)

    class Meta:
        model = Message
        fields = (
            'id',
            'input',
            'addMessages',
            'nextMessagesUrl',
            # 'errors',
        )

    def set_group(self, obj):
        try:
            getattr(self, 'qs')
        except AttributeError:
            self.qs = [obj]
            if obj.timestamp:
                current = obj
                for message in obj.chat.message_set.filter(timestamp__gt=obj.timestamp):
                    if self.next_handler.group_filter(current, message):
                        current = message
                        self.qs.append(message)

    def get_input(self, obj):
        """
        Getting description for next message.
        """
        self.set_group(obj)
        incl_msg = []
        sub_kind = None
        for i in self.qs:
            if i.contenttype == 'uniterror' or i.kind == 'abort':
                incl_msg.append(i.id)
            if i.contenttype == 'unitlesson' and i.content:
                if i.content.lesson.sub_kind == 'choices':
                    sub_kind = 'choices'
                    incl_msg.append(i.id)
                if i.content.sub_kind == 'numbers':
                    sub_kind = 'numbers'
                if i.content.lesson.sub_kind == 'equation':
                    sub_kind = 'equation'
                elif i.content.lesson.sub_kind == 'canvas':
                    sub_kind = 'canvas'
            # Add UnitLesson id for JS to check during selection validation
            if i.contenttype == 'unitlesson' and i.kind == 'faqs':
                incl_msg.append(i.id)

        input_data = {
            'type': obj.get_next_input_type(),
            'url': obj.get_next_url(),
            'options': obj.get_options(),
            'doWait': obj.chat.state.fsmNode.name.startswith('WAIT_') if obj.chat.state else False,
            'includeSelectedValuesFromMessages': incl_msg,
        }
        if i.contenttype == 'unitlesson':
            if sub_kind == 'numbers':
                input_data['html'] = '<input type="number" name="{}" value="{}">'.format(
                    "text",
                    0,
                )
            elif sub_kind == 'canvas':
                input_data['html'] = '<input type="hidden" />'

            input_data['subType'] = sub_kind

        if not obj.chat.next_point or input_data['doWait']:
            input_data['html'] = '&nbsp;'
        return InputSerializer().to_representation(input_data)

    def get_addMessages(self, obj):
        self.set_group(obj)
        return InternalMessageSerializer(many=True).to_representation(self.qs)


class ChatHistorySerializer(serializers.ModelSerializer):
    """
    Serializer to implement /history API.
    """
    input = serializers.SerializerMethodField()
    addMessages = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = (
            'input',
            'addMessages',
        )

    def get_input(self, obj):
        """
        Getting description for next message.
        """
        incl_msg = []
        sub_kind = None
        msg = None
        if obj.state is not None:
            msg = obj.message_set.filter(timestamp__isnull=False).last()
            # only last msg will be in available as obj after exiting from the loop.
            if msg.contenttype == 'unitlesson' and msg.content:
                if msg and msg.contenttype == 'unitlesson' and msg.content and msg.content.lesson.sub_kind == 'choices':
                    sub_kind = 'choices'
                    incl_msg.append(msg.id)
                if msg.content.lesson.sub_kind == 'numbers':
                    sub_kind = 'numbers'
                elif msg.content.lesson.sub_kind == 'equation':
                    sub_kind = 'equation'
                elif msg.content.lesson.sub_kind == 'canvas':
                    sub_kind = 'canvas'
            # Add UnitLesson id for JS to check during selection validation
            if msg.contenttype == 'unitlesson' and msg.kind == 'faqs':
                incl_msg.append(msg.id)

        input_data = {
            # obj - is the last item from loop
            'type': obj.next_point.input_type if obj.next_point else 'custom',
            'url': reverse('chat:messages-detail', args=(obj.next_point.id,)) if obj.next_point else None,
            'options': obj.get_options() if obj.next_point else None,
            'doWait': obj.state.fsmNode.name.startswith('WAIT_') if obj.state else False,
            'includeSelectedValuesFromMessages': incl_msg,
        }

        if msg and msg.contenttype == 'unitlesson':
            if sub_kind == 'numbers':
                input_data['html'] = '<input name="{}" type="number" value="{}">'.format(
                    "text", 0,
                )
            elif sub_kind == 'canvas':
                input_data['html'] = '<input type="hidden" />'

            input_data['subType'] = sub_kind

        if not obj.next_point or input_data['doWait']:
            input_data['html'] = '&nbsp;'
        return InputSerializer().to_representation(input_data)

    def get_addMessages(self, obj):
        return InternalMessageSerializer(many=True).to_representation(
            obj.message_set.all().exclude(timestamp__isnull=True).order_by('timestamp')
        )


class LessonSerializer(serializers.ModelSerializer):
    """
    Serializer for Lesson.
    """
    html = serializers.CharField(source='lesson.title', read_only=True)
    isDone = serializers.SerializerMethodField()
    isUnlocked = serializers.SerializerMethodField()
    updatesCount = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    threadId = serializers.SerializerMethodField()

    class Meta:
        model = UnitLesson
        fields = (
            'id',
            'html',
            'isUnlocked',
            'isDone',
            'updatesCount',
            'threadId',
        )

    def get_id(self, obj):
        if hasattr(obj, 'message'):
            return obj.message
        else:
            return obj.id

    def get_isUnlocked(self, obj):
        if hasattr(obj, 'message'):
            message = Message.objects.get(id=obj.message)
            return message.timestamp is not None
        else:
            return False

    def get_isDone(self, obj):
        if hasattr(obj, 'is_done'):
            return obj.is_done

        if hasattr(obj, 'message'):
            msg = Message.objects.get(id=obj.message)
            lesson_order = msg.content.unitlesson.order
            chat = msg.chat

            def check_fsm_name(*nodes):
                return chat.state and chat.state.fsmNode.fsm.fsm_name_is_one_of(*nodes)

            if chat.is_live and check_fsm_name('live_chat'):
                # here we assume that user can not get next question without answering for current one.
                questions = chat.message_set.filter(
                    kind='orct',
                    contenttype='unitlesson',
                    content_id__isnull=False,
                )
                responses = chat.message_set.filter(
                    kind='response',
                    contenttype='response',
                    content_id__isnull=False,
                    input_type='text'
                )
                diff = questions.count() - responses.count()
                if diff >= 1:
                    return False
                elif diff == 0:
                    obj.is_done = True
                    return True
                else:
                    return False
            if check_fsm_name('chat'):
                is_done = lesson_order < chat.state.unitLesson.order
                obj.is_done = is_done
                return is_done
            if check_fsm_name('additional') or check_fsm_name('faq'):
                return lesson_order < chat.state.parentState.unitLesson.order
            else:
                obj.is_done = True
                return True
        else:
            return False

    def get_updatesCount(self, obj):
        is_done = obj.is_done if hasattr(obj, 'is_done') else self.get_isDone(obj)
        return obj.updates(self.context.get('chat')) if is_done and self.context.get('chat') else 0
    
    def get_threadId(self, obj):
        return obj.id


class ChatProgressSerializer(serializers.ModelSerializer):
    """
    Serializer to implement /progress API.
    """
    breakpoints = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    lessons_dict = None

    class Meta:
        model = Chat
        fields = (
            'progress',
            'breakpoints',
            'is_live',
        )

    def get_breakpoints(self, obj):
        if not self.lessons_dict:
            messages = obj.message_set.filter(contenttype='chatdivider', is_additional=False)
            if obj.is_live:
                lessons = []
                for msg in messages:
                    try:  # pragma: no cover
                        lesson = msg.content.unitlesson
                        lesson.message = msg.id
                        lessons.append(lesson)
                    except AttributeError as ex:
                        log.error(
                            "{}, Error details: message_id '{}', chat_id '{}', user '{}', kind '{}', text '{}'".format(
                                ex,
                                msg.id,
                                obj.id,
                                self.context['request'].user.username,
                                msg.kind,
                                msg.text
                            )
                        )  # pragma: no cover
            else:
                lessons = list(
                    obj.enroll_code.courseUnit.unit.unitlesson_set.filter(
                        order__isnull=False
                    ).order_by('order')
                )
                for each in messages:
                    try:
                        if each.content.unitlesson in lessons:
                            lessons[lessons.index(each.content.unitlesson)].message = each.id
                        elif each.content.unitlesson and each.content.unitlesson.kind != 'answers':
                            lesson = each.content.unitlesson
                            lesson.message = each.id
                            lessons.append(lesson)
                    except:
                        pass
            
            self.lessons_dict = LessonSerializer(many=True, context={'chat': obj}).to_representation(lessons)
        return self.lessons_dict

    def get_progress(self, obj):
        if not self.lessons_dict:
            try:
                self.get_breakpoints(obj)
            except:
                pass
        if self.lessons_dict and obj.state:
            done = reduce(lambda x, y: x+y, [x['isDone'] for x in self.lessons_dict])
            progress = round(float(done)/len(self.lessons_dict), 2)
        else:
            # if no lessons passed yet - return 1
            progress = 1
        assignment = GradedLaunch.objects.filter(
            course_id=obj.enroll_code.courseUnit.course.id
        ).first()
        if not obj.progress == (progress * 100):
            obj.progress = progress * 100
            obj.save()
            if assignment and waffle.switch_is_active('lti_send_outcome'):
                # this is very simple implementation and should be changed
                # we are sendign grade only for updated progress
                send_outcome.delay(progress, assignment.id)
        return progress


class AddUnitByChatStepSerializer(serializers.ModelSerializer):
    """
    Serializer for Message, used when user in "Add unit by chat"
    chat to serialize messages for Progress
    """
    html = serializers.CharField(source='get_sidebar_html', read_only=True)
    isDone = serializers.SerializerMethodField()
    isUnlocked = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()

    def get_id(self, obj):
        return obj.id

    def get_isUnlocked(self, obj):
        return bool(obj.timestamp)

    def get_isDone(self, obj):
        return bool(obj.timestamp and obj.chat.message_set.filter(
            userMessage=True,
            timestamp__isnull=False,
            id__gt=obj.id
        ).count())

    class Meta:
        model = Message
        fields = (
            'id',
            'html',
            'isUnlocked',
            'isDone'
        )


class AddUnitByChatSerializer(ChatProgressSerializer):
    """
    Serializer for progress in "Add unit by chat"
    """
    breakpoints = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = (
            'progress',
            'breakpoints',
            'is_live',
        )

    def get_breakpoints(self, obj):
        steps = obj.message_set.filter(is_additional=False, userMessage=False, timestamp__isnull=False)
        self.lessons_dict = AddUnitByChatStepSerializer(many=True).to_representation(steps)
        return self.lessons_dict


class ResourcesSerializer(serializers.ModelSerializer):
    """
    Serializer for Resource Lesson.
    """
    html = serializers.CharField(source='lesson.title', read_only=True)
    isUnlocked = serializers.SerializerMethodField()
    isDone = serializers.SerializerMethodField()
    isStarted = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    ul = serializers.SerializerMethodField()
    threadId = serializers.SerializerMethodField()

    class Meta:
        model = UnitLesson
        fields = (
            'id',
            'ul',
            'html',
            'isUnlocked',
            'isStarted',
            'isDone',
            'threadId',
        )

    def get_id(self, obj):
        """
        Return message id if message for this lesson has been already made or None
        """
        if hasattr(obj, 'message'):
            return obj.message
        else:
            return None

    def get_ul(self, obj):
        """
        Return UnitLesson id if there is no message fot this resource yet
        """
        if hasattr(obj, 'message'):
            return None
        else:
            return obj.id

    def get_isUnlocked(self, obj):
        """
        Return True if main sequence has ended and studen get access to resources
        """
        if obj.chat.state:
            return False
        else:
            return True

    def get_isStarted(self, obj):
        """
        Return True if this resource started
        """
        if hasattr(obj, 'message'):
            return True
        else:
            return False

    def get_isDone(self, obj):
        """
        Return True if all messages for that resource have already been showed
        """
        if hasattr(obj, 'message'):
            if obj.chat.state and obj.chat.state.unitLesson.id == obj.id:
                return False
            else:
                return True
        else:
            return False
    
    def get_threadId(self, obj):
        """
        Get id of current thread.
        """
        return obj.id


class ChatResourcesSerializer(serializers.ModelSerializer):
    """
    Serializer to implement /progress API.
    """
    breakpoints = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = (
            'breakpoints',
        )

    def get_breakpoints(self, obj):
        if obj.is_live:
            #NOTE: if chat.is_live Don't show Resources.
            return ResourcesSerializer(many=True).to_representation([])

        courseUnit = obj.enroll_code.courseUnit
        unit = courseUnit.unit
        lessons = list(
            unit.unitlesson_set.filter(kind=UnitLesson.COMPONENT, order__isnull=True)
        )
        lessons.sort(key=lambda x: x.lesson.title)
        messages = obj.message_set.filter(
            contenttype='unitlesson', is_additional=True, student_error__isnull=True
        )
        for each in messages:
            if each.content in lessons:
                lessons[lessons.index(each.content)].message = each.id

        for each in lessons:
            each.chat = obj

        return ResourcesSerializer(many=True).to_representation(lessons)


class ChatSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    session = serializers.CharField(source='state.id', read_only=True)
    is_preview = serializers.BooleanField(read_only=True)
    is_test = serializers.BooleanField(read_only=True)

    class Meta:
        model = Chat
        fields = ('id', 'session', 'is_test', 'is_preview')
