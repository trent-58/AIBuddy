from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("chats", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatTopic",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("topic_name", models.CharField(max_length=255)),
                ("normalized_name", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "chat",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="topics", to="chats.chat"),
                ),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.AddConstraint(
            model_name="chattopic",
            constraint=models.UniqueConstraint(fields=("chat", "normalized_name"), name="chat_topic_unique_per_chat"),
        ),
    ]
