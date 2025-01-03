from typing import TYPE_CHECKING

from ai_quiz.models import Participant

from .base import BaseEventHandler

if TYPE_CHECKING:
    from ai_quiz.consumers.consumers import RoomConsumer


class PlayerMessageEventHandler(BaseEventHandler):
    event_type: str = "player_message"

    async def handle(self, event, consumer: "RoomConsumer"):
        payload = event.get("payload", {})
        message = payload.get("message")
        username = payload.get("username")
        participant = await Participant.aget_participant_by_username(
            username, room__room_code=consumer.room_code
        )
        if participant is None:
            await consumer.send_error(f"Participant not found for username: {username}")
            return
        await consumer.send_data_to_room(
            {
                "type": self.event_type,
                "payload": {
                    "message": message,
                    "player": {
                        "username": username,
                        "avatarStyle": participant.avatar_style,
                        "avatarSeed": participant.avatar_seed,
                    },
                },
            }
        )
