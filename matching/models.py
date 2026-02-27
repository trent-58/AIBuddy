from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class ChatInvite(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_invites")
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_invites")

    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
        ],
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.status})"