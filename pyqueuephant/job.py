from __future__ import annotations

import importlib
import inspect
import sys
from dataclasses import dataclass
from dataclasses import field
from enum import StrEnum
from enum import auto
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


class TaskNotFound(Exception):
    pass


class JobStatus(StrEnum):
    waiting = auto()
    working = auto()
    finished = auto()
    failed = auto()
    canceled = auto()


@dataclass
class JobFailure:
    id: int
    job_id: int
    attempt: int
    traceback: str


@dataclass
class Job:
    id: int
    task_path: str
    task_args: dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.waiting
    depends_on_jobs: list[Job] | None = None

    @classmethod
    def from_row(cls, row: Any) -> Job:
        task_args = row["task_args"]

        return Job(
            id=row["id"],
            status=JobStatus(row["status"]),
            task_path=row["task_path"],
            task_args=task_args if task_args is not None else {},
        )

    @staticmethod
    def create(
        id: int,
        task_path: str,
        task_args: dict[str, Any] = {},
        depends_on_jobs: list[Job] | None = None,
    ) -> Job:
        return Job(
            id=id,
            task_path=task_path,
            task_args=task_args,
            depends_on_jobs=depends_on_jobs,
        )

    async def run_task(self) -> None:
        path, name = self.task_path.split(":")
        try:
            if path in sys.modules:
                module = importlib.reload(sys.modules[path])
            else:
                module = importlib.import_module(path)
        except ModuleNotFoundError:
            raise TaskNotFound

        class_or_function: AbstractTask = getattr(module, name)

        try:
            if inspect.isclass(class_or_function):
                instance: AbstractTaskClass = class_or_function()
                await instance.execute(self.task_args)

            else:
                class_or_function = cast(AbstractTaskFunction, class_or_function)
                await class_or_function(self.task_args)
        except Exception:
            raise TaskFailed
