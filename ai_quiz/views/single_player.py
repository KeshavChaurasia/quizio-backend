import logging
from rest_framework.views import APIView
from adrf.views import APIView as AsyncAPIView
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ai_quiz.ai import generate_questions, generate_subtopics
from ai_quiz.models import (
    Game,
    Participant,
    Question,
    SinglePlayerGame,
    SinglePlayerQuestion,
    Topic,
)
from ai_quiz.serializers import (
    QuestionsRequestSerializer,
    QuestionsResponseSerializer,
    SingleQuestionsResponseSerializer,
    SubtopicsRequestSerializer,
    SubtopicsResponseSerializer,
)


class StartSinglePlayerGameAPIView(AsyncAPIView):
    # TODO: See if I really need this
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=QuestionsRequestSerializer,
        responses={
            201: SingleQuestionsResponseSerializer,
        },
        operation_description="Create a room with a custom serializer",
    )
    async def post(self, request, *args, **kwargs):
        serializer = QuestionsRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # Create a game object
        game, created = await SinglePlayerGame.objects.aget_or_create(
            user=request.user, status="in_progress"
        )
        if not created:
            return Response(
                {
                    "error": "You can only have a single game running",
                    "gameId": game.id,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        topic = await Topic.objects.acreate(
            name=serializer.data.get("topic"),
            subtopics=serializer.data.get("subtopics"),
        )
        questions = await generate_questions(**serializer.data)

        questions = await SinglePlayerQuestion.objects.abulk_create(
            [
                SinglePlayerQuestion(
                    game=game,
                    question=q.question,
                    subtopic=q.subtopic,
                    topic=topic,
                    options=q.options,
                    correct_answer=q.answer,
                    timer=serializer.data.get("timer"),
                    difficulty=serializer.data.get("difficulty"),
                )
                for q in questions.questions
            ]
        )
        response_data = {
            "gameId": game.id,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class QuestionsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            game: SinglePlayerGame = request.user.single_player_games.get(
                status="in_progress"
            )
        except SinglePlayerGame.DoesNotExist:
            return Response(
                {"error": "Game not found"}, status=status.HTTP_404_NOT_FOUND
            )
        questions = game.questions.all()
        serializer = SingleQuestionsResponseSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CheckAnswerAPIView(APIView):
    def post(self, request, *args, **kwargs):
        question_id = request.data.get("questionId")
        answer = request.data.get("answer")
        if not question_id:
            return Response(
                {"error": "questionId required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        game: SinglePlayerGame = request.user.single_player_games.filter(
            status="in_progress"
        ).first()
        if game is None:
            return Response(
                {"error": "Game not found"}, status=status.HTTP_404_NOT_FOUND
            )
        try:
            current_question: SinglePlayerQuestion = game.questions.all()[
                game.current_question
            ]
            question = SinglePlayerQuestion.objects.get(id=question_id, game=game)
            if current_question.id != question.id:
                return Response(
                    {
                        "error": "You can only answer the current question",
                        "question": {
                            "questionId": current_question.id,
                            "question": current_question.question,
                            "options": current_question.options,
                            "timer": current_question.timer,
                        },
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except IndexError:
            game.end_game()
            return Response(
                {"error": "No more questions to answer"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except SinglePlayerQuestion.DoesNotExist:
            return Response(
                {"error": "Question not found"}, status=status.HTTP_404_NOT_FOUND
            )

        question.answered = True if answer else False
        question.skipped = False if answer else True
        question.save()
        game.current_question += 1
        game.save()
        if question.correct_answer == answer:
            return Response({"correct": True}, status=status.HTTP_200_OK)
        return Response(
            {"correct": False, "answer": question.correct_answer},
            status=status.HTTP_200_OK,
        )
