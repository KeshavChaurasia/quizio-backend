import logging

from adrf.views import APIView as AsyncAPIView
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ai_quiz.ai import generate_questions, generate_subtopics
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
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=SubtopicsRequestSerializer,
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
        return Response({"subtopics": subtopics.subtopics}, status=status.HTTP_200_OK)
