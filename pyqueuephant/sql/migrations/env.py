import asyncio
import os
from logging.config import fileConfig
from typing import cast

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.engine import Engine
from sqlalchemy.engine import engine_from_config
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.ext.asyncio.engine import async_engine_from_config

from pyqueuephant.sql import tables

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = tables.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url() -> str:
    # postgresql+asyncpg://postgres:postgres@localhost/database-name
    # url = PostgresDsn.build(
    #     scheme="postgresql+asyncpg",
    #     user=os.environ["POSTGRES_USER"],
    #     password=os.environ["POSTGRES_PASSWORD"],
    #     host=os.environ["POSTGRES_SERVER"],
    #     path=f"/{os.environ['POSTGRES_DATABASE']}",
    #     query=os.getenv("POSTGRES_QUERY", None),
    # )

    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.environ["POSTGRES_SERVER"]
    path = f"{os.environ['POSTGRES_DATABASE']}"

    return f"postgresql+asyncpg://{user}:{password}@{host}/{path}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def include_name(name: str, type_: str, parent_names: dict) -> bool:
    if type_ == "table":
        return not name.startswith(("job_", "periodic_"))

    return False


# def include_object(object, name, type_, reflected, compare_to):
#     if (type_ == "column" and
#         not reflected and
#         object.info.get("skip_autogenerate", False)):
#         return False
#     else:
#         return True


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    tag = context.get_tag_argument()
    if tag != "pytest":
        config.set_main_option("sqlalchemy.url", get_url())

    configuration = config.get_section(config.config_ini_section) or {}
    connectable: AsyncEngine | Engine | None = context.config.attributes.get(
        "connection", None
    )

    config_database_url = cast(str, config.get_main_option("sqlalchemy.url"))
    database_url = make_url(config_database_url)

    if database_url.drivername.endswith("psycopg2"):
        engine_from_config_fn = engine_from_config
    else:
        engine_from_config_fn = async_engine_from_config  # type: ignore

    if connectable is None:
        connectable = engine_from_config_fn(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )

    if isinstance(connectable, AsyncEngine):
        asyncio.run(run_async_migrations(connectable))
    elif isinstance(connectable, Engine):
        with connectable.connect() as connection:
            do_run_migrations(connection)


async def run_async_migrations(connectable: AsyncEngine) -> None:
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
