-- defer_job --
INSERT INTO job(id, task_path, task_args) VALUES ($1, $2, $3);

-- add_job_dependencies --
INSERT INTO job_dependency(job_id, depends_on_job_id) VALUES ($1, $2);

-- fetch_job --
WITH jobs_to_process AS (
    SELECT j.*
    FROM job j
    LEFT JOIN (
        SELECT
            jd.job_id,
            jd.depends_on_job_id
        FROM
            job_dependency jd
        JOIN
            job d ON jd.depends_on_job_id = d.id
        WHERE
            d.status NOT IN ('succeeded', 'failed')
    ) AS d ON j.id = d.job_id

    WHERE
        NOT EXISTS (
            SELECT 1
            FROM
                job_dependency jd2
                JOIN job d2 ON jd2.depends_on_job_id = d2.id
            WHERE
                jd2.job_id = j.id
                AND d2.status NOT IN ('succeeded', 'failed')
        )
        AND j.status = 'waiting'
    ORDER BY j.id
    LIMIT 1
    FOR UPDATE OF j SKIP LOCKED
)
UPDATE job
SET status = 'working'
WHERE id IN (
    SELECT id
    FROM jobs_to_process
) RETURNING *;


-- finish_job --
UPDATE job SET status = $1 WHERE id = $2;

-- add_job_failure --
INSERT INTO job_result(job_id, attempt, result) VALUES($1, $2, $3);
