import logging
from rest_framework.views import APIView
from adrf.views import APIView as AsyncAPIView
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ai_quiz.ai import generate_questions, generate_subtopics
from ai_quiz.models import Question
from ai_quiz.serializers import (
    QuestionsRequestSerializer,
    SubtopicsRequestSerializer,
    SubtopicsResponseSerializer,
)

logger = logging.getLogger(__name__)
User = get_user_model()


class SubtopicsAPIView(AsyncAPIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=SubtopicsRequestSerializer,
        responses={
            201: SubtopicsResponseSerializer,
        },
        operation_description="Create a room with a custom serializer",
    )
    async def post(self, request, *args, **kwargs):
        topic = request.data.get("topic")
        if not topic:
            return Response(
                {"error": "`topic` is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subtopics = await generate_subtopics(topic)
        return Response({"subtopics": subtopics.subtopics}, status=status.HTTP_200_OK)


class QuestionsAPIView(AsyncAPIView):
    # TODO: See if I really need this
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=QuestionsRequestSerializer,
        responses={
            201: SubtopicsResponseSerializer,
        },
        operation_description="Create a room with a custom serializer",
    )
    async def post(self, request, *args, **kwargs):
        serializer = QuestionsRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        questions = await generate_questions(**serializer.data)
        # Create question objects here
        questions = await Question.objects.abulk_create(
            [
                Question(
                    question=q.question,
                    options=q.options,
                    timer=q.timer,
                    subtopic=q.subtopic,
                    difficulty=q.difficulty,
                )
                for q in questions.questions
            ]
        )
        return Response({"subtopics": subtopics.subtopics}, status=status.HTTP_200_OK)


class CheckAnswerApiView(APIView):
    def post(self, request, *args, **kwargs):
        pass
