from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


# Custom User model to include roles (host only)
class User(AbstractUser):
    ROLE_CHOICES = [
        ("host", "Host"),
    ]
    role = models.CharField(max_length=6, choices=ROLE_CHOICES, default="host")

    def __str__(self):
        return self.username


# GuestUser model for unregistered users
class GuestUser(models.Model):
    userId = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    userName = models.CharField(max_length=255)
    room = models.ForeignKey("Room", on_delete=models.CASCADE, related_name="guests")
    score = models.IntegerField(default=0)

    def __str__(self):
        return self.userName


# Room model to manage room creation, and the host relationship
class Room(models.Model):
    STATUS_CHOICES = [
        ("waiting", "Waiting"),
        ("active", "Active"),
        ("ended", "Ended"),
    ]

    roomId = models.CharField(max_length=255, unique=True)
    host = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="hosted_rooms"
    )
    status = models.CharField(max_length=7, choices=STATUS_CHOICES, default="waiting")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Room {self.roomId} - {self.status}"


# Question model to define the trivia questions for each room
class Question(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="questions")
    text = models.CharField(max_length=512)
    options = models.JSONField()  # Store options as a JSON list
    correct_answer = models.CharField(max_length=512)
    timer = models.IntegerField(default=30)  # Time limit for each question in seconds
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Q{self.id} - {self.text}"


# Answer model to track answers submitted by players
class Answer(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="answers"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="answers", null=True, blank=True
    )
    guest_user = models.ForeignKey(
        GuestUser,
        on_delete=models.CASCADE,
        related_name="answers",
        null=True,
        blank=True,
    )
    answer = models.CharField(max_length=512)
    is_correct = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Answer by {self.user.username if self.user else self.guest_user.userName} to {self.question.text} - Correct: {self.is_correct}"

    def save(self, *args, **kwargs):
        # Automatically determine if the answer is correct
        self.is_correct = self.answer == self.question.correct_answer
        super().save(*args, **kwargs)
