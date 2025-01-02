from django.urls import path
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
    CheckRoomValidView,
)

urlpatterns = [
    path("rooms/create/", CreateRoomView.as_view(), name="create_room"),
    path("rooms/valid/", CheckRoomValidView.as_view(), name="check_room_valid"),
    path("rooms/join/", JoinRoomView.as_view(), name="join_room"),
    path("rooms/end/", EndRoomView.as_view(), name="end_room"),
    path("game/create/", CreateGameView.as_view(), name="create_game"),
    path("game/start/", StartGameView.as_view(), name="start_game"),
    path("game/end/", EndGameView.as_view(), name="end_game"),
    path("topic/", SubtopicsAPIView.as_view(), name="generate_subtopics"),
    path(
        "single-player/start",
        StartSinglePlayerGameAPIView.as_view(),
        name="start_single_player_game",
    ),
    path(
        "single-player/question",
        QuestionsAPIView.as_view(),
        name="next_single_player_question",
    ),
    path(
        "single-player/answer",
        CheckAnswerAPIView.as_view(),
        name="check_single_player_answer",
    ),
]
