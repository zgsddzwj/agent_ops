import asyncio
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


def main():
    from arq.worker import run_worker

    run_worker(WorkerSettings)


if __name__ == "__main__":
    main()
