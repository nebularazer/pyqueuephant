import asyncio
from random import randint

from sqlalchemy.ext.asyncio import create_async_engine

from pyqueuephant.example_tasks.task1 import Task1Class
from pyqueuephant.job import Job
from pyqueuephant.job_manager import JobManager


async def main() -> None:
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost/pyqueuephant"
    )

    jm = JobManager(engine)

    job1 = Job.create(
        task_path=f"{Task1Class.__module__}:{Task1Class.__name__}",
        task_args={"a": randint(1, 15)},
    )
    job2 = Job.create(
        task_path=f"{Task1Class.__module__}:{Task1Class.__name__}",
        task_args={"a": randint(1, 15)},
    )
    job3 = Job.create(
        task_path=f"{Task1Class.__module__}:{Task1Class.__name__}",
        task_args={"a": randint(1, 15)},
        depends_on_jobs=[job2],
    )
    job4 = Job.create(
        task_path=f"{Task1Class.__module__}:{Task1Class.__name__}",
        task_args={"a": randint(1, 15)},
        depends_on_jobs=[job3],
    )
    job5 = Job.create(
        task_path=f"{Task1Class.__module__}:{Task1Class.__name__}",
        task_args={"a": randint(1, 15)},
        depends_on_jobs=[job1, job3],
    )
    job6 = Job.create(
        task_path=f"{Task1Class.__module__}:{Task1Class.__name__}",
        task_args={"a": randint(1, 15)},
        depends_on_jobs=[job1, job2, job3, job4],
    )

    await jm.defer_jobs(job1, job2, job3, job4, job5, job6)


if __name__ == "__main__":
    asyncio.run(main())
