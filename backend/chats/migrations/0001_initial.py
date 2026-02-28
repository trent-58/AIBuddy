# Generated manually

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q, F


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Chat",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("ai", "AI"), ("direct", "Direct")], max_length=16)),
                ("pair_key", models.CharField(max_length=64, unique=True)),
                ("current_topic", models.TextField(blank=True, default="")),
                ("current_task", models.TextField(blank=True, default="")),
                ("current_task_hint", models.TextField(blank=True, default="")),
                ("last_command", models.CharField(blank=True, default="", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user_a",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chats_as_a", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "user_b",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="chats_as_b", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={},
        ),
        migrations.CreateModel(
            name="AIAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("task_text", models.TextField()),
                ("answer_text", models.TextField()),
                ("score", models.PositiveSmallIntegerField()),
                ("feedback", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "chat",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempts", to="chats.chat"),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ChatMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sender_type", models.CharField(choices=[("user", "User"), ("ai", "AI")], max_length=10)),
                ("content", models.TextField()),
                ("command", models.CharField(blank=True, default="", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "chat",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="chats.chat"),
                ),
                (
                    "sender_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chats_messages_sent",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.AddConstraint(
            model_name="chat",
            constraint=models.CheckConstraint(
                condition=(Q(kind="ai", user_b__isnull=True) | Q(kind="direct", user_b__isnull=False) & ~Q(user_a=F("user_b"))),
                name="chat_kind_relation_valid",
            ),
        ),
    ]
