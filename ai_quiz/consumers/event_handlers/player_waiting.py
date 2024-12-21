from typing import TYPE_CHECKING

from ai_quiz.models import Participant

from .base import BaseEventHandler

if TYPE_CHECKING:
    from ai_quiz.consumers.consumers import RoomConsumer


class PlayerWaitingEventHandler(BaseEventHandler):
    event_type: str = "player_waiting"

    async def handle(self, event: dict, consumer: "RoomConsumer"):
        # If player is waiting, update the status in the database
        # and broadcast a message to all the users in the room using event type "player_waiting"
        # TODO: Add a check to see if the game has started. If yes, refuse to let the player wait
        username = consumer.username
        if not username:
            await consumer.send_error("You need to be ready to wait.")
            return

        participant = await Participant.update_participant_status(
            username, status="waiting", room__room_code=consumer.room_code
        )
        if participant:
            await consumer.send_data_to_room(
                {"type": self.event_type, "username": username}
            )
        await consumer.send_all_player_names()
