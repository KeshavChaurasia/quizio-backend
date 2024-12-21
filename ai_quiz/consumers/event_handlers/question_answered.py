from .base import BaseEventHandler


class QuestionAnsweredEventHandler(BaseEventHandler):
    @staticmethod
    async def handle(event: dict, consumer):
        pass
