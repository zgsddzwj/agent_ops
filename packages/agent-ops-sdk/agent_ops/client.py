import asyncio
import json
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

DEFAULT_PRICING = {
    ("openai", "gpt-4o"): (2.50, 10.00),
    ("openai", "gpt-4o-mini"): (0.15, 0.60),
    ("qwen", "qwen-plus"): (0.40, 1.20),
    ("qwen", "qwen-turbo"): (0.05, 0.15),
    ("deepseek", "deepseek-chat"): (0.14, 0.28),
    ("anthropic", "claude-sonnet-4-20250514"): (3.00, 15.00),
}


def estimate_cost(
    provider: str | None, model: str | None, tokens_in: int, tokens_out: int
) -> float | None:
    if not model:
        return None
    for (p, m), (inp, out) in DEFAULT_PRICING.items():
        if m == model or (provider and p == provider and m == model):
            return tokens_in / 1000 * inp + tokens_out / 1000 * out
    return None


class AgentOpsClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8000",
        flush_interval: float = 5.0,
        flush_size: int = 50,
        offline_fallback: str | None = None,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.flush_interval = flush_interval
        self.flush_size = flush_size
        self.offline_fallback = offline_fallback
        self._buffer: list[dict] = []
        self._run_buffer: dict | None = None
        self._lock = threading.Lock()
        self._current_run_id: uuid.UUID | None = None
        self._flush_thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start_run(
        self,
        name: str | None = None,
        model_provider: str | None = None,
        model_name: str | None = None,
        metadata: dict | None = None,
    ) -> uuid.UUID:
        run_id = uuid.uuid4()
        self._current_run_id = run_id
        self._run_buffer = {
            "id": str(run_id),
            "name": name,
            "status": "running",
            "model_provider": model_provider,
            "model_name": model_name,
            "metadata": metadata,
        }
        return run_id

    def end_run(
        self,
        status: str = "success",
        latency_ms: float | None = None,
        ttft_ms: float | None = None,
        total_tokens: int | None = None,
        cost_usd: float | None = None,
        error: str | None = None,
    ) -> None:
        if self._run_buffer:
            self._run_buffer.update(
                {
                    "status": status,
                    "latency_ms": latency_ms,
                    "ttft_ms": ttft_ms,
                    "total_tokens": total_tokens,
                    "cost_usd": cost_usd,
                    "error": error,
                }
            )
        self.flush()

    def add_span(self, span: dict) -> None:
        with self._lock:
            self._buffer.append(span)
            if len(self._buffer) >= self.flush_size:
                self._do_flush()

    @property
    def current_run_id(self) -> uuid.UUID | None:
        return self._current_run_id

    def flush(self) -> None:
        with self._lock:
            self._do_flush()

    def _do_flush(self) -> None:
        if not self._buffer and not self._run_buffer:
            return
        payload = {
            "run": self._run_buffer,
            "spans": self._buffer[:],
        }
        self._buffer.clear()
        run_copy = self._run_buffer
        self._run_buffer = None

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{self.base_url}/v1/traces/ingest",
                    json=payload,
                    headers={"X-API-Key": self.api_key},
                )
                resp.raise_for_status()
        except Exception as e:
            if self.offline_fallback:
                path = Path(self.offline_fallback)
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("a") as f:
                    f.write(json.dumps({"error": str(e), "payload": payload}) + "\n")
            elif run_copy:
                self._run_buffer = run_copy

    def ingest_sync(self, run: dict | None, spans: list[dict]) -> None:
        payload = {"run": run, "spans": spans}
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{self.base_url}/v1/traces/ingest",
                json=payload,
                headers={"X-API-Key": self.api_key},
            )
            resp.raise_for_status()
