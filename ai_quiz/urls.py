from django.urls import path
from ai_quiz.views import CreateRoomView, JoinRoomView, StartGameView, EndGameView

urlpatterns = [
    path("rooms/create", CreateRoomView.as_view(), name="create_room"),
    path("rooms/join", JoinRoomView.as_view(), name="join_room"),
    path("game/start", StartGameView.as_view(), name="start_game"),
    path("game/end", EndGameView.as_view(), name="end_game"),
]
