from uuid import UUID

from sqlalchemy import literal_column
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.sql.dml import ReturningInsert
from sqlalchemy.sql.dml import ReturningUpdate
from sqlalchemy.sql.dml import Update

from pyqueuephant.job import JobStatus
from pyqueuephant.types import JsonDict

from .tables import job
from .tables import job_dependency
from .tables import job_result


def defer_job(job_id: UUID, task_path: str, task_args: JsonDict) -> ReturningInsert:
    query = (
        job.insert()
        .values(
            id=job_id,
            task_path=task_path,
            task_args=task_args,
        )
        .returning(job.c.id)
    )

    return query


def add_job_dependencies(*dependencies: tuple[UUID, UUID]) -> ReturningInsert:
    insert_stmt = (
        job_dependency.insert()
        .values(
            [
                {
                    "job_id": job_id,
                    "depends_on_job_id": depends_on_job_id,
                }
                for job_id, depends_on_job_id in dependencies
            ]
        )
        .returning(job_dependency.c.id)
    )

    return insert_stmt


def fetch_job() -> ReturningUpdate:
    job_dep1 = job_dependency.alias("job_dep1")
    job_dep2 = job.alias("job_dep2")

    job_depens = (
        select(literal_column("1"))
        .select_from(
            job_dep1.join(
                job_dep2,
                job_dep1.c.depends_on_job_id == job_dep2.c.id,
            )
        )
        .where(
            job_dep1.c.job_id == job.c.id,
            job_dep2.c.status != "succeeded",
        )
        .exists()
    )

    job_to_process = (
        select(job)
        .where(
            job.c.status == JobStatus.waiting,
            ~job_depens,
        )
        .limit(1)
        .with_for_update(of=job, skip_locked=True)
        .cte(name="job_to_process")
    )

    update_stmt = (
        update(job)
        .values(status=JobStatus.working)
        .where(job_to_process.c.id == job.c.id)
        .returning(job)
    )

    return update_stmt


def finish_job(job_id: UUID, job_status: JobStatus) -> Update:
    update_stmt = update(job).values(status=job_status).where(job.c.id == job_id)

    return update_stmt


def add_job_failure(
    job_id: UUID, attempt: int, result: str | None = None
) -> ReturningInsert:
    insert_stmt = (
        job_result.insert()
        .values(
            job_id=job_id,
            attempt=attempt,
            result=result,
        )
        .returning(job_result.c.id)
    )

    return insert_stmt
