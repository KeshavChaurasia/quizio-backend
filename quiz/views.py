from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from quiz.models import Quiz, QuizAttempt
from quiz.serializers import (
    ProfileSerializer,
    QuestionSerializer,
    QuizAttemptSerializer,
    UserSerializer,
)


@api_view(["POST"])
def register_user(request):
    data = request.data
    try:
        if User.objects.filter(username=data["username"]).exists():
            return Response(
                {"error": "Username already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(email=data["email"]).exists():
            return Response(
                {"error": "Email already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = User.objects.create(
            username=data["username"],
            email=data["email"],
            password=make_password(data["password"]),
        )
        return Response(
            {"message": "User registered successfully"},
            status=status.HTTP_201_CREATED,
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    if request.method == "GET":
        serializer = UserSerializer(user)
        return Response(serializer.data)

    elif request.method == "PUT":
        profile = user.profile  # Access the related profile object
        data = request.data.get("profile", {})
        serializer = ProfileSerializer(
            instance=profile, data=data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    data = request.data
    if not user.check_password(data["old_password"]):
        return Response(
            {"error": "Old password is incorrect"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if data["new_password"] != data["confirm_password"]:
        return Response(
            {"error": "New passwords do not match"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    user.set_password(data["new_password"])
    user.save()
    update_session_auth_hash(
        request, user
    )  # Keeps the user logged in after password change
    return Response(
        {"message": "Password updated successfully"}, status=status.HTTP_200_OK
    )


token_generator = PasswordResetTokenGenerator()


@api_view(["POST"])
def forgot_password(request):
    data = request.data
    try:
        user = User.objects.get(email=data["email"])
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"http://localhost:3000/reset-password/{uid}/{token}/"
        send_mail(
            "Password Reset Request",
            f"Click the link to reset your password: {reset_link}",
            "noreply@example.com",
            [user.email],
            fail_silently=False,
        )
        return Response(
            {"message": "Password reset email sent"}, status=status.HTTP_200_OK
        )
    except User.DoesNotExist:
        return Response(
            {"error": "No user with this email exists"},
            status=status.HTTP_404_NOT_FOUND,
        )


class TakeQuizView(APIView):
    permission_classes = []  # Allow all users (including anonymous users)

    def get(self, request, quiz_id):
        """
        Retrieve all questions for the specified quiz.
        """
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found"}, status=404)

        # Get all questions related to the quiz
        questions = (
            quiz.questions.all()
        )  # Assuming a related_name="questions" in Quiz model
        question_serializer = QuestionSerializer(questions, many=True)

        return Response(
            {"quiz_title": quiz.title, "questions": question_serializer.data},
            status=200,
        )

    def post(self, request, quiz_id):
        """
        Handle quiz submissions by calculating the score.
        """
        user = request.user
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found"}, status=404)

        # Validate submitted answers
        submitted_answers = request.data.get("answers", {})
        if not isinstance(submitted_answers, dict):
            return Response(
                {"error": "Answers should be a dictionary"}, status=400
            )

        questions = quiz.questions.all()
        total_questions = questions.count()
        score = 0

        for question in questions:
            correct_answers = set(
                question.answers.filter(is_correct=True).values_list(
                    "id", flat=True
                )
            )
            user_answers = set(submitted_answers.get(str(question.id), []))

            if correct_answers == user_answers:
                score += 1

        # Handle anonymous and authenticated users
        if isinstance(user, AnonymousUser):
            user = None  # Assign None for anonymous users

        # Save quiz attempt
        quiz_attempt = QuizAttempt.objects.create(
            user=user,  # Will be None for anonymous users
            quiz=quiz,
            score=score,
            total_questions=total_questions,
        )

        attempt_serializer = QuizAttemptSerializer(quiz_attempt)

        return Response(
            {
                "quiz_attempt": attempt_serializer.data,
                "questions": QuestionSerializer(questions, many=True).data,
            },
            status=201,
        )
