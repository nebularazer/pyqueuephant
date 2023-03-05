from __future__ import annotations

import importlib
import inspect
import sys
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Protocol
from typing import cast


class AbstractTaskClass(Protocol):
    async def execute(self, payload: dict[str, Any]) -> None:
        ...


AbstractTaskFunction = Callable[[dict[str, Any]], Awaitable]
AbstractTask = AbstractTaskClass | AbstractTaskFunction


class TaskFailed(Exception):
    pass


@dataclass
class JobFailure:
    id: int
    job_id: int
    attempt: int
    traceback: str


@dataclass
class Job:
    id: int
    name: str
    status: str
    task_path: str
    task_args: dict[str, Any] = field(default_factory=dict)
    depends_on: list[int] | None = None

    @classmethod
    def from_row(cls, row: Any) -> Job:
        task_args = row["task_args"]

        return Job(
            id=row["id"],
            status=row["status"],
            name=row["name"],
            task_path=row["task_path"],
            task_args=task_args if task_args is not None else {},
        )

    async def run_task(self) -> None:
        path, name = self.task_path.split(":")
        if path in sys.modules:
            module = importlib.reload(sys.modules[path])
        else:
            module = importlib.import_module(path)

        class_or_function: AbstractTask = getattr(module, name)

        try:
            if inspect.isclass(class_or_function):
                instance: AbstractTaskClass = class_or_function()
                await instance.execute(self.task_args)

            else:
                class_or_function = cast(AbstractTaskFunction, class_or_function)
                await class_or_function(self.task_args)
        except Exception as e:
            raise TaskFailed from e
        finally:
            pass
