from typing import TYPE_CHECKING

from ai_quiz.models import Game, Participant

from .base import BaseEventHandler

if TYPE_CHECKING:
    from ai_quiz.consumers.consumers import RoomConsumer


class PlayerWaitingEventHandler(BaseEventHandler):
    event_type: str = "player_waiting"

    async def handle(self, event: dict, consumer: "RoomConsumer"):
        # If player is waiting, update the status in the database
        # and broadcast a message to all the users in the room using event type "player_waiting"
        username = consumer.username
        if not username:
            await consumer.send_error("You need to be ready to wait.")
            return

        game = await Game.aget_current_game_for_room(consumer.room_code)
        if game and game.status == "in_progress":
            await consumer.send_error("Game has already started")
            return

        participant = await Participant.update_participant_status(
            username, status="waiting", room__room_code=consumer.room_code
        )
        if participant:
            await consumer.send_data_to_room(
                {"type": self.event_type, "payload": {"username": username}}
            )
        await consumer.send_all_player_names()
