from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import AIAttempt, Chat, ChatMessage


User = get_user_model()


class ChatSelectSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["ai", "person", "direct"])
    peer_id = serializers.IntegerField(required=False, min_value=1)

    def validate(self, attrs):
        user = self.context["request"].user
        mode = attrs["mode"]
        if mode == "direct":
            mode = "person"
            attrs["mode"] = "person"
        peer_id = attrs.get("peer_id")

        if mode == "ai":
            if peer_id is not None:
                raise serializers.ValidationError({"peer_id": "Do not send peer_id for ai mode"})
            return attrs

        if peer_id is None:
            raise serializers.ValidationError({"peer_id": "peer_id is required for person mode"})
        if user.id == peer_id:
            raise serializers.ValidationError({"peer_id": "Cannot create chat with yourself"})

        try:
            attrs["peer"] = User.objects.get(id=peer_id)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError({"peer_id": "User not found"}) from exc

        return attrs


class ChatMessageCreateSerializer(serializers.Serializer):
    text = serializers.CharField()


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ["id", "sender_type", "sender_user_id", "content", "command", "created_at"]


class ChatSerializer(serializers.ModelSerializer):
    peer_id = serializers.SerializerMethodField()
    peer_username = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = [
            "id",
            "kind",
            "peer_id",
            "peer_username",
            "current_topic",
            "current_task",
            "created_at",
            "updated_at",
        ]

    def get_peer_id(self, obj):
        request = self.context.get("request")
        if obj.kind == Chat.KIND_AI:
            return None
        if request is None:
            return obj.user_b_id
        if obj.user_a_id == request.user.id:
            return obj.user_b_id
        return obj.user_a_id

    def get_peer_username(self, obj):
        request = self.context.get("request")
        if obj.kind == Chat.KIND_AI:
            return "AI"
        if request is None:
            return str(obj.user_b)
        if obj.user_a_id == request.user.id:
            return obj.user_b.username if obj.user_b else None
        return obj.user_a.username


class ChatDetailSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = [
            "id",
            "kind",
            "user_a_id",
            "user_b_id",
            "current_topic",
            "current_task",
            "current_task_hint",
            "last_command",
            "messages",
        ]


class AIAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIAttempt
        fields = ["id", "task_text", "answer_text", "score", "feedback", "created_at"]
