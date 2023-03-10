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

from pyqueuephant.types import JobStatus

metadata = MetaData()

TABLE_PREFIX = "pyqueuephant_"

# ENUMS
job_status_type = postgresql.ENUM(
    *(e.value for e in JobStatus),
    name=f"{TABLE_PREFIX}job_status_type",
    create_type=False,
)
job_event_type = postgresql.ENUM(
    "deferred",
    "started",
    "succeeded",
    "failed",
    "canceled",
    "deferred_for_retry",
    name=f"{TABLE_PREFIX}job_event_type",
    create_type=False,
)


# TABLES
job_table = Table(
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

job_dependency_table = Table(
    f"{TABLE_PREFIX}job_dependency",
    metadata,
    Column("id", BIGINT, primary_key=True),
    Column(
        "job_id",
        postgresql.UUID(as_uuid=True),
        ForeignKey(job_table.c.id),
        nullable=False,
    ),
    Column(
        "depends_on_job_id",
        postgresql.UUID(as_uuid=True),
        ForeignKey(job_table.c.id),
        nullable=False,
    ),
)

job_result_table = Table(
    f"{TABLE_PREFIX}job_result",
    metadata,
    Column("id", BIGINT, primary_key=True),
    Column(
        "job_id",
        postgresql.UUID(as_uuid=True),
        ForeignKey(job_table.c.id),
        nullable=False,
    ),
    Column("attempt", SMALLINT, nullable=False, server_default="1"),
    Column("result", String),
)


job_event = Table(
    f"{TABLE_PREFIX}job_event",
    metadata,
    Column("id", BIGINT, primary_key=True),
    Column(
        "job_id",
        postgresql.UUID(as_uuid=True),
        ForeignKey(job_table.c.id),
        nullable=False,
    ),
    Column("event", job_event_type, nullable=False),
    Column(
        "timestamp",
        DateTime(timezone=True),
        nullable=False,
        server_default=text("TIMEZONE('utc', CURRENT_TIMESTAMP)"),
    ),
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
