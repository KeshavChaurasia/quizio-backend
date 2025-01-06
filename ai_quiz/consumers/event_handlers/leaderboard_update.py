from typing import TYPE_CHECKING

from ai_quiz.models import Game, Leaderboard

from .base import BaseEventHandler

if TYPE_CHECKING:
    from ai_quiz.consumers.consumers import RoomConsumer


class LeaderboardUpdateEventHandler(BaseEventHandler):
    event_type: str = "leaderboard_update"

    async def send_leaderboard_update(self, leaderboard, consumer: "RoomConsumer"):
        return await consumer.send_data_to_room(
            {
                "type": self.event_type,
                "payload": [
                    {"username": username, **value}
                    for username, value in leaderboard.data.items()
                ],
            }
        )

    async def handle(self, event, consumer: "RoomConsumer"):
        game = await Game.aget_current_game_for_room(consumer.room_code)
        try:
            leaderboard = await Leaderboard.objects.aget(game=game)
        except Leaderboard.DoesNotExist:
            await consumer.send_error("Leaderboard not found.")
            return
        await self.send_leaderboard_update(leaderboard, consumer)
