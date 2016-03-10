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
        return HistoryMessage(many=True).to_representation(obj.message_set.all())


class LessonSerializer(serializers.ModelSerializer):
    """
    Serializer for Lesson.
    """
    name = serializers.CharField(source='lesson.title', read_only=True)
    # started = serializers.BooleanField(source='', read_only=True)

    class Meta:
        model = UnitLesson
        fields = (
            'id',
            'name',
            # 'started',
            # 'done'
        )


class ChatProgressSerializer(serializers.ModelSerializer):
    """
    Serializer to implement /progress API.
    """
    lessons = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = (
            # 'progress',
            'lessons',
        )

    def get_lessons(self, obj):
        lessons = obj.enroll_code.courseUnit.unit.get_exercises()
        return LessonSerializer(many=True).to_representation(lessons)
