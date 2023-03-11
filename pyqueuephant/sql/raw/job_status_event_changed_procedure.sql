-- CREATE FUNCTION job_status_event_changed_procedure()
RETURNS TRIGGER
  LANGUAGE plpgsql
AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    -- INSTERT -> waiting: deferred
    INSERT INTO pyqueuephant_job_event(job_id, event)
    VALUES (NEW.id, 'deferred');
    NOTIFY pyqueuephant;
    RETURN NEW;
  ELSEIF TG_OP = 'UPDATE' THEN
    -- waiting -> working: started
    IF OLD.status = 'waiting'::pyqueuephant_job_status_type AND NEW.status = 'working'::pyqueuephant_job_status_type THEN
      INSERT INTO pyqueuephant_job_event(job_id, event)
      VALUES (OLD.id, 'started');
    -- working -> succeeded: succeeded
    ELSIF OLD.status = 'working'::pyqueuephant_job_status_type AND NEW.status = 'succeeded'::pyqueuephant_job_status_type THEN
      INSERT INTO pyqueuephant_job_event(job_id, event)
      VALUES (OLD.id, 'succeeded');
    -- working -> failed: failed
    ELSIF OLD.status = 'working'::pyqueuephant_job_status_type AND NEW.status = 'failed'::pyqueuephant_job_status_type THEN
      INSERT INTO pyqueuephant_job_event(job_id, event)
      VALUES (OLD.id, 'failed');
    -- waiting, working -> waiting: deferred_for_retry
    ELSIF OLD.status IN (
      'waiting'::pyqueuephant_job_status_type,
      'working'::pyqueuephant_job_status_type
     ) AND NEW.status = 'canceled'::pyqueuephant_job_status_type THEN
      INSERT INTO pyqueuephant_job_event(job_id, event)
      VALUES (OLD.id, 'canceled');
    -- working, succeeded, failed, canceled -> waiting: deferred_for_retry
    ELSIF OLD.status IN (
      'working'::pyqueuephant_job_status_type,
      'succeeded'::pyqueuephant_job_status_type,
      'failed'::pyqueuephant_job_status_type,
      'canceled'::pyqueuephant_job_status_type
    ) AND NEW.status = 'waiting'::pyqueuephant_job_status_type THEN
      INSERT INTO pyqueuephant_job_event(job_id, event)
      VALUES (OLD.id, 'deferred_for_retry');
    END IF;
    RETURN NEW;
  END IF;
END;
$$;
