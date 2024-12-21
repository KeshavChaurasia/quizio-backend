from dataclasses import dataclass
from .base import BaseEventHandler
from ai_quiz.models import Participant
from django.db.models import Q


@dataclass
class PlayerReadyEventHandler(BaseEventHandler):
    event_type: str = "player_ready"

    async def update_participant_status(self, username, status="ready"):
        participant = await Participant.aget_participant_by_username(
            username, room__room_code=self.room_code
        )
        if participant is not None and participant.status != status:
            participant.status = status
            await participant.asave()
            return participant
        return None

    async def handle(self, event: dict):
        # TODO: Add a check to see if the game has started. If yes, refuse to let the player get ready
        username = event.get("username")
        if username is None:
            await self.send_error("username is required")
            return

        self.username = username

        participant = await self.update_participant_status(username, status="ready")
        if participant:
            await self.send_data_to_room({"type": "player_ready", "username": username})
        await self.consumer.send_all_player_names()
