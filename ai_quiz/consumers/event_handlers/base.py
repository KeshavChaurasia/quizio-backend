from abc import ABC, abstractmethod
from dataclasses import field, dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_quiz.consumers.consumers import RoomConsumer


@dataclass
class BaseEventHandler(ABC):
    consumer: "RoomConsumer"
    event_type: str = field(init=False)

    @abstractmethod
    async def handle(self, event: dict):
        pass

    async def send_error(self, message):
        await self.consumer.send_error(message)

    async def send_data_to_room(self, data):
        await self.consumer.send_data_to_room({"type": self.event_type, **data})

    async def send_data_to_user(self, data):
        await self.consumer.send_data_to_user(data)

    @property
    def room_code(self):
        return self.consumer.room_code

    @property
    def username(self):
        return self.consumer.username

    @username.setter
    def username(self, value):
        self.consumer.username = value
