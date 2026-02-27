from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import EmailVerificationCode, Interest, InterestOption, User


class InterestInline(admin.TabularInline):
    model = Interest
    extra = 0
    autocomplete_fields = ("name",)


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
        ("Profile", {"fields": ("bio",)}),
    )
    inlines = (InterestInline,)


@admin.register(InterestOption)
class InterestOptionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at", "updated_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "name", "created_at", "updated_at")
    search_fields = ("user__username", "user__email", "name__name")
    list_filter = ("name", "created_at")
    autocomplete_fields = ("user", "name")


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "user", "code", "is_verified", "expires_at", "created_at")
    search_fields = ("email", "user__username")
    list_filter = ("is_verified", "created_at", "expires_at")
    autocomplete_fields = ("user",)
