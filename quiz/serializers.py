from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, QuizAttempt


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["bio", "avatar"]


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ["id", "username", "email", "profile"]


class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "user",
            "quiz",
            "score",
            "total_questions",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
