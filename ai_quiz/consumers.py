import json
from collections import defaultdict

from channels.db import database_sync_to_async, sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from rest_framework_simplejwt.tokens import UntypedToken

from ai_quiz.models import Game, Participant, Room
from ai_quiz.serializers import QuestionSerializer


class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope["url_route"]["kwargs"]["room_code"]

        await self.channel_layer.group_add(self.room_code, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        participants = await database_sync_to_async(Participant.objects.filter)(
            Q(user__username=self.username) | Q(guest_user__username=self.username),
            room__room_code=self.room_code,
        )
        if not await participants.aexists():
            return
        participant = await participants.afirst()
        participant.status = "inactive"
        await participant.asave()
        await self.send_all_player_names()
        await self.channel_layer.group_discard(self.room_code, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data["type"]
        if event_type == "player_ready":
            await self.handle_player_ready(data)
            await self.send_all_player_names()
        elif event_type == "player_waiting":
            await self.handle_player_waiting(data)
        elif event_type == "next_question":
            await self.handle_next_question(data)
        elif event_type == "question_answered":
            pass
        elif event_type == "question_skipped":
            pass
        else:
            raise ValueError("Invalid event type")

    @sync_to_async
    def get_all_participants(self):
        room = Room.objects.filter(room_code=self.room_code)
        if room.exists():
            participants = room.first().participants.filter(~Q(status="inactive"))
            return [p.user.username for p in participants if p.user] + [
                p.guest_user.username for p in participants if p.guest_user
            ]

    async def send_all_player_names(self):
        usernames = await self.get_all_participants()
        await self.channel_layer.group_send(
            self.room_code,
            {
                "type": "room_message",
                "event": {"type": "all_players", "usernames": usernames},
            },
        )

    @database_sync_to_async
    def get_next_question(self):
        games = Game.objects.filter(
            room__room_code=self.room_code, status="in_progress"
        )
        if not games.exists():
            return None
        game = games.latest("created_at")
        questions = game.questions.all()
        if game.current_question < len(questions):
            new_question = questions[game.current_question]
            game.current_question += 1
            game.save()
            return new_question
        # This means the game is over
        game.status = "finished"
        game.ended_at = timezone.now()
        game.save()
        return None

    async def handle_next_question(self, data):
        token = data.get("token")
        if not token:
            await self.channel_layer.send(
                self.channel_name,
                {"type": "room_message", "event": {"error": "No token found."}},
            )
            return
        user = await self.authenticate_user(token)
        if user is None:
            await self.channel_layer.send(
                self.channel_name,
                {
                    "type": "room_message",
                    "event": {"error": "Token is invalid."},
                },
            )
            return
        else:
            await self.channel_layer.send(
                self.channel_name,
                {
                    "type": "room_message",
                    "event": {"success": f"Authenticated user: {user}"},
                },
            )
        question = await self.get_next_question()
        if question is not None:
            question_serializer = QuestionSerializer(question)
            await self.channel_layer.group_send(
                self.room_code,
                {
                    "type": "room_message",
                    "event": {
                        "type": "next_question",
                        "event": question_serializer.data,
                    },
                },
            )
        else:
            await self.channel_layer.group_send(
                self.room_code,
                {
                    "type": "room_message",
                    "event": {"type": "all_questions_done"},
                },
            )

    @sync_to_async
    def update_participant(self, username, status="ready"):
        participants = Participant.objects.filter(
            Q(user__username=username) | Q(guest_user__username=username),
            room__room_code=self.room_code,
        )
        if participants.exists():
            participant = participants.first()
            if participant.status != status:
                participant.status = status
                participant.save()
            return participant
        return None

    async def handle_player_waiting(self, data):
        # If player is waiting, update the status in the database
        # and broadcast a message to all the users in the room using event type "player_waiting"
        username = data["username"]

        participant = await self.update_participant(username, status="waiting")
        if participant:
            await self.channel_layer.group_send(
                self.room_code,
                {
                    "type": "room_message",
                    "event": {"type": "player_waiting", "username": username},
                },
            )
        else:
            await self.send(text_data=json.dumps({"error": "Participant not found"}))

    async def handle_player_ready(self, data):
        # If player is ready, update the status in the database
        # and broadcast a message to all the users in the room using event type "player_ready"
        username = data["username"]
        self.username = username
        participant = await self.update_participant(username, status="ready")
        if participant:
            await self.channel_layer.group_send(
                self.room_code,
                {
                    "type": "room_message",
                    "event": {"type": "player_ready", "username": username},
                },
            )
        else:
            await self.send(text_data=json.dumps({"error": "Participant not found"}))

    async def room_message(self, event):
        message = event["event"]
        await self.send(text_data=json.dumps({"message": message}))

    @database_sync_to_async
    def authenticate_user(self, token):
        try:
            # Validate the token using Simple JWT
            UntypedToken(token)  # Validate token
            user_id = UntypedToken(token).payload["user_id"]
            User = get_user_model()
            return User.objects.get(id=user_id)
        except Exception:
            return None
