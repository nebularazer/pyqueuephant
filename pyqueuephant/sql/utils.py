import importlib.resources


def read_file(filename: str) -> str:
    return (importlib.resources.files("pyqueuephant.sql.raw") / filename).read_text()
