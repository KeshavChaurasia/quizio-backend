from abc import ABC, abstractmethod
from dataclasses import field, dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_quiz.consumers.consumers import RoomConsumer


@dataclass
class BaseEventHandler(ABC):
    event_type: str = field(init=False)

    @abstractmethod
    async def handle(self, event: dict, consumer: "RoomConsumer"):
        pass
