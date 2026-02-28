from django.contrib import admin

from .models import ChatInvite


@admin.register(ChatInvite)
class ChatInviteAdmin(admin.ModelAdmin):
    list_display = ("id", "from_user", "to_user", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("from_user__username", "to_user__username")
    autocomplete_fields = ("from_user", "to_user")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
