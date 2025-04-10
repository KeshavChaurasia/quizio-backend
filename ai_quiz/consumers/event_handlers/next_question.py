from typing import TYPE_CHECKING

from ai_quiz.models import Game
from ai_quiz.serializers import QuestionSerializer
from users.authenticators import aget_authenticated_user

from .base import BaseEventHandler

if TYPE_CHECKING:
    from ai_quiz.consumers.consumers import RoomConsumer


class NextQuestionEventHandler(BaseEventHandler):
    event_type: str = "next_question"

    async def get_next_question(self, room_code: str):
        game: Game = await Game.aget_current_game_for_room(room_code)
        if not game:
            raise ValueError("No game found for the room.")
        game.status = "in_progress"
        await game.asave()

        new_question, is_last_question = await game.aget_next_question()
        return new_question, is_last_question

    async def handle(self, event: dict, consumer: "RoomConsumer"):
        token = event.get("payload", {}).get("token")
        if not token:
            await consumer.send_error("No token found.")
            return
        user = await aget_authenticated_user(token)
        if user is None:
            await consumer.send_error("Invalid token.")
            return

        await consumer.send_data_to_user({"success": "Authenticated."})

        try:
            question, is_last_question = await self.get_next_question(
                consumer.room_code
            )
            if question is not None:
                question_serializer = QuestionSerializer(question)
                await consumer.send_data_to_room(
                    {
                        "type": self.event_type,
                        "payload": {
                            **question_serializer.data,
                            "is_last_question": is_last_question,
                        },
                    }
                )
            else:
                await consumer.send_data_to_room({"type": "all_questions_done"})
        except ValueError as e:
            await consumer.send_error(str(e))
