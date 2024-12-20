import random
import string
import uuid
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from users.models import GuestUser

User = get_user_model()


# Room model to manage room creation, and the host relationship
class Room(models.Model):
    STATUS_CHOICES = [
        ("waiting", "Waiting"),
        ("active", "Active"),
        ("ended", "Ended"),
    ]

    room_id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    room_code = models.CharField(max_length=8, unique=True)
    host = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="hosted_rooms"
    )
    status = models.CharField(max_length=7, choices=STATUS_CHOICES, default="waiting")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Room {self.room_code} - {self.status}"

    def get_waiting_game(self):
        try:
            waiting_game = self.games.get(status="waiting")
            try:
                waiting_game.leaderboard
            except Leaderboard.DoesNotExist:
                waiting_game.create_leaderboard()
            return waiting_game
        except Game.DoesNotExist:
            raise ValueError("Create a game before starting.")
        except Game.MultipleObjectsReturned:
            # Handle the case where multiple games are found
            raise ValueError("Multiple games with status 'waiting' found.")

    def end_game(self):
        if self.games.filter(status="in_progress").exists():
            game: "Game" = self.games.get(status="in_progress")
            game.status = "finished"
            game.ended_at = timezone.now()
            game.save()
            return game
        else:
            raise ValueError("No game in progress to end.")

    def save(self, *args, **kwargs):
        if not self.room_code:  # Generate only if room_code is not set
            self.room_code = self.generate_unique_room_code()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_room_code():
        """Generate a random 6-character alphanumeric code."""
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

    def generate_unique_room_code(self):
        """Ensure the room_code is unique."""
        while True:
            code = self.generate_room_code()
            if not Room.objects.filter(room_code=code).exists():
                return code


class Game(models.Model):
    STATUS_CHOICES = [
        ("waiting", "Waiting"),
        ("in_progress", "In Progress"),
        ("finished", "Finished"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey("Room", on_delete=models.CASCADE, related_name="games")
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default="in_progress"
    )
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    current_question = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.id}-{self.status}"

    def create_leaderboard(self):
        print("Creating leaderboard")
        self.leaderboard, _ = Leaderboard.objects.get_or_create(game=self)
        print(self.leaderboard)
        return self.leaderboard


class Participant(models.Model):
    STATUS_CHOICES = [
        ("waiting", "Waiting"),
        ("ready", "Ready"),
        ("inactive", "Inactive"),
    ]
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name="participants"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="participating_users",
        null=True,
        blank=True,
    )
    guest_user = models.ForeignKey(
        GuestUser,
        on_delete=models.CASCADE,
        related_name="participating_guest_users",
        null=True,
        blank=True,
    )
    correct_answers = models.IntegerField(default=0)
    wrong_answers = models.IntegerField(default=0)
    skipped_questions = models.IntegerField(default=0)
    score = models.IntegerField(default=0)
    status = models.CharField(max_length=10, default="waiting", choices=STATUS_CHOICES)

    def __str__(self):
        return f"Participant for Room {self.room.room_id}"


class Leaderboard(models.Model):
    game = models.OneToOneField(
        Game, on_delete=models.CASCADE, related_name="leaderboard"
    )
    data = models.JSONField(default=dict)  # A dictionary to store rankings

    def update_leaderboard(self):
        participants = self.game.room.participants.all().order_by("-score")
        self.data = [
            {
                "username": participant.user.username,
                "score": participant.score,
                "correct": participant.correct_answers,
                "wrong": participant.wrong_answers,
                "skipped": participant.skipped_questions,
            }
            for participant in participants
        ]
        self.save()

    def __str__(self):
        return f"Leaderboard for Game {self.game.id}"


class Topic(models.Model):
    name = models.CharField(max_length=512, unique=True)
    subtopics = models.JSONField(
        default=list, null=True, blank=True
    )  # Store subtopics as a JSON list

    def __str__(self):
        return self.name


# Question model to define the trivia questions for each room
class Question(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="questions")
    question = models.CharField(max_length=512)
    subtopic = models.CharField(max_length=512, null=True, blank=True)
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="question_topic",
        null=True,
        blank=True,
    )
    options = models.JSONField()  # Store options as a JSON list
    correct_answer = models.CharField(max_length=512)
    timer = models.IntegerField(default=30)  # Time limit for each question in seconds
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Q{self.id} - {self.question}"


# Answer model to track answers submitted by players
class Answer(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="answers"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="answers",
        null=True,
        blank=True,
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
