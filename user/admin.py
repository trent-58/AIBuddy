from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "is_staff",
        "is_active",
        "date_joined",
    )
    search_fields = ("username", "email")
    list_filter = ("is_staff", "is_active", "is_superuser")

    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Profile", {"fields": ("interests", "bio")}),
    )
