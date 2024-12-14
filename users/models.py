from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


class User(AbstractUser):
    ROLE_CHOICES = [
        ("host", "Host"),
    ]
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="ai_quiz_user_set",  # Change the related_name here
        blank=True,
        help_text="The groups this user belongs to.",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="ai_quiz_user_permissions_set",  # Change the related_name here
        blank=True,
        help_text="Specific permissions for this user.",
    )
    role = models.CharField(max_length=6, choices=ROLE_CHOICES, default="host")

    def __str__(self):
        return self.username


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    avatar = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"


# GuestUser model for unregistered users
class GuestUser(models.Model):
    userId = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    userName = models.CharField(max_length=255)
    room = models.ForeignKey(
        "ai_quiz.Room", on_delete=models.CASCADE, related_name="guests"
    )
    score = models.IntegerField(default=0)

    def __str__(self):
        return self.userName
