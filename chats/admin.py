from django.contrib import admin

from .models import AIAttempt, Chat, ChatMessage, ChatTopic


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("created_at",)


class ChatTopicInline(admin.TabularInline):
    model = ChatTopic
    extra = 0
    readonly_fields = ("normalized_name", "created_at")


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ("id", "kind", "user_a", "user_b", "updated_at")
    list_filter = ("kind", "created_at", "updated_at")
    search_fields = ("user_a__username", "user_b__username", "pair_key")
    readonly_fields = ("pair_key", "created_at", "updated_at")
    inlines = (ChatTopicInline, ChatMessageInline)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "chat", "sender_type", "sender_user", "command", "created_at")
    list_filter = ("sender_type", "command", "created_at")
    search_fields = ("content", "sender_user__username")
    readonly_fields = ("created_at",)


@admin.register(AIAttempt)
class AIAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "chat", "score", "created_at")
    list_filter = ("score", "created_at")
    search_fields = ("task_text", "answer_text", "feedback")
    readonly_fields = ("created_at",)


@admin.register(ChatTopic)
class ChatTopicAdmin(admin.ModelAdmin):
    list_display = ("id", "chat", "topic_name", "normalized_name", "created_at")
    list_filter = ("created_at",)
    search_fields = ("topic_name", "normalized_name")
    readonly_fields = ("created_at",)
