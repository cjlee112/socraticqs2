from rest_framework import serializers

from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    """
    Message serializer.
    """
    class Meta:
        model = Message
