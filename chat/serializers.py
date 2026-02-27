from rest_framework import serializers

from .models import ChatSession, ChatMessage, TaskScore


class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = "__all__"
        read_only_fields = ["id", "created_at", "is_active", "is_solo"]


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "chat",
            "sender_type",
            "sender_username",
            "user",
            "content",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "sender_username"]

    def get_sender_username(self, obj):
        if obj.sender_type == ChatMessage.SENDER_AI:
            return "AI Tutor"
        return getattr(obj.user, "username", None)


class TaskScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskScore
        fields = ["id", "session", "task", "score", "feedback", "improvement", "created_at"]
        read_only_fields = ["id", "created_at"]
