import logging
from typing import TYPE_CHECKING

from ai_quiz.consumers.event_handlers.leaderboard_update import (
    LeaderboardUpdateEventHandler,
)
from ai_quiz.models import Game, Leaderboard, Participant, Question

from .base import BaseEventHandler

if TYPE_CHECKING:
    from ai_quiz.consumers.consumers import RoomConsumer

logger = logging.getLogger(__name__)


class QuestionAnsweredEventHandler(BaseEventHandler):
    event_type: str = "question_answered"

    async def send_answer_validation_event(
        self,
        consumer: "RoomConsumer",
        answer: str,
        correct_answer: str,
        is_correct: bool,
    ):
        return await consumer.send_data_to_user(
            {
                "type": "answer_validation",
                "payload": {
                    "isCorrect": is_correct,
                    "correctAnswer": correct_answer,
                    "submittedAnswer": answer,
                },
            }
        )

    # TODO: Send all_players_answered event to the host
    async def _handle_leaderboard_update(
        self,
        answer: str,
        consumer: "RoomConsumer",
        current_question: Question,
        leaderboard: Leaderboard,
        timestamp: int,
    ):
        username = consumer.username
        user_data = leaderboard.data.get(username)
        is_correct = False

        if not answer:
            # User skipped the question means the answer field will be null
            user_data["skipped_questions"] = user_data.get("skipped_questions", 0) + 1
        elif current_question.correct_answer == answer:
            # User answered correctly
            user_data["correct_answers"] = user_data.get("correct_answers", 0) + 1
            # Calculate score based on timestamp
            response_time = max(
                0, timestamp / 1000 - current_question.updated_at.timestamp()
            )

            user_data["score"] = user_data.get("score", 0) + int(
                max(
                    0,  # Min score
                    100  # Max score
                    * (1 - (response_time / current_question.time_per_question)),
                )
            )
            # IMPORTANT: Set is_correct to True
            is_correct = True
        else:
            # User answered incorrectly
            user_data["wrong_answers"] = user_data.get("wrong_answers", 0) + 1
        await leaderboard.asave()
        await self.send_answer_validation_event(
            consumer=consumer,
            answer=answer,
            correct_answer=current_question.correct_answer,
            is_correct=is_correct,
        )

    async def handle(self, data, consumer: "RoomConsumer"):
        username = consumer.username
        if not username:
            await consumer.send_error("Username is required.")
            return
        payload = data.get("payload", {})
        question_id = payload.get("questionId")
        answer = payload.get("submittedAnswer")
        timestamp = payload.get("timestamp")
        if not question_id or not timestamp:
            await consumer.send_data_to_user(
                {"error": "questionId and timestamp are required."}
            )
            return

        try:
            game = await Game.aget_current_game_for_room(consumer.room_code)
            if not game:
                await consumer.send_error("No game found for the room.")
                return
            current_question = await game.questions.aget(id=question_id)
        except Question.DoesNotExist:
            await consumer.send_error(f"Invalid question id: {question_id}")
            return

        participant: Participant = await Participant.aget_participant_by_username(
            username=username, room__room_code=consumer.room_code
        )
        if not participant:
            await consumer.send_error("Participant not found.")
            return
        leaderboard, _ = await Leaderboard.objects.aget_or_create(game=game)

        await self._handle_leaderboard_update(
            answer=answer,
            consumer=consumer,
            current_question=current_question,
            leaderboard=leaderboard,
            timestamp=timestamp,
        )

        await LeaderboardUpdateEventHandler().send_leaderboard_update(
            leaderboard=leaderboard, consumer=consumer
        )
