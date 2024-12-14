from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.serializers import (
    ProfileSerializer,
    UserSerializer,
)

User = get_user_model()


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
        serializer = ProfileSerializer(instance=profile, data=data, partial=True)
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
