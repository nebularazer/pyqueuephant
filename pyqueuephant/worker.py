import asyncio
import os
import signal
import traceback
from asyncio import CancelledError as CanceledError  # yes, i did that...
from asyncio import TimeoutError
from typing import Any
from typing import Callable
from typing import cast

import asyncpg
from asyncpg import Pool
from asyncpg.connection import Connection

from pyqueuephant.job import Job
from pyqueuephant.job import TaskFailed
from pyqueuephant.job_manager import JobManager

PG_NOTIFY_CHANNEL = "pyqueuephant"
SHUTDOWN_SIGNALS = [signal.SIGINT, signal.SIGTERM]
SHUTDOWN_TIMEOUT = 10
WORKER_CONCURRENCY = 3


class Worker:
    def __init__(
        self,
        pool: Pool,
        channel: str = PG_NOTIFY_CHANNEL,
        shutdown_timeout: int = SHUTDOWN_TIMEOUT,
        concurrency: int = WORKER_CONCURRENCY,
    ) -> None:
        self.pool = pool
        self.channel = channel
        self.shutdown_timeout = shutdown_timeout
        self.concurrency = concurrency

        self.event = asyncio.Event()
        self.manager = JobManager(pool=pool)
        self._shutdown_requested = False
        self._shutdown_event = asyncio.Event()

        self.running_tasks: set[asyncio.Task] = set()

    @property
    def shutdown_requested(self) -> bool:
        return self._shutdown_requested

    @shutdown_requested.setter
    def shutdown_requested(self, value: bool) -> None:
        self._shutdown_requested = value
        if value is True:
            self._shutdown_event.set()
            self.event.set()

    async def job_worker(self, id: int) -> None:
        print(f"Start job worker-{id}...")
        while not self.shutdown_requested:
            job = await self.manager.fetch_job()
            if job is not None:
                print(f"Fetched a job ({job.name}) to process...")
                await self.execute_job(job)

            else:
                self.event.clear()
                print("Waiting for notifications...")
                await self.event.wait()
        else:
            print(f"Stopped worker-{id}.")

    async def execute_job(self, job: Job) -> None:
        try:
            task = asyncio.create_task(job.run_task())
            task.add_done_callback(self.running_tasks.discard)
            self.running_tasks.add(task)
            await task
            await self.manager.finish_job(job)
            print(f"Finished to process job ({job.name}).")
        except TaskFailed:
            tb = traceback.format_exc(chain=False)
            await self.manager.fail_job(job, tb)
        except CanceledError:
            print(f"Canceled Job ({job.name}) due to worker shutdown.")
            await self.manager.cancel_job(job, reason="Worker shutdown")  # TODO: DB!

    @staticmethod
    def _pg_notify_handler(
        event: asyncio.Event,
    ) -> Callable[[Any, Any, str, Any], None]:
        def handle(connection: Any, pid: Any, channel: str, payload: Any) -> None:
            print(f"PG Notification: {channel}")
            event.set()

        return handle

    async def _shutdown(self) -> None:
        print("Received shutdown signal...")
        self.shutdown_requested = True
        loop = asyncio.get_running_loop()
        loop.remove_signal_handler(signal.SIGINT)
        loop.remove_signal_handler(signal.SIGTERM)

        tasks = self.running_tasks
        if len(tasks) == 0:
            return

        try:
            gather = asyncio.gather(*tasks)
            print(f"Wait {self.shutdown_timeout}s for {len(tasks)} jobs to finish.")
            await asyncio.wait_for(gather, timeout=self.shutdown_timeout)
            print("All tasks finished before timeout...")
        except TimeoutError:
            print("Wait for unfinished tasks cleanup...")

    async def listener(self) -> None:
        async with self.pool.acquire() as connection:
            connection = cast(Connection, connection)
            handler = self._pg_notify_handler(self.event)
            await connection.add_listener(self.channel, handler)

            await self._shutdown_event.wait()
            print("No longer waiting for pg notify.")

            await connection.remove_listener(self.channel, handler)

    async def run(self) -> None:
        loop = asyncio.get_event_loop()
        for sig in SHUTDOWN_SIGNALS:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self._shutdown()))

        job_workers = [
            asyncio.create_task(self.job_worker(id=id))
            for id in range(self.concurrency)
        ]
        listener = asyncio.create_task(self.listener())

        await asyncio.gather(*job_workers, listener, return_exceptions=False)


async def main() -> None:
    pool = await asyncpg.create_pool(
        database="pyqueuephant",
        user="postgres",
        password="postgres",
    )

    worker = Worker(pool)

    pid = os.getpid()
    print(pid)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
