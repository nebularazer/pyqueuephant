from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.schema import MetaData
from sqlalchemy.sql.schema import Table
from sqlalchemy.types import BIGINT
from sqlalchemy.types import SMALLINT
from sqlalchemy.types import DateTime
from sqlalchemy.types import String

from pyqueuephant.job_manager import JobStatus

metadata = MetaData()

TABLE_PREFIX = ""

# ENUMS
job_status_type = postgresql.ENUM(
    *(e.value for e in JobStatus),
    name=f"{TABLE_PREFIX}job_status_type",
)
job_event_type = postgresql.ENUM(
    "deferred",
    "started",
    "succeeded",
    "failed",
    "canceled",
    "deferred_for_retry",
    name=f"{TABLE_PREFIX}job_event_type",
)

# TABLES
job = Table(
    f"{TABLE_PREFIX}job",
    metadata,
    Column(
        "id",
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    ),
    Column("status", job_status_type, nullable=False, server_default="waiting"),
    Column("task_path", String(128), nullable=False),
    Column("task_args", postgresql.JSONB, nullable=False, server_default="{}"),
)

job_dependency = Table(
    f"{TABLE_PREFIX}job_dependency",
    metadata,
    Column("id", BIGINT, primary_key=True),
    Column(
        "job_id", postgresql.UUID(as_uuid=True), ForeignKey("job.id"), nullable=False
    ),
    Column(
        "depends_on_job_id",
        postgresql.UUID(as_uuid=True),
        ForeignKey("job.id"),
        nullable=False,
    ),
)

job_result = Table(
    f"{TABLE_PREFIX}job_result",
    metadata,
    Column("id", BIGINT, primary_key=True),
    Column(
        "job_id", postgresql.UUID(as_uuid=True), ForeignKey("job.id"), nullable=False
    ),
    Column("attempt", SMALLINT, nullable=False, server_default="1"),
    Column("result", String),
)


job_event = Table(
    f"{TABLE_PREFIX}job_event",
    metadata,
    Column("id", BIGINT, primary_key=True),
    Column(
        "job_id", postgresql.UUID(as_uuid=True), ForeignKey("job.id"), nullable=False
    ),
    Column("event", job_event_type, nullable=False),
    Column("timestamp", DateTime(timezone=True), server_default="now()"),
)

periodic_jobs = Table(
    f"{TABLE_PREFIX}periodic_jobs",
    metadata,
    Column("id", BIGINT, primary_key=True),
    Column("schedule", String(255), nullable=False),
    Column("last_deferred", DateTime(timezone=True)),
    Column("task_path", String(128), nullable=False),
    Column("task_args", postgresql.JSONB, nullable=False, server_default="{}"),
)


def main() -> None:
    from sqlalchemy import create_engine
    from sqlalchemy import literal_column
    from sqlalchemy import select
    from sqlalchemy import update

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

    update_query = (
        update(job)
        .values(status=JobStatus.working)
        .where(job_to_process.c.id == job.c.id)
        .returning(job)
    )

    engine = create_engine("postgresql+asyncpg://postgres:postgres@localhost")
    query = update_query.compile(
        bind=engine,
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True},
    )

    print(
        str(
            query.statement.compile(  # type: ignore[union-attr]
                bind=engine,
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        )
    )


if __name__ == "__main__":
    main()
