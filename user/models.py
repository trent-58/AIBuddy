from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    interests = models.JSONField(default=list, blank=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.username