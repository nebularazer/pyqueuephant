import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from pyqueuephant.worker import Worker


async def main() -> None:
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost/pyqueuephant"
    )

    worker = Worker(engine)

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
