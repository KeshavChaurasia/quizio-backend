from rest_framework import serializers

from ai_quiz.models import Question


class ErrorSerializer(serializers.Serializer):
    error = serializers.CharField(max_length=100)


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["question", "options", "timer", "id"]


class CreateRoomRequestSerializer(serializers.Serializer):
    pass


class HostSerializer(serializers.Serializer):
    userId = serializers.CharField(max_length=100)
    userName = serializers.CharField(max_length=100)
    role = serializers.CharField(max_length=100)


class CreateRoomResponseSerializer(serializers.Serializer):
    roomId = serializers.CharField(max_length=100)
    roomCode = serializers.CharField(max_length=8)
    qrCode = serializers.CharField(max_length=1024)
    host = serializers.DictField(child=HostSerializer())
    ws = serializers.CharField(max_length=1024)


class PlayerSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100)
    avatarStyle = serializers.CharField(max_length=100)
    avatarSeed = serializers.CharField(max_length=100)


class JoinRoomRequestSerializer(serializers.Serializer):
    roomCode = serializers.CharField(max_length=8)
    player = PlayerSerializer(many=False)


class JoinRoomResponseSerializer(serializers.Serializer):
    userId = serializers.CharField(max_length=100)
    username = serializers.CharField(max_length=100)
    roomId = serializers.CharField(max_length=100)
    roomCode = serializers.CharField(max_length=8)
    role = serializers.CharField(max_length=100)
    ws = serializers.CharField(max_length=1024)


class CreateGameRequestSerializer(serializers.Serializer):
    roomCode = serializers.CharField(max_length=8)
    topic = serializers.CharField(max_length=100)
    subtopics = serializers.ListField(child=serializers.CharField(max_length=100))
    n = serializers.IntegerField()
    difficulty = serializers.CharField(max_length=10)


class CreateGameResponseSerializer(serializers.Serializer):
    gameId = serializers.CharField(max_length=100)


class StartGameRequestSerializer(serializers.Serializer):
    roomCode = serializers.CharField(max_length=8)


class StartGameResponseSerializer(serializers.Serializer):
    gameId = serializers.CharField(max_length=100)


class EndGameRequestSerializer(serializers.Serializer):
    roomCode = serializers.CharField(max_length=8)


class SubtopicsRequestSerializer(serializers.Serializer):
    topic = serializers.CharField(max_length=100)


class SubtopicsResponseSerializer(serializers.Serializer):
    subtopics = serializers.ListField(child=serializers.CharField(max_length=100))


class QuestionsRequestSerializer(serializers.Serializer):
    topic = serializers.CharField(max_length=100)
    subtopics = serializers.ListField(child=serializers.CharField(max_length=100))
    n = serializers.IntegerField()
    difficulty = serializers.CharField(max_length=10)
    timer = serializers.IntegerField()


class SingleQuestionsResponseSerializer(serializers.Serializer):
    questionId = serializers.CharField(max_length=100, source="id")
    question = serializers.CharField(max_length=1024)
    options = serializers.ListField(child=serializers.CharField(max_length=1024))
    timer = serializers.IntegerField()


class QuestionsResponseSerializer(serializers.ListSerializer):
    child = SingleQuestionsResponseSerializer()


class NextGameQuestionRequestSerializer(serializers.Serializer):
    gameId = serializers.CharField(max_length=100)


class CheckAnswerRequestSerializer(serializers.Serializer):
    questionId = serializers.CharField(max_length=100)
    answer = serializers.CharField(max_length=1024)
