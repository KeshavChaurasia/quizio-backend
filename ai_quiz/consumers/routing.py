from django.urls import re_path
from ai_quiz.consumers import consumers

websocket_urlpatterns = [
    re_path(r"ws/room/(?P<room_code>\w+)/$", consumers.RoomConsumer.as_asgi()),
]
