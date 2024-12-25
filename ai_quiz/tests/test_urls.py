from django.test import SimpleTestCase
from django.urls import reverse, resolve
from ai_quiz.views import (
    EndRoomView,
    CreateGameView,
    CreateRoomView,
    JoinRoomView,
    StartGameView,
    EndGameView,
    SubtopicsAPIView,
    StartSinglePlayerGameAPIView,
    QuestionsAPIView,
    CheckAnswerAPIView,
)


class TestUrls(SimpleTestCase):
    def test_create_room_url(self):
        url = reverse("create_room")
        self.assertEqual(resolve(url).func.view_class, CreateRoomView)

    def test_join_room_url(self):
        url = reverse("join_room")
        self.assertEqual(resolve(url).func.view_class, JoinRoomView)

    def test_end_room_url(self):
        url = reverse("end_room")
        self.assertEqual(resolve(url).func.view_class, EndRoomView)

    def test_create_game_url(self):
        url = reverse("create_game")
        self.assertEqual(resolve(url).func.view_class, CreateGameView)

    def test_start_game_url(self):
        url = reverse("start_game")
        self.assertEqual(resolve(url).func.view_class, StartGameView)

    def test_end_game_url(self):
        url = reverse("end_game")
        self.assertEqual(resolve(url).func.view_class, EndGameView)

    def test_generate_subtopics_url(self):
        url = reverse("generate_subtopics")
        self.assertEqual(resolve(url).func.view_class, SubtopicsAPIView)

    def test_start_single_player_game_url(self):
        url = reverse("start_single_player_game")
        self.assertEqual(resolve(url).func.view_class, StartSinglePlayerGameAPIView)

    def test_next_single_player_question_url(self):
        url = reverse("next_single_player_question")
        self.assertEqual(resolve(url).func.view_class, QuestionsAPIView)

    def test_check_single_player_answer_url(self):
        url = reverse("check_single_player_answer")
        self.assertEqual(resolve(url).func.view_class, CheckAnswerAPIView)
