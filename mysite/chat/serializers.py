from rest_framework import serializers

from .models import Message
from ct.models import UnitLesson, Response


class MessageSerializer(serializers.ModelSerializer):
    """
    Message serializer.
    """
    next_point = serializers.CharField(source='get_next_point', read_only=True)
    userInputType = serializers.CharField(source='get_next_input_type', read_only=True)
    userInputUrl = serializers.CharField(source='get_next_url', read_only=True)
    errors = serializers.CharField(source='get_errors', read_only=True)
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
            'errors'
        )

    def get_messages(self, obj):
        print('get_messages')
        text = None
        if isinstance(obj.content, UnitLesson):
            text = [obj.content.lesson.text]
        elif isinstance(obj.content, Response):
            text = [obj.content.text]
        return [text]
