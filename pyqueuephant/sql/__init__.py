from __future__ import annotations

import importlib.resources
import re
from dataclasses import dataclass
from dataclasses import make_dataclass

QUERIES_RE = re.compile(r"(?:\n|^)-- ([a-z0-9_]+) --\n(?:-- .+\n)*", re.MULTILINE)


@dataclass
class Queries:
    pass


def parse_queries() -> Queries:
    content = (
        importlib.resources.files("pyqueuephant.sql") / "queries.sql"
    ).read_text()
    split = iter(QUERIES_RE.split(content))
    next(split)

    queries: dict[str, str] = {}
    try:
        while True:
            name = next(split)
            query = next(split).strip()
            queries[name] = query
    except StopIteration:
        pass

    q = Queries()
    q.__class__ = make_dataclass(
        "Queries",
        fields=[(key, str) for key in list(queries.keys())],
        bases=(Queries,),
    )
    for key, value in queries.items():
        setattr(q, key, value)

    return q


queries = parse_queries()
