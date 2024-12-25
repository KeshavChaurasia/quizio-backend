import asyncio
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch
from ai_quiz.models import Game, Participant
from ai_quiz.consumers.event_handlers.player_waiting import PlayerWaitingEventHandler


class TestPlayerWaitingEventHandler(IsolatedAsyncioTestCase):
    def setUp(self):
        self.event_handler = PlayerWaitingEventHandler()
        self.consumer = AsyncMock()
        self.consumer.room_code = "test_room_code"
        self.consumer.username = "test_user"
        self.event = {"payload": {"username": "test_user"}}
        self.event_no_username = {"payload": {}}

    def test_event_name_correct(self):
        self.assertEqual(self.event_handler.event_type, "player_waiting")

    @patch("ai_quiz.models.Game.aget_current_game_for_room")
    @patch("ai_quiz.models.Participant.update_participant_status")
    async def test_handle_success(
        self, mock_update_participant_status, mock_aget_current_game_for_room
    ):
        mock_aget_current_game_for_room.return_value = None
        mock_update_participant_status.return_value = AsyncMock()

        await self.event_handler.handle(self.event, self.consumer)

        self.consumer.send_data_to_room.assert_called_once_with(
            {"type": "player_waiting", "payload": {"username": "test_user"}}
        )
        self.consumer.send_all_player_names.assert_called_once()

    @patch("ai_quiz.models.Game.aget_current_game_for_room")
    async def test_handle_game_in_progress(self, mock_aget_current_game_for_room):
        mock_aget_current_game_for_room.return_value = AsyncMock(status="in_progress")

        await self.event_handler.handle(self.event, self.consumer)

        self.consumer.send_error.assert_called_once_with("Game has already started")

    async def test_handle_no_username(self):
        self.consumer.username = None
        await self.event_handler.handle(self.event_no_username, self.consumer)

        self.consumer.send_error.assert_called_once_with(
            "You need to be ready to wait."
        )

    @patch("ai_quiz.models.Game.aget_current_game_for_room")
    @patch("ai_quiz.models.Participant.update_participant_status")
    async def test_handle_participant_update_failure(
        self, mock_update_participant_status, mock_aget_current_game_for_room
    ):
        mock_aget_current_game_for_room.return_value = None
        mock_update_participant_status.return_value = None

        await self.event_handler.handle(self.event, self.consumer)

        self.consumer.send_data_to_room.assert_not_called()
        self.consumer.send_all_player_names.assert_called_once()
