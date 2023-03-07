import asyncio
import json
import random
from typing import Any


class Task1Class:
    async def execute(self, payload: str) -> None:
        fail = random.choice((False, False))
        data = json.loads(payload)
        sleep = data["a"]
        print(f"sleeping for: {sleep}")
        await asyncio.sleep(sleep)
        if fail:
            print(f"FAILED: Task1Class.execute({data=})")
            raise ZeroDivisionError
        else:
            print(f"FINISHED: Task1Class.execute({data=})")

    async def __call__(self, *args: Any, **kwds: Any) -> Any:
        print(f"Task1Class.__call__: ({args}, {kwds=})")
