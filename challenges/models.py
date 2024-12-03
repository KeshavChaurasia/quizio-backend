import uuid
from django.db import models
from django.contrib.auth.models import User
from quiz.models import Question


class Challenge(models.Model):
    CHALLENGE_TYPE_CHOICES = [
        ("round_based", "Round Based"),
        ("question_based", "Question Based"),
    ]

    host = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="hosted_challenges"
    )
    type = models.CharField(max_length=20, choices=CHALLENGE_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, default="pending"
    )  # e.g., active, completed, canceled
    join_token = models.UUIDField(default=uuid.uuid4, unique=True)

    def __str__(self):
        return f"Challenge: {self.title} ({self.type})"


class ChallengeParticipant(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="participated_challenges", null=True, blank=True
    )
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE, related_name="participants"
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(
        default=True
    )  # To track if the user left the challenge

    def __str__(self):
        return f"Participant: {self.user.username} in {self.challenge.title}"


class Round(models.Model):
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE, related_name="rounds"
    )
    title = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Round {self.id} in Challenge: {self.challenge.title}"


class ChallengeQuestion(models.Model):
    round = models.ForeignKey(
        Round,
        on_delete=models.CASCADE,
        related_name="questions",
        null=True,
        blank=True,
    )
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE, related_name="questions"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    timer = models.IntegerField(default=30)  # Timer in seconds for the question

    def __str__(self):
        return f"Question {self.question.id} in Challenge: {self.challenge.title}"


class AnswerSubmission(models.Model):
    participant = models.ForeignKey(
        ChallengeParticipant, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(
        ChallengeQuestion, on_delete=models.CASCADE, related_name="submissions"
    )
    answer = models.TextField()  # Stores the submitted answer
    is_correct = models.BooleanField(null=True, blank=True)  # Marked after validation
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer by {self.participant.user.username} for {self.question.question.id}"
