from rest_framework_mongoengine.serializers import DocumentSerializer
from .models import Message

class MessageSerializer(DocumentSerializer):
    class Meta:
        model = Message
        fields = "__all__"