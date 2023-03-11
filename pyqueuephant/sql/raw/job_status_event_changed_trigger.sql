-- CREATE TRIGGER job_status_event_changed_trigger
  AFTER INSERT OR UPDATE ON pyqueuephant_job
  FOR EACH ROW
  EXECUTE PROCEDURE pyqueuephant_job_status_event_changed_procedure ();
