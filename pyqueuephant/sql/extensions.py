from alembic_utils.pg_extension import PGExtension

uuid_ossp = PGExtension(
    schema="public",
    signature="uuid-ossp",
)
