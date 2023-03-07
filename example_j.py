import asyncio
from typing import Generator

import asyncpg

from pyqueuephant.example_tasks.task1 import Task1Class
from pyqueuephant.job import Job
from pyqueuephant.job_manager import JobManager


def int_generator(start: int) -> Generator[int, None, None]:
    while True:
        yield start
        start += 1


async def main() -> None:
    pool = await asyncpg.create_pool(
        database="pyqueuephant",
        user="postgres",
        password="postgres",
    )

    jm = JobManager(pool)

    gen = int_generator(7)

    job1 = Job.create(
        id=next(gen),
        task_path=f"{Task1Class.__module__}:{Task1Class.__name__}",
        task_args={"a": 5},
    )
    job2 = Job.create(
        id=next(gen),
        task_path=f"{Task1Class.__module__}:{Task1Class.__name__}",
        task_args={"a": 10},
    )
    job3 = Job.create(
        id=next(gen),
        task_path=f"{Task1Class.__module__}:{Task1Class.__name__}",
        task_args={"a": 12},
        depends_on_jobs=[job1, job2],
    )

    await jm.defer_job(job1)
    await jm.defer_job(job2)
    await jm.defer_job(job3)


if __name__ == "__main__":
    asyncio.run(main())
