from rest_framework import serializers

from .models import Session, Message, Attempt


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = [
            "id",
            "user",
            "current_topic_title",
            "current_topic_explanation",
            "current_task_text",
            "current_task_type",
            "current_task_hint",
            "last_command",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "session", "role", "content", "created_at"]
        read_only_fields = ["id", "created_at"]


class AttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attempt
        fields = ["id", "session", "task_text", "user_answer", "score", "feedback", "improvement", "created_at"]
        read_only_fields = ["id", "created_at"]
