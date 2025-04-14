from rest_framework import serializers
from .models import Message, ChatRoom, ChatAccess

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    timestamp = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Message
        fields = ["id", "chat_room", "sender", "sender_username", "content", "timestamp"]
        read_only_fields = ["id", "timestamp"]

class ChatRoomSerializer(serializers.ModelSerializer):
    exchange_id = serializers.IntegerField(source="exchange.id", read_only=True)

    class Meta:
        model = ChatRoom
        fields = ["id", "room_id", "exchange_id"]

class ChatAccessSerializer(serializers.ModelSerializer):
    user1_username = serializers.CharField(source="user1.username", read_only=True)
    user2_username = serializers.CharField(source="user2.username", read_only=True)

    class Meta:
        model = ChatAccess
        fields = ["id", "user1", "user1_username", "user2", "user2_username", "exchange", "is_active"]
