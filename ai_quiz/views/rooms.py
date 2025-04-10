from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from ai_quiz.models import GuestUser, Participant, Room
from ai_quiz.serializers import (
    CreateRoomRequestSerializer,
    CreateRoomResponseSerializer,
    JoinRoomRequestSerializer,
    JoinRoomResponseSerializer,
)
from quizio.utils import generate_qr_code

import logging

from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class CreateRoomView(APIView):
    permission_classes = [
        IsAuthenticated
    ]  # Ensure only authenticated users can create a room

    def _get_response(self, room: Room, user, created: bool = False):
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
        response_status = status.HTTP_200_OK if not created else status.HTTP_201_CREATED
        return Response(response_data, status=response_status)

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
        room = Room.objects.filter(Q(status="active") | Q(status="waiting"), host=user)
        if room.exists():
            room = room.first()
            # End all previous games
            # room.end_all_games()
            participant, _ = Participant.objects.get_or_create(
                user=request.user, room=room
            )
            participant.status = "ready"
            participant.avatar_style = user.profile.avatar_style
            participant.avatar_seed = user.profile.avatar_seed
            participant.save()
            room.end_all_games()
            return self._get_response(room, user)
        # Create a new room for the host
        room = Room.objects.create(host=user, status="waiting")

        Participant.objects.create(
            user=request.user,
            room=room,
            status="ready",
            avatar_style=user.profile.avatar_style,
            avatar_seed=user.profile.avatar_seed,
        )
        return self._get_response(room, user, created=True)


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
        serializer = JoinRoomRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        # Check if the room exists
        try:
            room = Room.objects.get(
                Q(status="active") | Q(status="waiting"),
                room_code=data["roomCode"],
            )
        except Room.DoesNotExist:
            return Response(
                {"error": "Room not found or has already been closed."},
                status=status.HTTP_404_NOT_FOUND,
            )
        # Check if the user is a logged in user
        if request.user.is_authenticated:
            user = request.user
        else:
            participant = Participant.get_participant_by_username(
                username=data["player"]["username"], room=room
            )
            if participant:
                return Response(
                    {"error": "Username is already taken."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user = GuestUser.objects.create(
                username=data["player"]["username"], room=room
            )
        # Create a participant object for the user
        if isinstance(user, User):
            participant, _ = Participant.objects.get_or_create(user=user, room=room)
            participant.avatar_style = user.profile.avatar_style
            participant.avatar_seed = user.profile.avatar_seed
            participant.save()
        else:
            participant, _ = Participant.objects.get_or_create(
                guest_user=user, room=room
            )
            participant.avatar_style = data["player"]["avatarStyle"]
            participant.avatar_seed = data["player"]["avatarSeed"]
            participant.save()

        # Construct the response data for the participant
        response_data = {
            **data,
            "roomId": room.room_id,
            "role": "participant" if request.user != room.host else "host",
            "ws": f"/rooms/{room.room_code}",
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


class CheckRoomValidView(APIView):
    def post(self, request, *args, **kwargs):
        room_code = request.data.get("roomCode")
        try:
            room = Room.objects.get(room_code=room_code)
        except Room.DoesNotExist:
            return Response(
                {"valid": False},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"valid": True}, status=status.HTTP_200_OK)
