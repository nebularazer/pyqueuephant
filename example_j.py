import asyncio

import asyncpg

from pyqueuephant.example_tasks.task1 import Task1Class
from pyqueuephant.job import Job
from pyqueuephant.job_manager import JobManager


async def main() -> None:
    pool = await asyncpg.create_pool(
        database="pyqueuephant",
        user="postgres",
        password="postgres",
    )

    jm = JobManager(pool)

    job1 = Job.create(
        task_path=f"{Task1Class.__module__}:{Task1Class.__name__}",
        task_args={"a": 5},
    )
    job2 = Job.create(
        task_path=f"{Task1Class.__module__}:{Task1Class.__name__}",
        task_args={"a": 10},
    )
    job3 = Job.create(
        task_path=f"{Task1Class.__module__}:{Task1Class.__name__}",
        task_args={"a": 12},
        depends_on_jobs=[job1, job2],
    )

    await jm.defer_job(job1, job2, job3)


if __name__ == "__main__":
    asyncio.run(main())
