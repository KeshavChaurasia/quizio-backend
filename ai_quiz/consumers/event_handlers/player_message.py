from typing import TYPE_CHECKING

from ai_quiz.models import Game, GameMessage, Participant

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
        game = await Game.aget_current_game_for_room(consumer.room_code)
        if game is None:
            await consumer.send_error("No game found for room")
            return
        game_message: GameMessage = await GameMessage.objects.acreate(
            participant=participant,
            message=message,
            game=game,
        )
        await consumer.send_data_to_room(
            {
                "type": self.event_type,
                "payload": {
                    "message": message,
                    "id": game_message.id,
                    "timestamp": game_message.created_at.timestamp(),
                    "player": {
                        "username": username,
                        "avatarStyle": participant.avatar_style,
                        "avatarSeed": participant.avatar_seed,
                    },
                },
            }
        )
