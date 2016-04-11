import injections
from rest_framework import serializers
from django.core.urlresolvers import reverse

from .models import Message, Chat, ChatDivider
from .services import ProgressHandler
from ct.models import UnitLesson, Response
from accounts.models import Instructor


class InternalMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for addMessage list representation.
    """
    html = serializers.CharField(source='get_html', read_only=True)
    name = serializers.CharField(source='get_name', read_only=True)
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = (
            'id',
            'type',
            'name',
            'userMessage',
            'avatar',
            'html'
        )

    def get_avatar(self, obj):
        if not obj.userMessage:
            try:
                return obj.chat.instructor.instructor.icon_url
            except Instructor.DoesNotExist:
                pass


class InputSerializer(serializers.Serializer):
    """
    Serializer for input description for next message.
    """
    type = serializers.CharField(max_length=16, read_only=True)
    url = serializers.CharField(max_length=64, read_only=True)
    options = serializers.ListField()
    includeSelectedValuesFromMessages = serializers.ListField(
        child=serializers.IntegerField(min_value=0)
    )
    html = serializers.CharField(max_length=300, read_only=True)


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
            print('Inside')
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
        input_data = {
            'type': obj.get_next_input_type(),
            'url': obj.get_next_url(),
            'options': obj.get_options(),
            'includeSelectedValuesFromMessages': [i.id for i in self.qs if i.contenttype == 'uniterror']
        }
        if not obj.chat.next_point or obj.input_type == 'custom':
            input_data['html'] = '<a href="http://google.com" class="btn">Close</a>'
        return InputSerializer().to_representation(input_data)

    def get_addMessages(self, obj):
        print('get_messages')
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
        input_data = {
            'type': obj.next_point.input_type if obj.next_point else 'custom',
            'url': reverse('chat:messages-detail', args=(obj.next_point.id,)) if obj.next_point else None,
            'options': obj.get_options() if obj.next_point else None,
            # for test purpose only
            'includeSelectedValuesFromMessages': []
        }
        if not obj.next_point:
            input_data['html'] = '<a href="http://google.com" class="btn">Close</a>'
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
    id = serializers.SerializerMethodField()

    class Meta:
        model = UnitLesson
        fields = (
            'id',
            'html',
            'isUnlocked',
            'isDone'
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
        if hasattr(obj, 'message'):
            lesson_order = Message.objects.get(id=obj.message).content.unitlesson.order
            chat = Message.objects.get(id=obj.message).chat
            if chat.state and chat.state.fsmNode.fsm.name in ['chat', 'additional']:
                current_unitlesson_order = chat.state.unitLesson.order
                return lesson_order < current_unitlesson_order
            else:
                return True
        else:
            return False


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
        )

    def get_breakpoints(self, obj):
        if not self.lessons_dict:
            messages = obj.message_set.filter(contenttype='chatdivider', is_additional=False)
            lessons = list(obj.enroll_code.courseUnit.unit.unitlesson_set.filter(order__isnull=False).order_by('order'))
            for each in messages:
                if each.content.unitlesson in lessons:
                    lessons[lessons.index(each.content.unitlesson)].message = each.id
                elif each.content.unitlesson and each.content.unitlesson.kind != 'answers':
                    lesson = each.content.unitlesson
                    lesson.message = each.id
                    lessons.append(lesson)
            self.lessons_dict = LessonSerializer(many=True).to_representation(lessons)
        return self.lessons_dict

    def get_progress(self, obj):
        if not self.lessons_dict:
            self.get_breakpoints(obj)
        done = reduce(lambda x, y: x+y, map(lambda x: x['isDone'], self.lessons_dict))
        return round(float(done)/len(self.lessons_dict), 2)


class ResourcesSerializer(serializers.ModelSerializer):
    """
    Serializer for Lesson.
    """
    html = serializers.CharField(source='lesson.title', read_only=True)
    isUnlocked = serializers.SerializerMethodField()
    isDone = serializers.SerializerMethodField()
    isStarted = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()

    class Meta:
        model = UnitLesson
        fields = (
            'id',
            'html',
            'isUnlocked',
            'isStarted',
            'isDone'
        )

    def get_id(self, obj):
        if hasattr(obj, 'message'):
            return obj.message
        else:
            return obj.id

    def get_isUnlocked(self, obj):
        if obj.chat.state:
            return False
        else:
            return True

    def get_isStarted(self, obj):
        if hasattr(obj, 'message'):
            return True
        else:
            return False

    def get_isDone(self, obj):
        if hasattr(obj, 'message'):
            if obj.chat.state and obj.chat.state.unitLesson.id == obj.id:
                return False
            else:
                return True
        else:
            return False

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
        courseUnit = obj.enroll_code.courseUnit
        unit = courseUnit.unit
        lessons = list(unit.unitlesson_set \
                          .filter(kind=UnitLesson.COMPONENT, order__isnull=True))
        lessons.sort(lambda x, y: cmp(x.lesson.title, y.lesson.title))
        messages = obj.message_set.filter(contenttype='unitlesson',
                                          is_additional=True,
                                          student_error__isnull=True
                                          )
        for each in messages:
            if each.content in lessons:
                lessons[lessons.index(each.content)].message = each.id

        for each in lessons:
            each.chat = obj

        return ResourcesSerializer(many=True).to_representation(lessons)
