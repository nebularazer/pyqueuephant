"""add pyqueuphant tables.

Revision ID: 038d56428718
Revises: a93e271e4aae
Create Date: 2023-03-08 22:08:08.899291

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "038d56428718"
down_revision = "a93e271e4aae"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "job",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "waiting",
                "working",
                "succeeded",
                "failed",
                "canceled",
                name="job_status_type",
            ),
            server_default="waiting",
            nullable=False,
        ),
        sa.Column("task_path", sa.String(length=128), nullable=False),
        sa.Column(
            "task_args",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "periodic_jobs",
        sa.Column("id", sa.BIGINT(), nullable=False),
        sa.Column("schedule", sa.String(length=255), nullable=False),
        sa.Column("last_deferred", sa.DateTime(timezone=True), nullable=True),
        sa.Column("task_path", sa.String(length=128), nullable=False),
        sa.Column(
            "task_args",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "job_dependency",
        sa.Column("id", sa.BIGINT(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("depends_on_job_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["depends_on_job_id"],
            ["job.id"],
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["job.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "job_event",
        sa.Column("id", sa.BIGINT(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column(
            "event",
            postgresql.ENUM(
                "deferred",
                "started",
                "succeeded",
                "failed",
                "canceled",
                "deferred_for_retry",
                name="job_event_type",
            ),
            nullable=False,
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default="now()",
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["job.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "job_result",
        sa.Column("id", sa.BIGINT(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("attempt", sa.SMALLINT(), server_default="1", nullable=False),
        sa.Column("result", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["job.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("job_result")
    op.drop_table("job_event")
    op.drop_table("job_dependency")
    op.drop_table("periodic_jobs")
    op.drop_table("job")
    # ### end Alembic commands ###
