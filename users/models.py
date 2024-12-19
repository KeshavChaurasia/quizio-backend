from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


class User(AbstractUser):
    ROLE_CHOICES = [
        ("host", "Host"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=6, choices=ROLE_CHOICES, default="host")

    def __str__(self):
        return f"User: {self.username}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    avatar = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


# GuestUser model for unregistered users
class GuestUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=255)
    room = models.ForeignKey(
        "ai_quiz.Room", on_delete=models.CASCADE, related_name="guests"
    )
    score = models.IntegerField(default=0)

    def __str__(self):
        return f"Guest: {self.username}"
