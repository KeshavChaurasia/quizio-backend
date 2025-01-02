from typing import TYPE_CHECKING


from .base import BaseEventHandler

if TYPE_CHECKING:
    from ai_quiz.consumers.consumers import RoomConsumer


class PlayerListEventHandler(BaseEventHandler):
    async def handle(self, event, consumer: "RoomConsumer"):
        await consumer.send_all_player_names()
