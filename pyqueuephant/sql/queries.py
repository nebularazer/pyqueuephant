from uuid import UUID

from sqlalchemy import literal_column
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.sql.dml import ReturningInsert
from sqlalchemy.sql.dml import ReturningUpdate
from sqlalchemy.sql.dml import Update

from pyqueuephant.job import Job
from pyqueuephant.job import JobStatus

from .tables import job_dependency_table
from .tables import job_result_table
from .tables import job_table


def defer_jobs(*jobs: Job) -> ReturningInsert:
    insert_stmt = (
        job_table.insert()
        .values(
            [
                {
                    "id": job.id,
                    "task_path": job.task_path,
                    "task_args": job.task_args,
                }
                for job in jobs
            ]
        )
        .returning(job_table.c.id)
    )

    return insert_stmt


def add_job_dependencies(job_id: UUID, dependencies: list[UUID]) -> ReturningInsert:
    values = [
        {
            "job_id": job_id,
            "depends_on_job_id": depends_on_job_id,
        }
        for depends_on_job_id in dependencies
    ]

    insert_stmt = (
        job_dependency_table.insert()
        .values(values)
        .returning(job_dependency_table.c.id)
    )

    return insert_stmt


def fetch_job() -> ReturningUpdate:
    job_dep1 = job_dependency_table.alias("job_dep1")
    job_dep2 = job_table.alias("job_dep2")

    job_depens = (
        select(literal_column("1"))
        .select_from(
            job_dep1.join(
                job_dep2,
                job_dep1.c.depends_on_job_id == job_dep2.c.id,
            )
        )
        .where(
            job_dep1.c.job_id == job_table.c.id,
            job_dep2.c.status != JobStatus.succeeded,
        )
        .exists()
    )

    job_to_process = (
        select(job_table)
        .where(
            job_table.c.status == JobStatus.waiting,
            ~job_depens,
        )
        .limit(1)
        .with_for_update(of=job_table, skip_locked=True)
        .cte(name="job_to_process")
    )

    update_stmt = (
        update(job_table)
        .values(status=JobStatus.working)
        .where(job_to_process.c.id == job_table.c.id)
        .returning(job_table)
    )

    return update_stmt


def finish_job(job_id: UUID, job_status: JobStatus) -> Update:
    update_stmt = (
        update(job_table).values(status=job_status).where(job_table.c.id == job_id)
    )

    return update_stmt


def add_job_result(job_id: UUID, attempt: int, result: str) -> ReturningInsert:
    insert_stmt = (
        job_result_table.insert()
        .values(
            job_id=job_id,
            attempt=attempt,
            result=result,
        )
        .returning(job_result_table.c.id)
    )

    return insert_stmt
