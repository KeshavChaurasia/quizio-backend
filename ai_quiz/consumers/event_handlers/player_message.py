from typing import TYPE_CHECKING

from .base import BaseEventHandler

if TYPE_CHECKING:
    from ai_quiz.consumers.consumers import RoomConsumer


class PlayerMessageEventHandler(BaseEventHandler):
    event_type: str = "player_message"

    async def handle(self, event, consumer: "RoomConsumer"):
        payload = event.get("payload", {})
        message = payload.get("message")
        username = payload.get("username")
        await consumer.send_data_to_room(
            {
                "type": self.event_type,
                "payload": {"message": message, "username": username},
            }
        )
