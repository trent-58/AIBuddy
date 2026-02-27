from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from chat.models import ChatSession  # sening chat appdan

User = settings.AUTH_USER_MODEL


class AITask(models.Model):
    chat = models.OneToOneField(ChatSession, on_delete=models.CASCADE, related_name="ai_task")
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Task for Chat {self.chat.id}"


class Submission(models.Model):
    chat = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="submissions")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submission by {self.user}"


class AIEvaluation(models.Model):
    chat = models.OneToOneField(ChatSession, on_delete=models.CASCADE, related_name="evaluation")
    score = models.FloatField()
    explanation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evaluation for Chat {self.chat.id}"