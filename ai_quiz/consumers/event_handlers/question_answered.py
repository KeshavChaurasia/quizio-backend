from typing import TYPE_CHECKING

from ai_quiz.models import Game, Leaderboard, Participant, Question

from .base import BaseEventHandler

if TYPE_CHECKING:
    from ai_quiz.consumers.consumers import RoomConsumer


class QuestionAnsweredEventHandler(BaseEventHandler):
    event_type: str = "question_answered"

    async def handle(self, data, consumer: "RoomConsumer"):
        # TODO: Currently, the frontend can send many answers for the same question. We need to handle this.
        username = consumer.username
        if not username:
            await consumer.send_error("Username is required.")
            return
        question_id = data.get("payload", {}).get("questionId")
        answer = data.get("payload", {}).get("submittedAnswer")
        if not question_id:
            await consumer.send_data_to_user({"error": "questionId is required."})
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
        if not answer:
            participant.skipped_questions += 1
            await consumer.send_data_to_user(
                {
                    "type": "answer_validation",
                    "payload": {
                        "submittedAnswer": answer,
                        "isCorrect": False,
                        "correctAnswer": current_question.correct_answer,
                    },
                }
            )
        elif current_question.correct_answer == answer:
            # TODO: Separate out the participant correct answers and wrong answers variables to leaderboard
            participant.correct_answers += 1
            participant.score += 1  # TODO: Update the score based on the timestamp
            leaderboard.data[username] = participant.score

            await consumer.send_data_to_user(
                {
                    "type": "answer_validation",
                    "payload": {
                        "submittedAnswer": answer,
                        "isCorrect": True,
                        "correctAnswer": current_question.correct_answer,
                    },
                }
            )
        else:
            participant.wrong_answers += 1
            await consumer.send_data_to_user(
                {
                    "type": "answer_validation",
                    "payload": {
                        "submittedAnswer": answer,
                        "isCorrect": False,
                        "correctAnswer": current_question.correct_answer,
                    },
                }
            )
        await consumer.send_data_to_room(
            {
                "type": "leaderboard_update",
                "payload": [
                    {"username": d, "score": leaderboard.data[d]}
                    for d in leaderboard.data
                ],
            }
        )
        await participant.asave()
        await leaderboard.asave()
