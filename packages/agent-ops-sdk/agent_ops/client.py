import asyncio
import json
import logging
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

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
    """Estimate cost in USD based on model pricing table."""
    if not model:
        return None
    for (p, m), (inp, out) in DEFAULT_PRICING.items():
        if m == model or (provider and p == provider and m == model):
            return tokens_in / 1000 * inp + tokens_out / 1000 * out
    return None


class AgentOpsClient:
    """Client for AgentOps trace ingestion with buffering and retry logic."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8000",
        flush_interval: float = 5.0,
        flush_size: int = 50,
        offline_fallback: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff: float = 1.0,
    ):
        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.flush_interval = flush_interval
        self.flush_size = flush_size
        self.offline_fallback = offline_fallback
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

        self._buffer: list[dict] = []
        self._run_buffer: Optional[dict] = None
        self._lock = threading.Lock()
        self._current_run_id: Optional[uuid.UUID] = None
        self._flush_thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

        logger.info(f"AgentOps client initialized for {self.base_url}")

    def start_run(
        self,
        name: str | None = None,
        model_provider: str | None = None,
        model_name: str | None = None,
        metadata: dict | None = None,
    ) -> uuid.UUID:
        """Start a new run and return its UUID."""
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
        """End the current run and flush buffered data."""
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
        """Add a span to the buffer, auto-flush when buffer is full."""
        if not isinstance(span, dict):
            raise ValueError("Span must be a dictionary")
        with self._lock:
            self._buffer.append(span)
            if len(self._buffer) >= self.flush_size:
                self._do_flush()

    @property
    def current_run_id(self) -> uuid.UUID | None:
        """Return the current run ID, or None if no run is active."""
        return self._current_run_id

    def flush(self) -> None:
        """Flush buffered spans and run data to the API."""
        with self._lock:
            self._do_flush()

    def _do_flush(self) -> None:
        """Internal flush with exponential backoff retry."""
        if not self._buffer and not self._run_buffer:
            return

        payload = {
            "run": self._run_buffer,
            "spans": self._buffer[:],
        }
        self._buffer.clear()
        run_copy = self._run_buffer
        self._run_buffer = None

        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(
                        f"{self.base_url}/v1/traces/ingest",
                        json=payload,
                        headers={"X-API-Key": self.api_key},
                    )
                    resp.raise_for_status()
                logger.debug(f"Flushed {len(payload['spans'])} spans successfully")
                return
            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries:
                    self._handle_flush_error(e, payload, run_copy)
                    return
            except httpx.RequestError as e:
                logger.warning(f"Request error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries:
                    self._handle_flush_error(e, payload, run_copy)
                    return
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries:
                    self._handle_flush_error(e, payload, run_copy)
                    return

            if attempt < self.max_retries:
                time.sleep(self.retry_backoff * (2 ** attempt))

    def _handle_flush_error(
        self, error: Exception, payload: dict, run_copy: Optional[dict]
    ) -> None:
        """Handle flush failure: save to offline fallback or restore run buffer."""
        logger.error(f"Flush failed after {self.max_retries + 1} attempts: {error}")

        if self.offline_fallback:
            try:
                path = Path(self.offline_fallback)
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("a") as f:
                    f.write(json.dumps({
                        "error": str(error),
                        "payload": payload,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }) + "\n")
                logger.info(f"Saved failed payload to offline fallback: {path}")
            except Exception as fallback_error:
                logger.error(f"Failed to save to offline fallback: {fallback_error}")
        elif run_copy:
            self._run_buffer = run_copy
            logger.warning("Restored run buffer due to flush failure")

    def ingest_sync(self, run: dict | None, spans: list[dict]) -> None:
        """Synchronously ingest a run and its spans without buffering."""
        payload = {"run": run, "spans": spans}
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(
                f"{self.base_url}/v1/traces/ingest",
                json=payload,
                headers={"X-API-Key": self.api_key},
            )
            resp.raise_for_status()
