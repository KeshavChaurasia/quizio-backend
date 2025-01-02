import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.core.cache import cache  # Using Redis as a cache

from ai_quiz.models import Game, Participant

from .base import BaseEventHandler

if TYPE_CHECKING:
    from ai_quiz.consumers.consumers import RoomConsumer

logger = logging.getLogger(__name__)


@dataclass
class PlayerReadyEventHandler(BaseEventHandler):
    event_type: str = "player_ready"

    async def handle(self, event: dict, consumer: "RoomConsumer"):
        username = event.get("payload", {}).get("username")
        if username is None:
            logger.info(
                f"Cannot set player as ready. Username is required. payload: {event.get('payload')}"
            )
            await consumer.send_error("username is required")
            return

        consumer.username = username
        await cache.aset(f"user_channel_{username}", consumer.channel_name)
        game = await Game.aget_current_game_for_room(consumer.room_code)
        if game and game.status == "in_progress":
            await consumer.send_error("Game has already started")
            return
        participant = await Participant.update_participant_status(
            username, status="ready", room__room_code=consumer.room_code
        )
        if participant:
            logger.debug(f"Player {username} is ready")
            await consumer.send_data_to_room(
                {
                    "type": self.event_type,
                    "payload": {
                        "player": {
                            "username": await participant.aparticipant_username,
                            "avatarStyle": participant.avatar_style,
                            "avatarSeed": participant.avatar_seed,
                        }
                    },
                }
            )
        else:
            await consumer.send_error(
                f"Participant with username: {username} not found"
            )
            return
        await consumer.send_all_player_names()
