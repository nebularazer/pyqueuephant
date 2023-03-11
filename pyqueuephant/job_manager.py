from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine

from pyqueuephant.job import Job
from pyqueuephant.sql import queries


class JobManager:
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine

    async def defer_jobs(self, *jobs: Job) -> None:
        async with self.engine.begin() as connection:
            await connection.execute(queries.defer_jobs(*jobs))

            for job in jobs:
                if not job.depends_on_jobs:
                    continue

                dependency_ids = [depends.id for depends in job.depends_on_jobs]
                await connection.execute(
                    queries.add_job_dependencies(job.id, dependency_ids)
                )

    async def fetch_job(self) -> Job | None:
        async with self.engine.begin() as connection:
            result = await connection.execute(queries.fetch_job())
            row = result.one_or_none()

        if not row:
            return None

        job_id, status, path, args = row

        return Job(id=job_id, task_path=path, task_args=args, status=status)

    async def finish_job(self, job: Job, result: str | None = None) -> None:
        async with self.engine.begin() as connection:
            await connection.execute(queries.finish_job(job.id, job.status))

            if result is not None:
                await connection.execute(
                    queries.add_job_result(
                        job_id=job.id,
                        attempt=1,  # TODO: fix me
                        result=result,
                    )
                )
