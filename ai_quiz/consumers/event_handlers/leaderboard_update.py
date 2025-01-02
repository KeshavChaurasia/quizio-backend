from typing import TYPE_CHECKING

from ai_quiz.models import Game, Leaderboard

from .base import BaseEventHandler

if TYPE_CHECKING:
    from ai_quiz.consumers.consumers import RoomConsumer


class LeaderboardUpdateEventHandler(BaseEventHandler):
    async def handle(self, event, consumer: "RoomConsumer"):
        game = await Game.aget_current_game_for_room(consumer.room_code)
        try:
            leaderboard = await Leaderboard.objects.aget(game=game)
        except Leaderboard.DoesNotExist:
            await consumer.send_error("Leaderboard not found.")
            return
        await consumer.send_data_to_room(
            {
                "type": "leaderboard_update",
                "payload": [
                    {"username": username, **value}
                    for username, value in leaderboard.data.items()
                ],
            }
        )
