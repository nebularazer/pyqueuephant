"""enable extensions.

Revision ID: ee4bbd3a1bb0
Revises:
Create Date: 2023-03-11 21:35:52.998988

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ee4bbd3a1bb0"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("""CREATE EXTENSION IF NOT EXISTS "uuid-ossp";"""))


def downgrade() -> None:
    op.execute(sa.text("""DROP EXTENSION IF EXISTS "uuid-ossp";"""))
