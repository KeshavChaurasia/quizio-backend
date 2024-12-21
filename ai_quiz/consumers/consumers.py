import json

from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Q

from ai_quiz.consumers.event_handlers import (
    NextQuestionEventHandler,
    PlayerReadyEventHandler,
    PlayerWaitingEventHandler,
    QuestionAnsweredEventHandler,
)
from ai_quiz.models import Participant


class RoomConsumer(AsyncWebsocketConsumer):
    event_handlers = {
        "player_ready": PlayerReadyEventHandler(),
        "player_waiting": PlayerWaitingEventHandler(),
        "next_question": NextQuestionEventHandler(),
        "question_answered": QuestionAnsweredEventHandler(),
    }

    @property
    def username(self):
        return getattr(self, "_username", None)

    @username.setter
    def username(self, value):
        self._username = value

    async def connect(self):
        self.room_code = self.scope["url_route"]["kwargs"]["room_code"]

        await self.channel_layer.group_add(self.room_code, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if self.username:
            await self.send_data_to_room(
                {"type": "player_disconnected", "username": self.username}
            )
            await Participant.update_participant_status(
                username=self.username,
                status="inactive",
                room__room_code=self.room_code,
            )
            await self.send_all_player_names()
        await self.channel_layer.group_discard(self.room_code, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data["type"]
        try:
            # Handle all events here
            await self.event_handlers[event_type].handle(data, self)
        except KeyError:
            raise ValueError(f"Invalid event type: {event_type}")

    async def send_data_to_room(self, data):
        await self.channel_layer.group_send(
            self.room_code, {"type": "room_message", "event": data}
        )

    async def send_data_to_user(self, data):
        await self.channel_layer.send(
            self.channel_name, {"type": "room_message", "event": data}
        )

    async def send_all_player_names(self):
        usernames = await Participant.aget_all_participants_from_room(
            self.room_code, ~Q(status="inactive")
        )
        await self.send_data_to_room({"type": "all_players", "usernames": usernames})

    async def send_error(self, message):
        await self.send_data_to_user({"error": message})

    async def room_message(self, event):
        message = event["event"]
        await self.send(text_data=json.dumps({"message": message}))
