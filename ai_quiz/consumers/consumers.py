import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Q
from ai_quiz.consumers.event_handlers import (
    HostStartingGameEventHandler,
    LeaderboardUpdateEventHandler,
    NextQuestionEventHandler,
    PlayerListEventHandler,
    PlayerReadyEventHandler,
    PlayerWaitingEventHandler,
    QuestionAnsweredEventHandler,
    HostEndingGameEventHandler,
    KickPlayerEventHandler,
)
from ai_quiz.models import Participant, Room

logger = logging.getLogger(__name__)


class RoomConsumer(AsyncWebsocketConsumer):
    event_handlers = {
        # This comes from the frontend
        # The event names that the backend sends are in the respective classes
        "player_ready": PlayerReadyEventHandler(),
        "player_waiting": PlayerWaitingEventHandler(),
        "kick_player": KickPlayerEventHandler(),
        "send_next_question": NextQuestionEventHandler(),
        "send_question_answered": QuestionAnsweredEventHandler(),
        "send_leaderboard_update": LeaderboardUpdateEventHandler(),
        "send_all_players": PlayerListEventHandler(),
        "send_host_starting_game": HostStartingGameEventHandler(),
        "send_host_ending_game": HostEndingGameEventHandler(),
    }

    @property
    def username(self):
        return getattr(self, "_username", None)

    @username.setter
    def username(self, value):
        self._username = value

    async def connect(self):
        logger.info(f"Connection request for {self.channel_name}")
        self.room_code = self.scope["url_route"]["kwargs"]["room_code"]
        if not await self.is_room_code_valid():
            await self.close(code=401)
            return
        await self.channel_layer.group_add(self.room_code, self.channel_name)
        await self.accept()
        logger.info(f"Connection established for {self.channel_name}")

    async def disconnect_user(self, username):
        await self.send_data_to_room(
            {
                "type": "player_disconnected",
                "payload": {"username": username},
            }
        )
        participant = await Participant.aget_participant_by_username(
            username=username, room__room_code=self.room_code
        )
        logger.debug(f"username: {username}, room_code: {self.room_code}")
        if participant is None:
            logger.debug(f"Participant not found: {username} while disconnecting.")
        else:
            room = await Room.objects.aget(room_code=self.room_code)
            participant_username = await participant.aparticipant_username
            host_username = await room.ahost_name
            if participant_username == host_username:
                await self.send_data_to_room({"type": "host_ended_game", "payload": {}})
            await participant.adelete()
        await self.send_all_player_names()

    async def disconnect(self, close_code):
        if self.username:
            await self.disconnect_user(self.username)
        await self.channel_layer.group_discard(self.room_code, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data["type"]
        logger.info(f"Received event: {event_type}")
        try:
            # TODO: Currently, players who aren't in the current game can also send
            # events after the game has started. This should be fixed.

            # Handle all events here
            await self.event_handlers[event_type].handle(data, self)
        except KeyError:
            await self.send_error(f"Event type {event_type} not found.")

    async def send_data_to_room(self, data):
        await self.channel_layer.group_send(
            self.room_code, {"type": "room_message", "event": data}
        )

    async def send_data_to_user(self, data):
        await self.channel_layer.send(
            self.channel_name, {"type": "room_message", "event": data}
        )

    async def send_all_player_names(self):
        players = await Participant.aget_all_participants_from_room(
            self.room_code, ~Q(status="inactive")
        )
        await self.send_data_to_room(
            {"type": "all_players", "payload": {"players": players}}
        )

    async def send_error(self, message):
        await self.send_data_to_user({"error": message})

    async def room_message(self, event):
        message = event["event"]
        await self.send(text_data=json.dumps({"message": message}))

    async def is_room_code_valid(self):
        try:
            await Room.objects.aget(room_code=self.room_code)
            return True
        except Room.DoesNotExist:
            return False
