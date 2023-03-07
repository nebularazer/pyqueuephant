import asyncio

import asyncpg

from pyqueuephant.worker import Worker


async def main() -> None:
    pool = await asyncpg.create_pool(
        database="pyqueuephant",
        user="postgres",
        password="postgres",
    )

    worker = Worker(pool)

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
