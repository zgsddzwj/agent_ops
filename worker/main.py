"""ARQ worker entry point for Agent Ops background tasks.

Runs periodic and on-demand jobs: eval runs, benchmark runs, security
scans, and hourly metric aggregation. Start with `python -m worker.main`
or `arq worker.main.WorkerSettings`.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from arq import cron
from arq.connections import RedisSettings

from app.core.config import settings
from worker.tasks import (
    aggregate_metrics_task,
    run_benchmark_task,
    run_eval_task,
    run_security_scan_task,
)


class WorkerSettings:
    """Settings consumed by arq's run_worker.

    max_tries limits retries so a persistently failing scan task does not
    retry 5 times by default; job_timeout is raised above arq's 300s default
    because eval/benchmark jobs can legitimately run longer.
    """

    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    functions = [
        run_eval_task,
        run_benchmark_task,
        run_security_scan_task,
        aggregate_metrics_task,
    ]
    cron_jobs = [
        cron(aggregate_metrics_task, hour=None, minute=0),
    ]
    max_jobs = 10
    max_tries = 3
    job_timeout = 600
    keep_result = 3600


def main():
    from arq.worker import run_worker

    run_worker(WorkerSettings)


if __name__ == "__main__":
    main()
