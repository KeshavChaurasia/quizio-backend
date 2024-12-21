import base64
import logging
from io import BytesIO

import qrcode
from adrf.views import APIView as AsyncAPIView
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from ai_quiz.ai import generate_questions, generate_subtopics
from ai_quiz.models import Game, GuestUser, Participant, Question, Room, Topic
from ai_quiz.serializers import (
    CreateGameRequestSerializer,
    CreateGameResponseSerializer,
    CreateRoomRequestSerializer,
    CreateRoomResponseSerializer,
    JoinRoomRequestSerializer,
    JoinRoomResponseSerializer,
    StartGameRequestSerializer,
    StartGameResponseSerializer,
    SubtopicsRequestSerializer,
    SubtopicsResponseSerializer,
)
from quizio.utils import generate_qr_code

logger = logging.getLogger(__name__)
User = get_user_model()


class CreateRoomView(APIView):
    permission_classes = [
        IsAuthenticated
    ]  # Ensure only authenticated users can create a room

    @swagger_auto_schema(
        request_body=CreateRoomRequestSerializer,
        responses={
            201: CreateRoomResponseSerializer,
        },
        operation_description="Create a room with a custom serializer",
    )
    def post(self, request, *args, **kwargs):
        """Handle room creation by the host."""
        user = request.user  # This will be the logged-in host

        # Check if a room already exists for the host
        room = Room.objects.filter(host=user, status="active")
        if room.exists():
            room = room.first()
            qr_code = generate_qr_code(room.room_code)
            response_data = {
                "roomId": room.room_id,
                "roomCode": room.room_code,
                "qrCode": qr_code,
                "host": {
                    "userId": f"host-{user.id}",
                    "userName": user.username,
                    "role": "host",
                },
                "ws": f"/rooms/{room.room_code}",  # WebSocket URL with token
            }
            return Response(response_data, status=status.HTTP_200_OK)
        # Create a new room for the host
        room = Room.objects.create(host=user)

        # Generate the join link and QR code
        room_code = room.room_code
        qr_code = generate_qr_code(room_code)

        # Construct the response data
        response_data = {
            "roomId": room.room_id,
            "roomCode": room_code,
            "qrCode": qr_code,
            "host": {
                "userId": f"host-{user.id}",
                "userName": user.username,
                "role": "host",
            },
            "ws": f"/rooms/{room_code}",  # WebSocket URL with token
        }
        Participant.objects.create(user=request.user, room=room).save()
        return Response(response_data, status=status.HTTP_201_CREATED)


