from unittest.mock import patch

from django.test import TestCase

from ai_quiz.models import (
    Game,
    Leaderboard,
    Participant,
    Question,
    Room,
    Topic,
)
from users.models import GuestUser, User


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


class ParticipantModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
        )
        self.room = Room.objects.create(host=self.user)
        self.guest_user = GuestUser.objects.create(username="guestuser", room=self.room)
        self.participant = Participant.objects.create(
            room=self.room, user=self.user, status="waiting"
        )

    def test_create_participant(self):
        participant = Participant.objects.create(
            room=self.room, user=self.user, status="ready"
        )
        self.assertIsNotNone(participant.id)
        self.assertEqual(participant.room, self.room)
        self.assertEqual(participant.user, self.user)
        self.assertEqual(participant.status, "ready")

    def test_participant_str(self):
        self.assertEqual(
            str(self.participant), f"{self.user.username}:{self.room.room_code}"
        )

    def test_get_participant_by_username(self):
        participant = Participant.get_participant_by_username(
            self.user.username, room=self.room
        )
        self.assertEqual(participant, self.participant)

    def test_get_participant_by_username_guest(self):
        guest_participant = Participant.objects.create(
            room=self.room, guest_user=self.guest_user, status="waiting"
        )
        participant = Participant.get_participant_by_username(
            self.guest_user.username, room=self.room
        )
        self.assertEqual(participant, guest_participant)

    async def test_aget_participant_by_username(self):
        participant = await Participant.aget_participant_by_username(
            self.user.username, room=self.room
        )
        self.assertEqual(participant, self.participant)

    async def test_aget_participant_by_username_guest(self):
        guest_participant = await Participant.objects.acreate(
            room=self.room, guest_user=self.guest_user, status="waiting"
        )
        participant = await Participant.aget_participant_by_username(
            self.guest_user.username, room=self.room
        )
        self.assertEqual(participant, guest_participant)

    async def test_update_participant_status(self):
        updated_participant = await Participant.update_participant_status(
            self.user.username, status="ready", room=self.room
        )
        self.assertEqual(updated_participant.status, "ready")

    def test_get_all_participants_from_room(self):
        participants = Participant.get_all_participants_from_room(self.room.room_code)
        self.assertIn(self.participant.participant_username, participants)

    async def test_aget_all_participants_from_room(self):
        participants = await Participant.aget_all_participants_from_room(
            self.room.room_code
        )
        self.assertIn(self.participant.participant_username, participants)


class LeaderboardModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.room = Room.objects.create(host=self.user)
        self.game = Game.objects.create(room=self.room, status="waiting")
        self.leaderboard = Leaderboard.objects.create(
            game=self.game, data={"testuser": 10}
        )

    def test_create_leaderboard(self):
        self.assertIsNotNone(self.leaderboard.id)
        self.assertEqual(self.leaderboard.game, self.game)
        self.assertEqual(self.leaderboard.data, {"testuser": 10})

    def test_leaderboard_str(self):
        self.assertEqual(str(self.leaderboard), f"Leaderboard: {self.room.room_code}")


class TopicModelTest(TestCase):
    def setUp(self):
        self.topic = Topic.objects.create(
            name="Science", subtopics=["Physics", "Chemistry"]
        )

    def test_create_topic(self):
        self.assertIsNotNone(self.topic.id)
        self.assertEqual(self.topic.name, "Science")
        self.assertEqual(self.topic.subtopics, ["Physics", "Chemistry"])

    def test_topic_str(self):
        self.assertEqual(str(self.topic), "Science")


class QuestionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.room = Room.objects.create(host=self.user)
        self.game = Game.objects.create(room=self.room, status="waiting")
        self.topic = Topic.objects.create(
            name="Science", subtopics=["Physics", "Chemistry"]
        )
        self.question = Question.objects.create(
            game=self.game,
            question="What is the capital of France?",
            subtopic="Geography",
            topic=self.topic,
            options=["Paris", "London", "Berlin", "Madrid"],
            difficulty="easy",
            correct_answer="Paris",
            timer=30,
        )

    def test_create_question(self):
        self.assertIsNotNone(self.question.id)
        self.assertEqual(self.question.game, self.game)
        self.assertEqual(self.question.question, "What is the capital of France?")
        self.assertEqual(self.question.subtopic, "Geography")
        self.assertEqual(self.question.topic, self.topic)
        self.assertEqual(self.question.options, ["Paris", "London", "Berlin", "Madrid"])
        self.assertEqual(self.question.difficulty, "easy")
        self.assertEqual(self.question.correct_answer, "Paris")
        self.assertEqual(self.question.timer, 30)

    def test_question_str(self):
        self.assertEqual(
            str(self.question), f"Q{self.question.id} - What is the capital of France?"
        )

    def test_get_all_questions_from_game(self):
        questions, len_questions = Question.get_all_questions_from_game(self.game)
        self.assertEqual(len_questions, 1)
        self.assertIn(self.question, questions)

    async def test_aget_all_questions_from_game(self):
        questions, len_questions = await Question.aget_all_questions_from_game(
            self.game
        )
        self.assertEqual(len_questions, 1)
        self.assertIn(self.question, questions)
