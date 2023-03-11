from __future__ import annotations

import importlib
import inspect
import sys
from dataclasses import dataclass
from dataclasses import field
from typing import cast
from uuid import UUID
from uuid import uuid4

from pyqueuephant.types import AbstractTask
from pyqueuephant.types import AbstractTaskClass
from pyqueuephant.types import AbstractTaskFunction
from pyqueuephant.types import JobStatus
from pyqueuephant.types import JsonDict


class TaskFailed(Exception):
    pass


class TaskNotFound(Exception):
    pass


@dataclass
class JobResult:
    id: int
    job_id: UUID
    attempt: int = 1
    result: str | None = None


@dataclass
class Job:
    id: UUID
    task_path: str
    task_args: JsonDict = field(default_factory=dict)
    status: JobStatus = JobStatus.waiting
    depends_on_jobs: list[Job] = field(default_factory=list)

    @staticmethod
    def create(
        task_path: str,
        task_args: JsonDict | None = None,
        depends_on_jobs: list[Job] | None = None,
    ) -> Job:
        if task_args is None:
            task_args = {}

        if depends_on_jobs is None:
            depends_on_jobs = []

        return Job(
            id=uuid4(),
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
