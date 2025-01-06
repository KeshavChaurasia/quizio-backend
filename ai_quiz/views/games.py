import logging
from django.db.models import Q
from adrf.views import APIView as AsyncAPIView
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from ai_quiz.ai import generate_questions, generate_subtopics
from ai_quiz.models import Game, Participant, Question, Room, Topic
from ai_quiz.serializers import (
    CreateGameRequestSerializer,
    CreateGameResponseSerializer,
    StartGameRequestSerializer,
    StartGameResponseSerializer,
)

logger = logging.getLogger(__name__)
User = get_user_model()


class CreateGameView(AsyncAPIView):
    permission_classes = [IsAuthenticated]

    @database_sync_to_async
    def validate_room(self, user) -> Room | None:
        """Validate the room code and return the room object."""
        try:
            room = user.hosted_rooms.get(Q(status="active") | Q(status="waiting"))
        except Room.DoesNotExist:
            return None
        return room

    async def validate_game(self, room: Room):
        """Validate if a game is already in progress."""
        try:
            game = await Game.aget_current_game_for_room(room.room_code)
            return game
        except Game.DoesNotExist:
            return None

    async def create_game(
        self, room: Room, topic: str, n, difficulty: str, time_per_question: int = 30
    ):
        """Create a new game object associated with the room."""
        game = await Game.objects.acreate(room=room, status="waiting")
        await database_sync_to_async(game.create_leaderboard)()
        subtopics = await generate_subtopics(topic)
        await self._fetch_and_create_questions(
            game=game,
            topic=topic,
            subtopics=subtopics.subtopics,
            n=n,
            difficulty=difficulty,
            time_per_question=time_per_question,
        )
        return game.id

    async def _fetch_and_create_questions(
        self,
        game: Game,
        topic: str,
        subtopics: list[str],
        n: int,
        difficulty: str,
        time_per_question: int = 30,
    ):
        """Fetch questions from the AI backend and create question objects."""
        questions = await generate_questions(
            topic=topic,
            subtopics=subtopics,
            n=n,
            difficulty=difficulty,
        )
        topic = await Topic.objects.acreate(name=topic, subtopics=subtopics)
        questions = await Question.objects.abulk_create(
            [
                Question(
                    game=game,
                    subtopic=question.subtopic,
                    question=question.question,
                    correct_answer=question.answer,
                    options=question.options,
                    topic=topic,
                    time_per_question=time_per_question,
                )
                for question in questions.questions
            ]
        )
        return questions

    @swagger_auto_schema(
        request_body=CreateGameRequestSerializer,
        responses={
            201: CreateGameResponseSerializer,
        },
        operation_description="Create a room with a custom serializer",
    )
    async def post(self, request, *args, **kwargs):
        serializer = CreateGameRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )
        data = serializer.validated_data
        # Check if the room exists
        room: Room = await self.validate_room(request.user)
        if room is None:
            return Response(
                {"error": "No active rooms found for user."},
                status=status.HTTP_404_NOT_FOUND,
            )
        await room.aend_all_games()
        await Participant.objects.aget_or_create(
            room=room, user=request.user, status="ready"
        )
        game_id = await self.create_game(
            room, data["topic"], data["n"], data["difficulty"], data["timePerQuestion"]
        )
        response_data = {
            "gameId": game_id,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class StartGameView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=StartGameRequestSerializer,
        responses={
            201: StartGameResponseSerializer,
        },
        operation_description="Create a room with a custom serializer",
    )
    def post(self, request, *args, **kwargs):
        """Start the game."""
        room: Room = request.user.hosted_rooms.filter(
            Q(status="active") | Q(status="waiting")
        ).first()
        if not room:
            return Response(
                {"error": "You are not hosting any active rooms."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            # We need to check if all players are ready before starting the game
            if room.participants.exclude(
                Q(status="ready") | Q(status="inactive")
            ).exists():
                return Response(
                    {"error": "All participants must be ready to start the game."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            game: Game = room.get_current_game()
            game.status = "in_progress"
            game.save()
            room.status = "active"
            room.save()
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        response_data = {
            "gameId": game.id,
        }
        return Response(response_data, status=status.HTTP_200_OK)


class EndGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """End the game."""
        room_code = request.data.get("roomCode")
        if not room_code:
            return Response(
                {"error": "roomCode required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the room exists
        game = Game.get_current_game_for_room(room_code)
        if game is None:
            return Response(
                {"error": "No active games found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if the requesting user is the host
        if game.room.host != request.user:
            return Response(
                {"error": "Only the host can end the game."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # End the game (e.g., setting a game state, etc.)
        game.end_game()
        return Response({"status": "game_ended"}, status=status.HTTP_200_OK)
