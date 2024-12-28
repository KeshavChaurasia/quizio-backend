from typing import TYPE_CHECKING

from ai_quiz.models import Participant

from .base import BaseEventHandler

if TYPE_CHECKING:
    from ai_quiz.consumers.consumers import RoomConsumer


class PlayerListEventHandler(BaseEventHandler):
    async def handle(self, event, consumer: "RoomConsumer"):
        participants = await Participant.aget_all_participants_from_room(
            consumer.room_code
        )
        await consumer.send_data_to_room(
            {
                "type": "all_players",
                "payload": {"usernames": participants},
            }
        )
