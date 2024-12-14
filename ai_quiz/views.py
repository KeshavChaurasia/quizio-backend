from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from ai_quiz.models import Room
import qrcode
from io import BytesIO
import base64
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

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
        user_name = request.data.get("userName")

        if not user_name:
            return Response(
                {"error": "userName is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Use the authenticated user as the host
        user = request.user  # This will be the logged-in host
        print("*****************************")
        print("user", user, type(user))
        print("*****************************")
        # Create a new room for the host
        room_id = str(
            Room.objects.count() + 1
        )  # Generate a simple room ID (this can be improved)
        room = Room.objects.create(room_id=room_id, host=user)

        # Generate the join link and QR code
        join_link = f"https://example.com/room/{room_id}"
        qr_code = generate_qr_code(join_link)

        # Construct the response data
        response_data = {
            "roomId": room.room_id,
            "joinLink": join_link,
            "qrCode": qr_code,
            "host": {
                "userId": f"host-{user.id}",
                "userName": user.username,
                "role": "host",
            },
            "ws": f"wss://example.com/rooms/{room_id}?token={user.auth_token.key}",  # WebSocket URL with token
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ai_quiz.models import Room, GuestUser


class JoinRoomView(APIView):
    def post(self, request, *args, **kwargs):
        """Allow a participant to join the room."""
        room_id = request.data.get("roomId")
        user_name = request.data.get("userName")

        if not room_id or not user_name:
            return Response(
                {"error": "roomId and userName are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the room exists
        try:
            room = Room.objects.get(room_id=room_id)
        except Room.DoesNotExist:
            return Response(
                {"error": "Room not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Create a new guest user
        guest_user = GuestUser.objects.create(user_name=user_name, room=room)

        # Construct the response data for the participant
        response_data = {
            "userId": f"guest-{guest_user.id}",
            "roomId": room.room_id,
            "userName": guest_user.user_name,
            "role": "player",
        }

        return Response(response_data, status=status.HTTP_200_OK)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ai_quiz.models import Room
from rest_framework.permissions import IsAuthenticated


class StartGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Start the game."""
        room_id = request.data.get("roomId")

        if not room_id:
            return Response(
                {"error": "roomId is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Check if the room exists
        try:
            room = Room.objects.get(room_id=room_id)
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

        # Start the game (e.g., setting a game state, etc.)
        # For now, we will just return a success response
        return Response({"status": "game_started"}, status=status.HTTP_200_OK)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ai_quiz.models import Room
from rest_framework.permissions import IsAuthenticated


class EndGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """End the game."""
        room_id = request.data.get("roomId")

        if not room_id:
            return Response(
                {"error": "roomId is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Check if the room exists
        try:
            room = Room.objects.get(room_id=room_id)
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
        # For now, we will just return a success response
        return Response({"status": "game_ended"}, status=status.HTTP_200_OK)
