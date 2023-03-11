from alembic_utils.replaceable_entity import register_entities

from . import extensions
from . import procedures
from . import triggers
from .tables import metadata

entities = [
    extensions.uuid_ossp,
    procedures.job_status_event_changed_procedure,
    triggers.job_status_event_changed_trigger,
]

register_entities(entities)


__all__ = [
    "metadata",
]
