from rest_framework import serializers

from ai_quiz.models import Question


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["question", "options", "timer", "id"]


class CreateRoomSerializer(serializers.Serializer):
    pass


class JoinRoomSerializer(serializers.Serializer):
    roomCode = serializers.CharField(max_length=8)
    username = serializers.CharField(max_length=100)


class CreateGameSerializer(serializers.Serializer):
    roomCode = serializers.CharField(max_length=8)
    topic = serializers.CharField(max_length=100)
    subtopics = serializers.ListField(child=serializers.CharField(max_length=100))
    n = serializers.IntegerField()
    difficulty = serializers.CharField(max_length=10)


class StartGameSerializer(serializers.Serializer):
    roomCode = serializers.CharField(max_length=8)


class EndGameSerializer(serializers.Serializer):
    roomCode = serializers.CharField(max_length=8)


class SubtopicsSerializer(serializers.Serializer):
    topic = serializers.CharField(max_length=100)
