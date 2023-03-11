from alembic_utils.pg_trigger import PGTrigger

from .utils import read_file

job_status_event_changed_trigger = PGTrigger(
    schema="public",
    signature="pyqueuephant_job_status_event_changed_trigger",
    on_entity="public.pyqueuephant_job",
    definition=read_file("job_status_event_changed_trigger.sql"),
)
