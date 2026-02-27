from django.contrib import admin

from .models import ChatSession, ChatMessage, TaskScore


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user1", "user2", "is_solo", "topic", "is_active", "created_at")
    list_filter = ("is_solo", "is_active", "created_at")
    search_fields = ("user1__username", "user2__username", "topic")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "chat", "sender_type", "user", "created_at")
    list_filter = ("sender_type", "created_at")
    search_fields = ("content", "user__username")


@admin.register(TaskScore)
class TaskScoreAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "score", "created_at")
    list_filter = ("created_at",)
    search_fields = ("task", "feedback", "improvement")
