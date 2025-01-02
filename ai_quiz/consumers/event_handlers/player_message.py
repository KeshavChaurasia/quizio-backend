from typing import TYPE_CHECKING

from .base import BaseEventHandler

if TYPE_CHECKING:
    from ai_quiz.consumers.consumers import RoomConsumer


class PlayerMessageEventHandler(BaseEventHandler):
    async def handle(self, event, consumer: "RoomConsumer"):
        payload = event.get("payload", {})
        message = payload.get("message")
        username = payload.get("username")
        await consumer.send_data_to_room(
            {
                "type": "player_message",
                "payload": {"message": message, "username": username},
            }
        )
