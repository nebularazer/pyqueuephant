-- defer_job --
INSERT INTO job(id, task_path, task_args) VALUES ($1, $2, $3);

-- add_job_dependencies --
INSERT INTO job_dependency(job_id, depends_on_job_id) VALUES ($1, $2);

-- fetch_job --
WITH job_to_process AS (
    SELECT
        job.id,
        job.status,
        job.task_path,
        job.task_args
    FROM job
    WHERE job.status = 'waiting'
    AND NOT EXISTS (
        SELECT 1 FROM job_dependency jd
        JOIN job job_dep ON jd.depends_on_job_id = job_dep.id
        WHERE jd.job_id = job.id AND job_dep.status != 'succeeded'
    )
    LIMIT 1
    FOR UPDATE OF job SKIP LOCKED
)
UPDATE job
SET status = 'working'
FROM job_to_process
WHERE job.id = job_to_process.id
RETURNING
    job.id,
    job.status,
    job.task_path,
    job.task_args;


-- finish_job --
UPDATE job SET status = $1 WHERE id = $2;

-- add_job_failure --
INSERT INTO job_result(job_id, attempt, result) VALUES($1, $2, $3);
