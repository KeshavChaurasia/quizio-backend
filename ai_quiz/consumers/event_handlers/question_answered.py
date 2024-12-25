from typing import TYPE_CHECKING

from ai_quiz.models import Game, Leaderboard, Participant, Question

from .base import BaseEventHandler

if TYPE_CHECKING:
    from ai_quiz.consumers.consumers import RoomConsumer


class QuestionAnsweredEventHandler(BaseEventHandler):
    event_type: str = "question_answered"

    async def handle(self, data, consumer: "RoomConsumer"):
        username = consumer.username
        if not username:
            await consumer.send_error("Username is required.")
            return
        question_id = data.get("payload", {}).get("questionId")
        answer = data.get("payload", {}).get("answer")
        if not question_id or not answer:
            await consumer.send_data_to_user(
                {"error": "questionId and answer are required."}
            )
            return

        try:
            game = await Game.aget_current_game_for_room(consumer.room_code)
            current_question = await game.questions.aget(id=question_id)
        except Question.DoesNotExist:
            await consumer.send_error(f"Invalid question id: {question_id}")
            return

        participant = await Participant.aget_participant_by_username(
            username=username, room__room_code=consumer.room_code
        )
        leaderboard, _ = await Leaderboard.objects.aget_or_create(game=game)

        if current_question.correct_answer == answer:
            # TODO: Separate out the participant correct answers and wrong answers variables to leaderboard
            participant.correct_answers += 1
            participant.score += 1  # TODO: Update the score based on the timestamp
            leaderboard.data[username] = participant.score

            await consumer.send_data_to_user(
                {
                    "type": "answer_validation",
                    "event": {"answer": answer, "isCorrect": True},
                }
            )
        else:
            participant.wrong_answers += 1
            await consumer.send_data_to_user(
                {
                    "type": "answer_validation",
                    "event": {"answer": answer, "isCorrect": False},
                }
            )
        await consumer.send_data_to_room(
            {
                "type": "leaderboard_update",
                "data": leaderboard.data,
            }
        )
        await participant.asave()
        await leaderboard.asave()
