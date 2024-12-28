from typing import TYPE_CHECKING

from ai_quiz.models import Game
from users.authenticators import aget_authenticated_user

from .base import BaseEventHandler

if TYPE_CHECKING:
    from ai_quiz.consumers.consumers import RoomConsumer


class HostEndingGameEventHandler(BaseEventHandler):
    async def handle(self, event, consumer: "RoomConsumer"):
        token = event.get("payload", {}).get("token")
        if not token:
            await consumer.send_error("No token found.")
            return
        user = await aget_authenticated_user(token)
        if user is None:
            await consumer.send_error("Invalid token.")
            return
        game: Game = await Game.aget_current_game_for_room(consumer.room_code)
        await game.aend_game()
        await consumer.send_data_to_room({"type": "host_ended_game", "payload": {}})
