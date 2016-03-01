from rest_framework import serializers

from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    """
    Message serializer.
    """
    next_point = serializers.CharField(source='get_next_point', read_only=True)

    class Meta:
        model = Message
        fields = ('id', 'contenttype', 'next_point')
