import base64
from io import BytesIO

import qrcode
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_quiz.models import GuestUser, Participant, Room

User = get_user_model()


# Utility function to generate QR code in base64
def generate_qr_code(join_link):
    """Generate a QR code for the join link and return it as a base64 string."""
    img = qrcode.make(join_link)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return qr_code_base64


class CreateRoomView(APIView):
    permission_classes = [
        IsAuthenticated
    ]  # Ensure only authenticated users can create a room

    def post(self, request, *args, **kwargs):
        """Handle room creation by the host."""
        user = request.user  # This will be the logged-in host

        # Check if a room already exists for the host
        room = Room.objects.filter(host=user)
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
    def post(self, request, *args, **kwargs):
        """Allow a participant to join the room."""
        room_code = request.data.get("roomCode")
        username = request.data.get("username")

        if not room_code or not username:
            return Response(
                {"error": "roomId and username are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the room exists
        try:
            room = Room.objects.get(room_code=room_code)
            print("Room exists:", room)
        except Room.DoesNotExist:
            return Response(
                {"error": "Room not found."}, status=status.HTTP_404_NOT_FOUND
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
            "user_id": user.id,
            "username": user.username,
            "room_id": room.room_id,
            "room_code": room.room_code,
            "role": "participant",
            "ws": f"/rooms/{room_code}",
        }

        return Response(response_data, status=status.HTTP_200_OK)


class StartGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Start the game."""
        room_code = request.data.get("room_code")

        if not room_code:
            return Response(
                {"error": "room_code is required"},
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
            game = room.start_new_game()
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        response_data = {
            "status": "game_started",
            "game_id": game.id,
        }
        return Response(response_data, status=status.HTTP_200_OK)


class EndGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """End the game."""
        room_code = request.data.get("room_code")
        game_id = request.data.get("game_id")
        if not room_code or not game_id:
            return Response(
                {"error": "room_code and game_id required"},
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
