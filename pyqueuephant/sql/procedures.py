from alembic_utils.pg_function import PGFunction

from .utils import read_file

job_status_event_changed_procedure = PGFunction(
    schema="public",
    signature="pyqueuephant_job_status_event_changed_procedure()",
    definition=read_file("job_status_event_changed_procedure.sql"),
)
