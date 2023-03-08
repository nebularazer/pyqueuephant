CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TYPE job_status_type AS ENUM (
  'waiting',
  'working',
  'failed',
  'succeeded',
  'canceled'
);

CREATE TYPE job_event_type AS ENUM (
  'deferred',
  'started',
  'succeeded',
  'failed',
  'canceled',
  'deferred_for_retry'
);

-- job --
CREATE TABLE job (
  id uuid DEFAULT uuid_generate_v4() NOT NULL PRIMARY KEY,
  status job_status_type DEFAULT 'waiting' ::job_status_type NOT NULL,
  task_path character varying(128) NOT NULL,
  task_args jsonb DEFAULT '{}' NOT NULL
);

-- job dependencies --
CREATE TABLE job_dependency (
  id bigserial PRIMARY KEY,
  job_id uuid REFERENCES job (id),
  depends_on_job_id uuid REFERENCES job (id)
);

-- job results --
CREATE TABLE job_result (
  id bigserial PRIMARY KEY,
  job_id uuid REFERENCES job (id),
  attempt smallint DEFAULT 1 NOT NULL,
  result character varying
);

-- periodic jobs --
CREATE TABLE periodic_jobs (
  id bigserial PRIMARY KEY,
  schedule varchar(255) NOT NULL,
  last_deferred timestamp with time zone,
  task_path character varying(128) NOT NULL,
  task_args jsonb DEFAULT '{}' NOT NULL
);

-- job events --
CREATE TABLE job_event (
  id bigserial PRIMARY KEY,
  job_id uuid REFERENCES job (id),
  event job_event_type NOT NULL,
  timestamp timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

-- none -> waiting: deferred
-- waiting -> working: started
-- working -> succeeded: succeeded
-- working -> failed: failed
-- working -> canceled: canceled
-- working, failed, succeeded, canceld -> waiting: deferred_for_retry
-- FUNCTIONS
CREATE FUNCTION job_status_event_changed_procedure() RETURNS TRIGGER
  LANGUAGE plpgsql
AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    -- INSTERT -> waiting: deferred
    INSERT INTO job_event(job_id, event)
    VALUES (NEW.id, 'deferred');
    NOTIFY pyqueuephant;
    RETURN NEW;
  ELSEIF TG_OP = 'UPDATE' THEN
    -- waiting -> working: started
    IF OLD.status = 'waiting'::job_status_type AND NEW.status = 'working'::job_status_type THEN
      INSERT INTO job_event(job_id, event)
      VALUES (OLD.id, 'started');
    -- working -> succeeded: succeeded
    ELSIF OLD.status = 'working'::job_status_type AND NEW.status = 'succeeded'::job_status_type THEN
      INSERT INTO job_event(job_id, event)
      VALUES (OLD.id, 'succeeded');
    -- working -> failed: failed
    ELSIF OLD.status = 'working'::job_status_type AND NEW.status = 'failed'::job_status_type THEN
      INSERT INTO job_event(job_id, event)
      VALUES (OLD.id, 'failed');
    -- waiting, working -> waiting: deferred_for_retry
    ELSIF OLD.status IN (
      'waiting'::job_status_type,
      'working'::job_status_type
     ) AND NEW.status = 'canceled'::job_status_type THEN
      INSERT INTO job_event(job_id, event)
      VALUES (OLD.id, 'canceled');
    -- working, succeeded, failed, canceled -> waiting: deferred_for_retry
    ELSIF OLD.status IN (
      'working'::job_status_type,
      'succeeded'::job_status_type,
      'failed'::job_status_type,
      'canceled'::job_status_type
    ) AND NEW.status = 'waiting'::job_status_type THEN
      INSERT INTO job_event(job_id, event)
      VALUES (OLD.id, 'deferred_for_retry');
    END IF;
    RETURN NEW;
  END IF;
END;
$$;

-- TRIGGERS
CREATE TRIGGER job_status_event_changed_trigger
  AFTER INSERT OR UPDATE ON job
  FOR EACH ROW
  EXECUTE PROCEDURE job_status_event_changed_procedure ();
