from django.contrib import admin

from .models import AITask, Submission, AIEvaluation


@admin.register(AITask)
class AITaskAdmin(admin.ModelAdmin):
    list_display = ("id", "chat", "title", "created_at")
    search_fields = ("title", "description")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "chat", "user", "submitted_at")
    search_fields = ("content", "user__username")
    list_filter = ("submitted_at",)


@admin.register(AIEvaluation)
class AIEvaluationAdmin(admin.ModelAdmin):
    list_display = ("id", "chat", "score", "created_at")
    search_fields = ("explanation",)
    list_filter = ("created_at",)
