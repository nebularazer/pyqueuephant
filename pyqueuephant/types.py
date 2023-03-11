from __future__ import annotations

from enum import StrEnum
from enum import auto
from typing import Awaitable
from typing import Callable
from typing import Protocol

# Define a type alias for valid JSON values
JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
JsonDict = dict[str, JsonValue]


class AbstractTaskClass(Protocol):
    async def execute(self, payload: JsonDict) -> None:
        ...


AbstractTaskFunction = Callable[[JsonDict], Awaitable]
AbstractTask = AbstractTaskClass | AbstractTaskFunction


class JobStatus(StrEnum):
    waiting = auto()
    working = auto()
    succeeded = auto()
    failed = auto()
    canceled = auto()
