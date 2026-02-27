from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


User = settings.AUTH_USER_MODEL


class Chat(models.Model):
    KIND_AI = "ai"
    KIND_DIRECT = "direct"
    KIND_CHOICES = [
        (KIND_AI, "AI"),
        (KIND_DIRECT, "Direct"),
    ]

    kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    user_a = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chats_as_a")
    user_b = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chats_as_b",
        null=True,
        blank=True,
    )
    pair_key = models.CharField(max_length=64, unique=True)

    current_topic = models.TextField(blank=True, default="")
    current_task = models.TextField(blank=True, default="")
    current_task_hint = models.TextField(blank=True, default="")
    last_command = models.CharField(max_length=20, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="chat_kind_relation_valid",
                condition=(
                    (Q(kind="ai") & Q(user_b__isnull=True))
                    | (Q(kind="direct") & Q(user_b__isnull=False) & ~Q(user_a=models.F("user_b")))
                ),
            )
        ]

    def clean(self):
        if self.kind == self.KIND_AI and self.user_b_id is not None:
            raise ValidationError("AI chat cannot have user_b")
        if self.kind == self.KIND_DIRECT:
            if self.user_b_id is None:
                raise ValidationError("Direct chat requires user_b")
            if self.user_a_id == self.user_b_id:
                raise ValidationError("Direct chat cannot be with self")

    @staticmethod
    def build_pair_key(*, kind: str, user_a_id: int, user_b_id: int | None = None) -> str:
        if kind == Chat.KIND_AI:
            return f"ai:{user_a_id}"
        if user_b_id is None:
            raise ValueError("Direct chat requires user_b_id")
        low, high = sorted([user_a_id, user_b_id])
        return f"direct:{low}:{high}"

    def save(self, *args, **kwargs):
        if self.kind == self.KIND_DIRECT and self.user_b_id is not None and self.user_a_id is not None:
            low, high = sorted([self.user_a_id, self.user_b_id])
            self.user_a_id = low
            self.user_b_id = high
        self.pair_key = self.build_pair_key(
            kind=self.kind,
            user_a_id=self.user_a_id,
            user_b_id=self.user_b_id,
        )
        self.full_clean()
        super().save(*args, **kwargs)

    def is_participant(self, user_id: int) -> bool:
        if self.user_a_id == user_id:
            return True
        if self.user_b_id == user_id:
            return True
        return False

    def __str__(self):
        if self.kind == self.KIND_AI:
            return f"AI chat for {self.user_a_id}"
        return f"Direct chat {self.user_a_id}<->{self.user_b_id}"


class ChatMessage(models.Model):
    SENDER_USER = "user"
    SENDER_AI = "ai"
    SENDER_CHOICES = [
        (SENDER_USER, "User"),
        (SENDER_AI, "AI"),
    ]

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    sender_type = models.CharField(max_length=10, choices=SENDER_CHOICES)
    sender_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="chats_messages_sent",
    )
    content = models.TextField()
    command = models.CharField(max_length=20, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender_type}#{self.chat_id}: {self.content[:40]}"


class AIAttempt(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="attempts")
    task_text = models.TextField()
    answer_text = models.TextField()
    score = models.PositiveSmallIntegerField()
    feedback = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Attempt#{self.id} score={self.score}"


class ChatTopic(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="topics")
    topic_name = models.CharField(max_length=255)
    normalized_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["chat", "normalized_name"],
                name="chat_topic_unique_per_chat",
            )
        ]

    def __str__(self):
        return f"{self.chat_id}: {self.topic_name}"
