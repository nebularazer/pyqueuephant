from __future__ import annotations

import asyncio
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Protocol
from typing import cast

# import asyncpg
from asyncpg.connection import Connection
from asyncpg.pool import Pool

from pyqueuephant.job import Job

AbstractTaskFunction = Callable[[dict[str, Any]], Awaitable]


class AbstractTaskClass(Protocol):
    async def execute(self, payload: dict[str, Any]) -> None:
        ...


AbstractTask = AbstractTaskClass | AbstractTaskFunction


class TaskFailed(Exception):
    pass


class JobManager:
    def __init__(self, pool: Pool) -> None:
        self.pool = pool

    async def defer_job(self, job: Job) -> None:
        async with self.pool.acquire() as connection:
            connection = cast(Connection, connection)
            async with connection.transaction():
                await connection.execute(
                    """INSERT INTO job(id, status, name) VALUES($1, $2, $3);""",
                    job.id,
                    "waiting",
                    job.name,
                )
                if job.depends_on is not None:
                    await connection.executemany(
                        """INSERT INTO job_dependency(job_id, depends_on_job_id) VALUES($1, $2);""",  # noqa
                        [(job.id, dep_id) for dep_id in job.depends_on],
                    )

    async def fetch_job(self) -> Job | None:
        async with self.pool.acquire() as connection:
            connection = cast(Connection, connection)
            row = await connection.fetchrow(
                """
                WITH jobs_to_process AS (
                    SELECT j.*
                    FROM job j
                    LEFT JOIN (
                        SELECT jd.job_id, jd.depends_on_job_id
                        FROM job_dependency jd
                        JOIN job d ON jd.depends_on_job_id = d.id
                        WHERE d.status <> 'done'
                    ) AS d ON j.id = d.job_id
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM job_dependency jd2
                        JOIN job d2 ON jd2.depends_on_job_id = d2.id
                        WHERE jd2.job_id = j.id
                        AND d2.status <> 'done'
                    )
                    AND j.status = 'waiting'
                    ORDER BY j.id
                    LIMIT 1
                    FOR UPDATE OF j SKIP LOCKED
                )
                UPDATE job
                SET status = 'doing'
                WHERE id IN (
                    SELECT id
                    FROM jobs_to_process
                )
                RETURNING *;
                """
            )

        if not row:
            return None

        return Job.from_row(row)

    async def fail_job(self, job: Job, traceback: str) -> None:
        async with self.pool.acquire() as connection:
            connection = cast(Connection, connection)
            async with connection.transaction():
                await connection.execute(
                    """
                    UPDATE job SET status = 'failed' WHERE id = $1
                    """,
                    job.id,
                )
                await connection.execute(
                    """
                    INSERT INTO job_failure(job_id, attempt, traceback)
                    VALUES($1, $2, $3);
                    """,
                    job.id,
                    1,
                    traceback,
                )

    async def finish_job(self, job: Job) -> None:
        async with self.pool.acquire() as connection:
            connection = cast(Connection, connection)
            async with connection.transaction():
                await connection.execute(
                    """
                    UPDATE job SET status = 'done' WHERE id = $1
                    """,
                    job.id,
                )

    async def cancel_job(self, job: Job, reason: str | None = None) -> None:
        # TODO: reason
        async with self.pool.acquire() as connection:
            connection = cast(Connection, connection)
            async with connection.transaction():
                await connection.execute(
                    """
                    UPDATE job SET status = 'canceled' WHERE id = $1
                    """,
                    job.id,
                )


async def main() -> None:
    pass
    # pool = await asyncpg.create_pool(
    #     database="pyqueuephant",
    #     user="postgres",
    #     password="postgres",
    # )

    # manager = JobManager(pool=pool)

    # job1 = Job(id=1, name="job 1", depends_on=None)
    # job2 = Job(id=2, name="job 2", depends_on=[job1.id])
    # job3 = Job(id=3, name="job 3", depends_on=None)
    # job4 = Job(id=4, name="job 4", depends_on=[job2.id, job3.id])
    # job5 = Job(id=5, name="job 5", depends_on=None)

    # await manager.defer_job(job1)
    # await manager.defer_job(job2)
    # await manager.defer_job(job3)
    # await manager.defer_job(job4)
    # await manager.defer_job(job5)

    # jobs = await manager.fetch_jobs()

    # pprint(jobs)


if __name__ == "__main__":
    asyncio.run(main())