class JoinRoomView(APIView):
    @swagger_auto_schema(
        request_body=JoinRoomRequestSerializer,
        responses={
            201: JoinRoomResponseSerializer,
        },
        operation_description="Create a room with a custom serializer",
    )
    def post(self, request, *args, **kwargs):
        """Allow a participant to join the room."""
        room_code = request.data.get("roomCode")
        username = request.data.get("username")

        if not room_code or not username:
            return Response(
                {"error": "roomCode and username are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the room exists
        try:
            room = Room.objects.get(room_code=room_code, status="active")
        except Room.DoesNotExist:
            return Response(
                {"error": "Room not found or has already been closed."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if request.user == room.host:
            return Response(
                {"error": "Host is already in the room."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if the user is a logged in user
        if request.user.is_authenticated:
            user = request.user
        else:
            if GuestUser.objects.filter(username=username, room=room).exists():
                return Response(
                    {"error": "Username is already taken."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user = GuestUser.objects.create(username=username, room=room)
        # Create a participant object for the user
        if isinstance(user, User):
            participant = Participant.objects.create(user=user, room=room)
        else:
            participant = Participant.objects.create(guest_user=user, room=room)
        # Construct the response data for the participant
        response_data = {
            "userId": user.id,
            "username": user.username,
            "roomId": room.room_id,
            "roomCode": room.room_code,
            "role": "participant",
            "ws": f"/rooms/{room_code}",
        }

        return Response(response_data, status=status.HTTP_200_OK)


class EndRoomView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        active_rooms = user.hosted_rooms.filter(status="active")
        if not active_rooms.exists():
            return Response(
                {"error": "No active rooms found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        room = active_rooms.latest("created_at")
        room.status = "ended"
        room.updated_at = timezone.now()
        room.save()
        return Response({"status": "room_closed"}, status=status.HTTP_200_OK)


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


class CreateGameView(AsyncAPIView):
    permission_classes = [IsAuthenticated]

    async def validate_room(self, room_code):
        """Validate the room code and return the room object."""
        try:
            room = await Room.objects.aget(room_code=room_code, status="active")
        except Room.DoesNotExist:
            return None
        return room

    async def validate_game(self, room: Room):
        """Validate if a game is already in progress."""
        try:
            game = Game.objects.aget(room=room, status="in_progress")
            return game
        except Game.DoesNotExist:
            return None

    async def create_game(self, room, topic, n, difficulty):
        """Create a new game object associated with the room."""
        game = await Game.objects.acreate(room=room, status="waiting")
        subtopics = await generate_subtopics(topic)
        await self._fetch_and_create_questions(
            game=game,
            topic=topic,
            subtopics=subtopics.subtopics,
            n=n,
            difficulty=difficulty,
        )
        return game.id

    async def _get_or_create_topic(self, topic, subtopics):
        """Get or create a topic object with the given subtopics."""
        topic, _ = await Topic.objects.aget_or_create(name=topic)
        topic.subtopics = list(set(subtopics)) + list(set(topic.subtopics))
        await topic.asave()
        return topic

    async def _fetch_and_create_questions(
        self,
        game: Game,
        topic: str,
        subtopics: list[str],
        n: int,
        difficulty: str,
    ):
        """Fetch questions from the AI backend and create question objects."""
        questions = await generate_questions(
            topic=topic,
            subtopics=subtopics,
            n_questions=n,
            difficulty=difficulty,
        )
        questions = await Question.objects.abulk_create(
            [
                Question(
                    game=game,
                    subtopic=question.subtopic,
                    question=question.question,
                    correct_answer=question.answer,
                    options=question.options,
                    topic=await self._get_or_create_topic(topic, subtopics),
                )
                for question in questions.questions
            ]
        )
        return questions

    @database_sync_to_async
    def validate_user(self, room, request):
        return request.user == room.host

    @swagger_auto_schema(
        request_body=CreateGameRequestSerializer,
        responses={
            201: CreateGameResponseSerializer,
        },
        operation_description="Create a room with a custom serializer",
    )
    async def post(self, request, *args, **kwargs):
        room_code = request.data.get("roomCode")
        topic = request.data.get("topic")
        subtopics = request.data.get("subtopics")
        n = request.data.get("n", 5)
        difficulty = request.data.get("difficulty", "easy")
        if not topic or not subtopics:
            return Response(
                {
                    "error": "`topic` and `subtopics` are required; `n` and `difficulty` are optional."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not room_code:
            return Response(
                {"error": "roomCode is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the room exists
        room = await self.validate_room(room_code)
        if room is None:
            return Response(
                {"error": f"Room with code {room_code} not found or has been closed."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if the requesting user is the host
        if not await self.validate_user(room, request):
            return Response(
                {"error": "Only the host can create the game."},
                status=status.HTTP_403_FORBIDDEN,
            )
        game = await self.validate_game(room)

        # There is already a game in progress
        if game is not None:
            return Response(
                {
                    "gameId": game.id,
                },
                status=status.HTTP_200_OK,
            )

        game_id = await self.create_game(room, topic, n, difficulty)
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
        room_code = request.data.get("roomCode")

        if not room_code:
            return Response(
                {"error": "roomCode is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the room exists
        try:
            room = Room.objects.get(room_code=room_code)
        except Room.DoesNotExist:
            return Response(
                {"error": "Room not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if the requesting user is the host
        if room.host != request.user:
            return Response(
                {"error": "Only the host can start the game."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # We need to check if all players are ready before starting the game
            if room.participants.exclude(status="ready").exists():
                return Response(
                    {"error": "All participants must be ready to start the game."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            game = room.get_waiting_game()
            game.create_leaderboard()
            game.status = "in_progress"
            game.save()
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
        game_id = request.data.get("gameId")
        if not room_code or not game_id:
            return Response(
                {"error": "roomCode and gameId required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the room exists
        try:
            room = Room.objects.get(room_code=room_code)
        except Room.DoesNotExist:
            return Response(
                {"error": "Room not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if the requesting user is the host
        if room.host != request.user:
            return Response(
                {"error": "Only the host can end the game."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # End the game (e.g., setting a game state, etc.)
        try:
            room.end_game()
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        # Get the game instances that are in progress and end them

        return Response({"status": "game_ended"}, status=status.HTTP_200_OK)
