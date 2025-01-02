import logging
from typing import TYPE_CHECKING

from users.authenticators import aget_authenticated_user

from .base import BaseEventHandler

if TYPE_CHECKING:
    from ai_quiz.consumers.consumers import RoomConsumer

logger = logging.getLogger(__name__)


class KickPlayerEventHandler(BaseEventHandler):
    async def handle(self, event, consumer: "RoomConsumer"):
        logger.info("Kicking player...")
        token = event.get("payload", {}).get("token")
        if not token:
            await consumer.send_error("No token found.")
            return
        user = await aget_authenticated_user(token)
        if user is None:
            await consumer.send_error("Invalid token.")
            return
        username = event.get("payload", {}).get("username")
        await consumer.disconnect_user(username)
        await consumer.send_all_player_names()
