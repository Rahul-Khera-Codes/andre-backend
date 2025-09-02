from adrf import serializers as adrf_serializers
from rest_framework import serializers

from ..models import (
    Message,
    Session,
    VectorStore,
)

class MessageSerializerAsync(adrf_serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ("role", "content", "timestamp")
        
class SessionSerializerAsync(adrf_serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ("session_id", "session_name")