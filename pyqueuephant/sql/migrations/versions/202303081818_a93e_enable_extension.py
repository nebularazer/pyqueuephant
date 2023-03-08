"""enable extension.

Revision ID: a93e271e4aae
Revises:
Create Date: 2023-03-08 18:18:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a93e271e4aae"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("""CREATE EXTENSION IF NOT EXISTS "uuid-ossp";"""))


def downgrade() -> None:
    op.execute(sa.text("""DROP EXTENSION IF EXISTS "uuid-ossp";"""))
