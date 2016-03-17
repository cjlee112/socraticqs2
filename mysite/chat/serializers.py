from datetime import datetime

from rest_framework import serializers
from django.core.urlresolvers import reverse

from .models import Message, Chat
from ct.models import UnitLesson, Response


class MessageSerializer(serializers.ModelSerializer):
    """
    Message serializer.
    """
    next_point = serializers.CharField(source='get_next_point', read_only=True)
    userInputType = serializers.CharField(source='get_next_input_type', read_only=True)
    userInputUrl = serializers.CharField(source='get_next_url', read_only=True)
    errors = serializers.CharField(source='get_errors', read_only=True)
    options = serializers.CharField(source='get_options', read_only=True)
    messages = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = (
            'id',
            'contenttype',
            'next_point',
            'userInputType',
            'userInputUrl',
            'messages',
            'errors',
            'options'
        )

    def get_messages(self, obj):
        print('get_messages')
        text = None
        if isinstance(obj.content, UnitLesson):
            text = [obj.content.lesson.text]
        elif isinstance(obj.content, Response):
            text = [obj.content.text]
        return [text]


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
        additional_lessons = Message.objects.filter(
            chat=obj,
            is_additional=True
        ).distinct('content_id').count()
        lessons = obj.enroll_code.courseUnit.unit.unitlesson_set.filter(order__isnull=False)
        finish_lessont = Message.objects.filter(chat=obj,
                                                contenttype='unitlesson',
                                                content_id__in=[i[0] for i in lessons.values_list('id')],
                                                timestamp__isnull=False)
        messages = Message.objects.filter(
            chat=obj,
            contenttype='unitlesson',
            content_id__in=[i[0] for i in lessons.values_list('id')],
            timestamp__isnull=False
            # is_additional=False
        ).distinct('content_id').count()
        # TODO implement counting of finished messages
        return messages / float(len(lessons)+additional_lessons)
