from django.test import TestCase
from django.utils import timezone
from ai_quiz.models import Room, Game
from users.models import User


class RoomModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
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
