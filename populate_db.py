import os
import django
import random
from django.utils import timezone
from datetime import timedelta

# Setup Django environment if running this script standalone
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quizio.settings")
django.setup()

from quiz.models import Quiz, Question, Answer, Category, QuizAttempt
from django.contrib.auth.models import User


def populate_db():
    # Create Users
    user1, created = User.objects.get_or_create(
        username="user1", email="user@example.com"
    )
    if created:
        user1.set_password("user1password")
        user1.save()

    user2, created = User.objects.get_or_create(
        username="user2", email="user2@example.com"
    )
    if created:
        user2.set_password("user2password")
        user2.save()

    # Create Categories
    category1 = Category.objects.create(name="General Knowledge")
    category2 = Category.objects.create(name="Science")

    # Create Quizzes
    quiz1 = Quiz.objects.create(
        title="Quiz 1", description="This is Quiz 1", created_by=user1
    )
    quiz2 = Quiz.objects.create(
        title="Quiz 2", description="This is Quiz 2", created_by=user1
    )

    # Assign categories to quizzes
    quiz1.categories.add(category1)
    quiz2.categories.add(category2)

    # Create Questions
    questions_data = [
        {
            "question_text": "What is the capital of France?",
            "answers": [
                {"text": "Paris", "is_correct": True},
                {"text": "Berlin", "is_correct": False},
                {"text": "Madrid", "is_correct": False},
                {"text": "Rome", "is_correct": False},
            ],
            "quizzes": [quiz1],
        },
        {
            "question_text": "Which planet is known as the Red Planet?",
            "answers": [
                {"text": "Earth", "is_correct": False},
                {"text": "Mars", "is_correct": True},
                {"text": "Jupiter", "is_correct": False},
                {"text": "Venus", "is_correct": False},
            ],
            "quizzes": [quiz1, quiz2],
        },
        {
            "question_text": "What is the boiling point of water?",
            "answers": [
                {"text": "100°C", "is_correct": True},
                {"text": "50°C", "is_correct": False},
                {"text": "150°C", "is_correct": False},
                {"text": "200°C", "is_correct": False},
            ],
            "quizzes": [quiz2],
        },
        {
            "question_text": "Who wrote 'Romeo and Juliet'?",
            "answers": [
                {"text": "William Shakespeare", "is_correct": True},
                {"text": "Charles Dickens", "is_correct": False},
                {"text": "Jane Austen", "is_correct": False},
                {"text": "Mark Twain", "is_correct": False},
            ],
            "quizzes": [quiz1],
        },
        {
            "question_text": "Which gas do plants absorb from the atmosphere?",
            "answers": [
                {"text": "Oxygen", "is_correct": False},
                {"text": "Carbon Dioxide", "is_correct": True},
                {"text": "Nitrogen", "is_correct": False},
                {"text": "Hydrogen", "is_correct": False},
            ],
            "quizzes": [quiz2],
        },
    ]

    # Add questions and answers to the database
    for question_data in questions_data:
        question = Question.objects.create(
            question_text=question_data["question_text"],
            question_type="text",  # For simplicity, using text-based questions
        )
        question.quizzes.set(question_data["quizzes"])
        question.save()

        for answer_data in question_data["answers"]:
            Answer.objects.create(
                question=question,
                answer_text=answer_data["text"],
                is_correct=answer_data["is_correct"],
                answer_type="text",  # For simplicity, using text-based answers
            )

    print("Quizzes and Questions populated successfully!")

    # Create some quiz attempts for users
    quizzes = [quiz1, quiz2]
    users = [user1, user2]

    for user in users:
        for quiz in quizzes:
            # Randomly simulate quiz attempts
            total_questions = quiz.questions.count()
            correct_answers = random.randint(
                0, total_questions
            )  # Random score between 0 and total questions

            # Create a quiz attempt
            quiz_attempt = QuizAttempt.objects.create(
                user=user,
                quiz=quiz,
                score=correct_answers,
                total_questions=total_questions,
                created_at=timezone.now()
                - timedelta(
                    days=random.randint(1, 30)
                ),  # Random date in the last 30 days
            )

            print(
                f"Created quiz attempt for {user.username} on {quiz.title} with {correct_answers}/{total_questions} correct answers."
            )

    print("Quiz attempts populated successfully!")


if __name__ == "__main__":
    populate_db()
