import asyncio
import random
from typing import Any
from typing import TypedDict
from typing import cast

from pyqueuephant.types import JsonDict


class ExamplePayload(TypedDict):
    a: int


class Task1Class:
    async def execute(self, payload: JsonDict) -> None:
        fail = random.choice((False, False))

        data = cast(ExamplePayload, payload)

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
