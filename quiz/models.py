# Create your models here.
from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    avatar = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Quiz(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    categories = models.ManyToManyField(
        Category, related_name="quizzes"
    )  # Link quizzes to categories
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="quizzes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ("text", "Text"),
        ("image", "Image URL"),
        ("video", "Video URL"),
        ("audio", "Audio URL"),
    ]

    question_text = models.TextField(blank=True)  # For text questions
    question_url = models.URLField(blank=True, null=True)  # For multimedia questions
    question_type = models.CharField(
        max_length=10, choices=QUESTION_TYPE_CHOICES, default="text"
    )
    quizzes = models.ManyToManyField(
        Quiz, related_name="questions"
    )  # Many-to-many with quizzes

    def __str__(self):
        return f"Question: {self.question_text[:50]}"


class Answer(models.Model):
    ANSWER_TYPE_CHOICES = [
        ("text", "Text"),
        ("image", "Image URL"),
        ("video", "Video URL"),
        ("audio", "Audio URL"),
    ]

    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="answers"
    )
    answer_text = models.TextField(blank=True)  # For text answers
    answer_url = models.URLField(blank=True, null=True)  # For multimedia answers
    answer_type = models.CharField(
        max_length=10, choices=ANSWER_TYPE_CHOICES, default="text"
    )
    is_correct = models.BooleanField(default=False)  # Whether this is a correct answer

    def __str__(self):
        return f"Answer for {self.question}: {self.answer_text[:50]}"


class QuizAttempt(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="quiz_attempts"
    )
    quiz = models.ForeignKey("Quiz", on_delete=models.CASCADE, related_name="attempts")
    score = models.PositiveIntegerField()
    total_questions = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - {self.score}/{self.total_questions}"
