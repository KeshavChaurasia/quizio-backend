from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch
from ai_quiz.models import Question
from ai_quiz.consumers.event_handlers.question_answered import (
    QuestionAnsweredEventHandler,
)


class TestQuestionAnsweredEventHandler(IsolatedAsyncioTestCase):
    def setUp(self):
        self.event_handler = QuestionAnsweredEventHandler()
        self.consumer = AsyncMock()
        self.consumer.room_code = "test_room_code"
        self.consumer.username = "test_user"
        self.event = {"questionId": 1, "answer": "correct_answer"}
        self.event_no_username = {"questionId": 1, "answer": "correct_answer"}
        self.event_no_question_id = {"answer": "correct_answer"}
        self.event_no_answer = {"questionId": 1}

    def test_event_name_correct(self):
        self.assertEqual(self.event_handler.event_type, "question_answered")

    @patch("ai_quiz.models.Game.aget_current_game_for_room")
    @patch("ai_quiz.models.Participant.aget_participant_by_username")
    @patch("ai_quiz.models.Leaderboard.objects.aget_or_create", new_callable=AsyncMock)
    async def test_handle_success(
        self,
        mock_leaderboard_get_or_create,
        mock_participant_get,
        mock_game_get,
    ):
        mock_participant_get.return_value = AsyncMock(correct_answers=0, score=0)
        mock_leaderboard_get_or_create.return_value = (
            AsyncMock(data={"test_user": 0}),
            True,
        )

        mock_game = MagicMock()
        mock_game.questions.aget = AsyncMock(
            return_value=Question(correct_answer="correct_answer")
        )
        mock_game_get.return_value = mock_game
        await self.event_handler.handle({"payload": {**self.event}}, self.consumer)

        self.consumer.send_data_to_user.assert_any_call(
            {
                "type": "answer_validation",
                "payload": {"answer": "correct_answer", "isCorrect": True},
            }
        )
        self.consumer.send_data_to_room.assert_called_once_with(
            {
                "type": "leaderboard_update",
                "payload": [{"username": "test_user", "score": 1}],
            }
        )

    @patch("ai_quiz.models.Game.aget_current_game_for_room")
    async def test_handle_invalid_question_id(self, mock_game_get):
        mock_game_get.return_value = AsyncMock()
        mock_game = MagicMock()
        mock_game.questions = MagicMock()
        mock_game.questions.aget = AsyncMock(side_effect=Question.DoesNotExist)
        mock_game_get.return_value = mock_game
        await self.event_handler.handle({"payload": {**self.event}}, self.consumer)

        self.consumer.send_error.assert_called_once_with("Invalid question id: 1")

    async def test_handle_no_username(self):
        self.consumer.username = None
        await self.event_handler.handle(self.event_no_username, self.consumer)

        self.consumer.send_error.assert_called_once_with("Username is required.")

    async def test_handle_no_question_id(self):
        await self.event_handler.handle(self.event_no_question_id, self.consumer)

        self.consumer.send_data_to_user.assert_called_once_with(
            {"error": "questionId and answer are required."}
        )

    async def test_handle_no_answer(self):
        await self.event_handler.handle(self.event_no_answer, self.consumer)

        self.consumer.send_data_to_user.assert_called_once_with(
            {"error": "questionId and answer are required."}
        )

    @patch("ai_quiz.models.Game.aget_current_game_for_room")
    @patch("ai_quiz.models.Participant.aget_participant_by_username")
    @patch("ai_quiz.models.Leaderboard.objects.aget_or_create", new_callable=AsyncMock)
    async def test_handle_incorrect_answer(
        self,
        mock_leaderboard_get_or_create,
        mock_participant_get,
        mock_game_get,
    ):
        mock_game_get.return_value = AsyncMock()
        mock_participant_get.return_value = AsyncMock(wrong_answers=0)
        mock_leaderboard_get_or_create.return_value = (AsyncMock(data={}), True)

        mock_game = MagicMock()
        mock_game.questions.aget = AsyncMock(
            return_value=Question(correct_answer="correct_answer")
        )
        mock_game_get.return_value = mock_game

        await self.event_handler.handle(
            {"payload": {"questionId": 1, "answer": "wrong_answer"}}, self.consumer
        )

        self.consumer.send_data_to_user.assert_any_call(
            {
                "type": "answer_validation",
                "payload": {"answer": "wrong_answer", "isCorrect": False},
            }
        )
