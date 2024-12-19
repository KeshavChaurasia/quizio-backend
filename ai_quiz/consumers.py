# consumers.py
import asyncio
from collections import defaultdict
import json
from urllib.parse import parse_qs

from channels.db import database_sync_to_async, sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework_simplejwt.tokens import UntypedToken

from ai_quiz.models import Game, Participant


class RoomConsumer(AsyncWebsocketConsumer):
    active_users = defaultdict(set)

    async def connect(self):
        print("Connected to websocket")
        print("room code from url is", self.scope["url_route"]["kwargs"])
        self.room_code = self.scope["url_route"]["kwargs"]["room_code"]

        # Join room group
        await self.channel_layer.group_add(self.room_code, self.channel_name)
        print("User connected to room:", self.room_code)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_code, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data["type"]
        if event_type == "player_ready":
            await self.handle_player_ready(data)
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
        # message = data["message"]

    @database_sync_to_async
    def get_next_question(self):
        print("Room code is", self.room_code)
        game = Game.objects.filter(room__room_code=self.room_code).first()
        if not game:
            print("Cannot find game..")
            return None
        questions = game.questions.all()
        if game.current_question < len(questions):
            new_question = questions[game.current_question]
            game.current_question += 1
            game.save()
            print(f"New question is: {new_question}")
            return new_question
        else:
            print("All questions done;")

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
        await self.channel_layer.group_send(
            self.room_code,
            {
                "type": "room_message",
                "event": {"type": "next_question", "event": question},
            },
        )

    @sync_to_async
    def update_participant(self, username, status="ready"):
        print("Room code is:", self.room_code)
        participants = Participant.objects.filter(
            Q(user__username=username) | Q(guest_user__username=username),
            room__room_code=self.room_code,
        )
        if participants.exists():
            participant = participants.first()
            if participant.status != status:
                print("Found username:", participant.user, participant.guest_user)
                participant.status = status
                participant.save()
            else:
                print(f"Participant is already {status}...")
            return participant
        return None

    async def handle_player_waiting(self, data):
        # If player is waiting, update the status in the database
        # and broadcast a message to all the users in the room using event type "player_waiting"
        username = data["username"]
        RoomConsumer.active_users[self.room_code].add(username)
        participant = await self.update_participant(username, status="waiting")
        if participant:
            print("Participant is waiting...")
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
        RoomConsumer.active_users[self.room_code].add(username)
        participant = await self.update_participant(username, status="ready")
        if participant:
            print("Participant is ready...")
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
            print("Authenticated with token:", token)
            UntypedToken(token)  # Validate token
            user_id = UntypedToken(token).payload["user_id"]
            User = get_user_model()
            return User.objects.get(id=user_id)
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
