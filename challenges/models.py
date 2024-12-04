import uuid
from django.db import models
from django.contrib.auth.models import User
from quiz.models import Question


class Challenge(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("canceled", "Canceled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    CHALLENGE_TYPE_CHOICES = [
        ("round_based", "Round Based"),
        ("question_based", "Question Based"),
    ]

    host = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="hosted_challenges"
    )
    type = models.CharField(max_length=20, choices=CHALLENGE_TYPE_CHOICES)
    title = models.CharField(max_length=255, default="Challenge")
    host = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="hosted_challenges"
    )
    join_token = models.UUIDField(default=uuid.uuid4, editable=False)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pending"
    )
    current_round = models.IntegerField(null=True, blank=True)
    current_question = models.ForeignKey(
        "ChallengeQuestion",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="current_question",
    )
    time_remaining = models.IntegerField(null=True, blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Challenge: {self.title} ({self.type})"

    def next_question(self):
        """
        Progress to the next question in the current round.
        If no more questions are left in this round, progress to the next round.
        """
        current_round = Round.objects.get(
            challenge=self, round_number=self.current_round
        )

        # Get the list of questions in the current round
        questions = current_round.questions.order_by("id")
        current_index = (
            list(questions).index(self.current_question)
            if self.current_question
            else -1
        )

        if current_index + 1 < len(questions):
            # Move to the next question
            self.current_question = questions[current_index + 1]
            self.save()
        else:
            # If no more questions, move to the next round
            self.next_round()

    def next_round(self):
        """
        Progress to the next round, or complete the challenge if no more rounds.
        """
        rounds = Round.objects.filter(challenge=self).order_by("round_number")

        if self.current_round < len(rounds):
            # Move to the next round
            self.current_round += 1
            self.current_question = (
                None  # Reset current question for the new round
            )
            self.save()
        else:
            # No more rounds, mark the challenge as completed
            self.status = "completed"
            self.save()

    def mark_completed(self):
        """
        Explicitly mark the challenge as completed.
        """
        self.status = "completed"
        self.save()


class ChallengeParticipant(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="participated_challenges",
        null=True,
        blank=True,
    )
    username = models.CharField(max_length=255, blank=True, null=True)
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE, related_name="participants"
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(
        default=True
    )  # To track if the user left the challenge
    score = models.IntegerField(default=0, null=True, blank=True)
    rejoined_at = models.DateTimeField(null=True, blank=True)  # Optional
    def __str__(self):
        return f"Participant: {self.user}"


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
    time_limit = models.IntegerField(default=30)  # Default 30 seconds per question
    time_started = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    time_ended = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return (
            f"Question {self.question.id} in Challenge: {self.challenge.title}"
        )


class AnswerSubmission(models.Model):
    participant = models.ForeignKey(
        ChallengeParticipant, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(
        ChallengeQuestion, on_delete=models.CASCADE, related_name="submissions"
    )
    answer = models.TextField()  # Stores the submitted answer
    is_correct = models.BooleanField(
        null=True, blank=True
    )  # Marked after validation
    submitted_at = models.DateTimeField(auto_now_add=True)
    time_taken = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Answer by {self.participant.user.username} for {self.question.question.id}"

class ChallengeEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ("challenge_started", "Challenge Started"),
        ("challenge_completed", "Challenge Completed"),
        ("user_joined", "User Joined"),
        ("user_left", "User Left"),
        ("question_asked", "Question Asked"),
        ("answer_submitted", "Answer Submitted"),
        ("round_started", "Round Started"),
        ("round_completed", "Round Completed"),
    ]

    challenge = models.ForeignKey(
        "Challenge", on_delete=models.CASCADE, related_name="events"
    )
    participant = models.ForeignKey(
        "ChallengeParticipant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )  # Optional, for user-specific events
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(
        null=True, blank=True
    )  # Store extra details about the event (e.g., answer, time taken)

    def __str__(self):
        return f"{self.event_type} at {self.timestamp} for Challenge {self.challenge.title}"
