from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class User(AbstractUser):
    ROLE_CHOICES = [
        ("host", "Host"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # TODO: This is redundant: Try remove it and seeing what happens
    role = models.CharField(max_length=6, choices=ROLE_CHOICES, default="host")
    email = models.EmailField(unique=True)

    def clean(self):
        super().clean()
        if self.email:
            try:
                validate_email(self.email)  # Explicitly validate the email
            except ValidationError:
                # Raise a single, custom error for invalid email
                raise ValidationError(f"Invalid email: {self.email}")

    def save(self, *args, **kwargs):
        # Ensure clean() is called before saving
        self.full_clean()
        super().save(*args, **kwargs)

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
