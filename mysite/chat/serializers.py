import injections
from rest_framework import serializers
from django.core.urlresolvers import reverse

from .models import Message, Chat
from .services import ProgressHandler
from ct.models import UnitLesson, Response


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
            'avatar',
            'html'
        )

    def get_avatar(self, obj):
        return '/avatar.jpg'


class InputSerializer(serializers.Serializer):
    """
    Serializer for input description for next message.
    """
    type = serializers.CharField(max_length=16, read_only=True)
    url = serializers.CharField(max_length=64, read_only=True)
    options = serializers.ListField()
    messagesWithSelectables = serializers.ListField(
        child=serializers.IntegerField(min_value=0)
    )


@injections.has
class MessageSerializer(serializers.ModelSerializer):
    """
    Message serializer.
    """
    next_handler = injections.depends(ProgressHandler)

    input = serializers.SerializerMethodField()
    errors = serializers.CharField(source='get_errors', read_only=True)
    addMessages = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = (
            'id',
            'input',
            'addMessages',
            'errors',
        )

    def get_input(self, obj):
        """
        Getting description for next message.
        """
        input_data = {
            'type': obj.get_next_input_type(),
            'url': obj.get_next_url(),
            'options': obj.get_options(),
            # for test purpose only
            'messagesWithSelectables': [1]
        }
        return InputSerializer().to_representation(input_data)

    def get_addMessages(self, obj):
        print('get_messages')
        qs = [obj]
        if obj.timestamp:
            current = obj
            for message in obj.chat.message_set.filter(timestamp__gt=obj.timestamp):
                if self.next_handler.group_filter(current, message):
                    current = message
                    qs.append(message)
        return InternalMessageSerializer(many=True).to_representation(qs)


class HistoryMessage(serializers.ModelSerializer):
    """
    Serializer to represent Message in histrory.
    """
    html = serializers.CharField(source='get_html', read_only=True)
    name = serializers.CharField(source='get_name', read_only=True)

    class Meta:
        model = Message
        fields = (
            'id',
            'type',
            'name',
            'html'
        )


class ChatHistorySerializer(serializers.ModelSerializer):
    """
    Serializer to implement /history API.
    """
    userInputType = serializers.CharField(source='next_point.input_type', read_only=True)
    userInputUrl = serializers.SerializerMethodField()
    userInputOptions = serializers.CharField(source='get_options', read_only=True)
    messages = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = (
            'userInputType',
            'userInputUrl',
            'userInputOptions',
            'messages',
        )

    def get_userInputUrl(self, obj):
        return reverse('chat:messages-detail', args=(obj.next_point.id,))

    def get_messages(self, obj):
        return HistoryMessage(many=True).to_representation(obj.message_set.all()
                                                              .exclude(timestamp__isnull=True)
                                                              .order_by('timestamp'))


class LessonSerializer(serializers.ModelSerializer):
    """
    Serializer for Lesson.
    """
    name = serializers.CharField(source='lesson.title', read_only=True)
    done = serializers.SerializerMethodField()
    started = serializers.SerializerMethodField()

    class Meta:
        model = UnitLesson
        fields = (
            'id',
            'name',
            'started',
            'done'
        )

    def get_started(self, obj):
        if hasattr(obj, 'message'):
            message = Message.objects.get(id=obj.message)
            return message.timestamp is not None
        else:
            return False

    def get_done(self, obj):
        if hasattr(obj, 'message'):
            message = Message.objects.get(id=obj.message)
            last_message = Message.objects.filter(chat=message.chat,
                                                  timestamp__isnull=False)\
                                          .order_by('timestamp').last()
            return message.timestamp is not None and not message.timestamp == last_message.timestamp
        else:
            return False


class ChatProgressSerializer(serializers.ModelSerializer):
    """
    Serializer to implement /progress API.
    """
    lessons = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = (
            'progress',
            'lessons',
        )

    def get_lessons(self, obj):
        messages = obj.message_set.filter(contenttype='unitlesson')
        lessons = list(obj.enroll_code.courseUnit.unit.unitlesson_set.filter(order__isnull=False))
        for each in messages:
            if each.content in lessons:
                lessons[lessons.index(each.content)].message = each.id
            else:
                if each.content.kind != 'answers':
                    lesson = each.content
                    lesson.message = each.id
                    lessons.append(lesson)
        return LessonSerializer(many=True).to_representation(lessons)

    def get_progress(self, obj):
        message_dict = self.get_lessons(obj)
        done = reduce(lambda x, y: x+y, map(lambda x: x['done'], message_dict))
        return round(float(done)/len(message_dict), 2)
