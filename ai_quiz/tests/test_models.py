from unittest.mock import patch
from django.test import TestCase

from ai_quiz.models import Game, Question, Room
from users.models import User


class RoomModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
        )

    def test_create_room(self):
        room = Room.objects.create(host=self.user)
        self.assertIsNotNone(room.room_id)
        self.assertEqual(room.host, self.user)
        self.assertEqual(room.status, "waiting")
        self.assertIsNotNone(room.room_code)
        self.assertEqual(len(room.room_code), 8)

    def test_generate_unique_room_code(self):
        room1 = Room.objects.create(host=self.user)
        room2 = Room.objects.create(host=self.user)
        self.assertNotEqual(room1.room_code, room2.room_code)

    def test_room_str(self):
        room = Room.objects.create(host=self.user)
        self.assertEqual(str(room), f"Room {room.room_code} - {room.status}")

    def test_get_current_game(self):
        room = Room.objects.create(host=self.user)
        game = Game.objects.create(room=room, status="waiting")
        current_game = room.get_current_game()
        self.assertEqual(current_game, game)

    def test_get_current_game_no_game(self):
        room = Room.objects.create(host=self.user)
        with self.assertRaises(ValueError):
            room.get_current_game()

    def test_end_game(self):
        room = Room.objects.create(host=self.user)
        game = Game.objects.create(room=room, status="in_progress")
        ended_game = room.end_game()
        self.assertEqual(ended_game.status, "finished")
        self.assertIsNotNone(ended_game.ended_at)

    def test_end_game_no_in_progress_game(self):
        room = Room.objects.create(host=self.user)
        with self.assertRaises(ValueError):
            room.end_game()


class GameModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
        )
        self.room = Room.objects.create(host=self.user)

    def test_create_game(self):
        game = Game.objects.create(room=self.room, status="waiting")
        self.assertIsNotNone(game.id)
        self.assertEqual(game.room, self.room)
        self.assertEqual(game.status, "waiting")
        self.assertIsNone(game.started_at)
        self.assertIsNone(game.ended_at)
        self.assertEqual(game.current_question, 0)

    def test_game_str(self):
        game = Game.objects.create(room=self.room, status="waiting")
        self.assertEqual(str(game), f"{game.id}-waiting")

    def test_create_leaderboard(self):
        game = Game.objects.create(room=self.room, status="waiting")
        leaderboard = game.create_leaderboard()
        self.assertIsNotNone(leaderboard)

    def test_get_next_question(self):
        game = Game.objects.create(room=self.room, status="waiting")
        question = game.questions.create(
            question="What is the capital of France?",
            correct_answer="Paris",
            options=["Paris", "London", "Berlin", "Madrid"],
        )
        next_question = game.get_next_question()
        self.assertEqual(next_question, question)
        self.assertEqual(game.current_question, 1)

    def test_get_next_question_end_game(self):
        game = Game.objects.create(room=self.room, status="waiting")
        game.questions.create(
            question="What is the capital of France?",
            correct_answer="Paris",
            options=["Paris", "London", "Berlin", "Madrid"],
        )
        game.current_question = 1
        next_question = game.get_next_question()
        self.assertIsNone(next_question)
        self.assertEqual(game.status, "finished")
        self.assertIsNotNone(game.ended_at)

    def test_end_game(self):
        game = Game.objects.create(room=self.room, status="in_progress")
        game.end_game()
        self.assertEqual(game.status, "finished")
        self.assertIsNotNone(game.ended_at)

    async def test_aend_game(self):
        game = await Game.objects.acreate(room=self.room, status="in_progress")
        await game.aend_game()
        self.assertEqual(game.status, "finished")
        self.assertIsNotNone(game.ended_at)

    async def test_aget_next_question(self):
        game = await Game.objects.acreate(room=self.room, status="waiting")
        question = await Question.objects.acreate(
            question="What is the capital of France?",
            correct_answer="Paris",
            options=["Paris", "London", "Berlin", "Madrid"],
            game=game,
        )

        next_question = await game.aget_next_question()
        self.assertEqual(next_question, question)
        self.assertEqual(game.current_question, 1)

    async def test_aget_next_question_no_questions(self):
        game = await Game.objects.acreate(room=self.room, status="waiting")

        question = await game.aget_next_question()
        self.assertEqual(question, None)
        self.assertEqual(game.current_question, 0)

    def test_get_current_game_for_room(self):
        game = Game.objects.create(room=self.room, status="in_progress")
        current_game = Game.get_current_game_for_room(self.room.room_code)
        self.assertEqual(current_game, game)

    async def test_aget_current_game_for_room(self):
        game = await Game.objects.acreate(room=self.room, status="in_progress")
        current_game = await Game.aget_current_game_for_room(self.room.room_code)
        self.assertEqual(current_game, game)
