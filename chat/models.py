from django.conf import settings
from django.db import models


User = settings.AUTH_USER_MODEL


class ChatSession(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chats_as_user1")
    user2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chats_as_user2",
        null=True,
        blank=True,
    )
    topic = models.CharField(max_length=255, blank=True, default="")
    current_topic = models.TextField(blank=True, default="")
    current_task = models.TextField(blank=True, default="")
    is_solo = models.BooleanField(default=False)
    command_state = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        if self.is_solo or not self.user2:
            return f"Solo chat: {self.user1}"
        return f"{self.user1} - {self.user2}"


class ChatMessage(models.Model):
    SENDER_USER = "user"
    SENDER_AI = "ai"

    SENDER_CHOICES = [
        (SENDER_USER, "User"),
        (SENDER_AI, "AI"),
    ]

    chat = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    sender_type = models.CharField(max_length=10, choices=SENDER_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        who = self.user if self.sender_type == self.SENDER_USER else "AI"
        return f"[{self.chat_id}] {who}: {self.content[:40]}"


class TaskScore(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="scores")
    task = models.TextField()
    score = models.PositiveSmallIntegerField()
    feedback = models.TextField()
    improvement = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Score {self.score} for session {self.session_id}"


class Session(models.Model):
    TASK_TYPE_CONCEPTUAL = "conceptual"
    TASK_TYPE_PRACTICAL = "practical"
    TASK_TYPE_CODING = "coding"
    TASK_TYPE_CHOICES = [
        (TASK_TYPE_CONCEPTUAL, "Conceptual"),
        (TASK_TYPE_PRACTICAL, "Practical"),
        (TASK_TYPE_CODING, "Coding"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="study_sessions")
    current_topic_title = models.TextField(null=True, blank=True)
    current_topic_explanation = models.TextField(null=True, blank=True)
    current_task_text = models.TextField(null=True, blank=True)
    current_task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, null=True, blank=True)
    current_task_hint = models.TextField(null=True, blank=True)
    last_command = models.CharField(max_length=30, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.id} for {self.user_id}"


class Message(models.Model):
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_SYSTEM = "system"
    ROLE_CHOICES = [
        (ROLE_USER, "User"),
        (ROLE_ASSISTANT, "Assistant"),
        (ROLE_SYSTEM, "System"),
    ]

    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}#{self.session_id}: {self.content[:40]}"


class Attempt(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="attempts")
    task_text = models.TextField()
    user_answer = models.TextField()
    score = models.IntegerField()
    feedback = models.TextField()
    improvement = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Attempt#{self.id} score={self.score}"
