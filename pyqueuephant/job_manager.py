from __future__ import annotations

import json
from typing import cast

from asyncpg.connection import Connection
from asyncpg.pool import Pool

from pyqueuephant.job import Job
from pyqueuephant.job import JobStatus
from pyqueuephant.sql import queries


class JobManager:
    def __init__(self, pool: Pool) -> None:
        self.pool = pool

    async def defer_job(self, *jobs: Job) -> None:
        async with self.pool.acquire() as connection:
            connection = cast(Connection, connection)
            async with connection.transaction():
                await connection.executemany(
                    queries.defer_job,
                    [
                        (job.id, job.task_path, json.dumps(job.task_args))
                        for job in jobs
                    ],
                )
                for job in jobs:
                    if job.depends_on_jobs is None:
                        continue
                    await connection.executemany(
                        queries.add_job_dependencies,
                        [(job.id, depends.id) for depends in job.depends_on_jobs],
                    )

    async def fetch_job(self) -> Job | None:
        async with self.pool.acquire() as connection:
            connection = cast(Connection, connection)
            row = await connection.fetchrow(queries.fetch_job)

        if not row:
            return None

        return Job.from_row(row)

    async def finish_job(self, job: Job, traceback: str | None = None) -> None:
        # TODO: reason
        async with self.pool.acquire() as connection:
            connection = cast(Connection, connection)
            async with connection.transaction():
                await connection.execute(
                    queries.finish_job,
                    job.status.value,
                    job.id,
                )
                if job.status == JobStatus.failed:
                    await connection.execute(
                        queries.add_job_failure,
                        job.id,
                        1,
                        traceback,
                    )
