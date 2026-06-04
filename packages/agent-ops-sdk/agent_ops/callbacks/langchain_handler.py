import time
import uuid
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from agent_ops.client import AgentOpsClient, estimate_cost


class AgentOpsCallbackHandler(BaseCallbackHandler):
    """LangChain callback handler for AgentOps trace ingestion."""

    def __init__(self, client: AgentOpsClient, run_name: str | None = None):
        super().__init__()
        self.client = client
        self.run_name = run_name
        self._run_id: UUID | None = None
        self._span_starts: dict[str, float] = {}
        self._llm_starts: dict[str, float] = {}
        self._llm_first_token: dict[str, float] = {}
        self._llm_token_counts: dict[str, int] = {}
        self._run_start: float | None = None
        self._total_tokens = 0
        self._total_cost = 0.0
        self._min_ttft: float | None = None

    def _ensure_run(self) -> UUID:
        if self._run_id is None:
            self._run_start = time.perf_counter()
            self._run_id = self.client.start_run(name=self.run_name)
        return self._run_id

    def _span_id(self, run_id: UUID) -> str:
        return str(run_id)

    def on_llm_start(self, serialized: dict, prompts: list[str], *, run_id: UUID, **kwargs: Any) -> None:
        self._ensure_run()
        key = self._span_id(run_id)
        self._llm_starts[key] = time.perf_counter()
        self._llm_token_counts[key] = 0

    def on_llm_new_token(self, token: str, *, run_id: UUID, **kwargs: Any) -> None:
        key = self._span_id(run_id)
        if key not in self._llm_first_token:
            self._llm_first_token[key] = time.perf_counter()
        self._llm_token_counts[key] = self._llm_token_counts.get(key, 0) + 1

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> None:
        run_uuid = self._ensure_run()
        key = self._span_id(run_id)
        start = self._llm_starts.pop(key, time.perf_counter())
        end = time.perf_counter()
        latency_ms = (end - start) * 1000

        ttft_ms = None
        tokens_per_sec = None
        if key in self._llm_first_token:
            ttft_ms = (self._llm_first_token.pop(key) - start) * 1000
            if self._min_ttft is None or ttft_ms < self._min_ttft:
                self._min_ttft = ttft_ms
            gen_time = end - self._llm_first_token.get(key, end)
            out_tokens = self._llm_token_counts.pop(key, 0)
            if gen_time > 0 and out_tokens > 0:
                tokens_per_sec = out_tokens / gen_time
        else:
            self._llm_token_counts.pop(key, None)

        tokens_in = tokens_out = 0
        model = provider = None
        output_text = None

        if response.llm_output:
            model = response.llm_output.get("model_name") or response.llm_output.get("model")
            token_usage = response.llm_output.get("token_usage") or {}
            tokens_in = token_usage.get("prompt_tokens", 0)
            tokens_out = token_usage.get("completion_tokens", 0) or self._llm_token_counts.get(key, 0)

        if response.generations and response.generations[0]:
            gen = response.generations[0][0]
            output_text = gen.text if hasattr(gen, "text") else str(gen)

        if model and "gpt" in model.lower():
            provider = "openai"
        elif model and "qwen" in model.lower():
            provider = "qwen"
        elif model and "deepseek" in model.lower():
            provider = "deepseek"
        elif model and "claude" in model.lower():
            provider = "anthropic"

        cost = estimate_cost(provider, model, tokens_in, tokens_out)
        if cost:
            self._total_cost += cost
        self._total_tokens += tokens_in + tokens_out

        self.client.add_span(
            {
                "run_id": str(run_uuid),
                "span_type": "llm",
                "name": model or "llm",
                "input": {"prompts": kwargs.get("prompts")},
                "output": {"text": output_text},
                "model": model,
                "provider": provider,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "latency_ms": latency_ms,
                "ttft_ms": ttft_ms,
                "tokens_per_sec": tokens_per_sec,
                "cost_usd": cost,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "ended_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    def on_llm_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        run_uuid = self._ensure_run()
        self.client.add_span(
            {
                "run_id": str(run_uuid),
                "span_type": "llm",
                "name": "llm",
                "status": "error",
                "error": str(error),
            }
        )

    def on_tool_start(self, serialized: dict, input_str: str, *, run_id: UUID, **kwargs: Any) -> None:
        self._ensure_run()
        self._span_starts[self._span_id(run_id)] = time.perf_counter()

    def on_tool_end(self, output: str, *, run_id: UUID, **kwargs: Any) -> None:
        run_uuid = self._ensure_run()
        key = self._span_id(run_id)
        start = self._span_starts.pop(key, time.perf_counter())
        latency_ms = (time.perf_counter() - start) * 1000
        tool_name = kwargs.get("name") or "tool"
        self.client.add_span(
            {
                "run_id": str(run_uuid),
                "span_type": "tool",
                "name": tool_name,
                "input": {"input": kwargs.get("inputs")},
                "output": {"output": str(output)[:2000]},
                "latency_ms": latency_ms,
            }
        )

    def on_chain_start(self, serialized: dict, inputs: dict, *, run_id: UUID, **kwargs: Any) -> None:
        self._ensure_run()
        self._span_starts[self._span_id(run_id)] = time.perf_counter()

    def on_chain_end(self, outputs: dict, *, run_id: UUID, **kwargs: Any) -> None:
        run_uuid = self._ensure_run()
        key = self._span_id(run_id)
        start = self._span_starts.pop(key, None)
        latency_ms = (time.perf_counter() - start) * 1000 if start else None
        name = kwargs.get("name") or (serialized.get("name") if (serialized := kwargs.get("serialized")) else "chain")
        self.client.add_span(
            {
                "run_id": str(run_uuid),
                "span_type": "chain",
                "name": name,
                "output": {"outputs": str(outputs)[:2000]} if outputs else None,
                "latency_ms": latency_ms,
            }
        )

    def on_chain_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        self._ensure_run()
        self.client.end_run(status="error", error=str(error))
        self.client.flush()

    def flush_run(self, status: str = "success") -> None:
        latency_ms = None
        if self._run_start:
            latency_ms = (time.perf_counter() - self._run_start) * 1000
        self.client.end_run(
            status=status,
            latency_ms=latency_ms,
            ttft_ms=self._min_ttft,
            total_tokens=self._total_tokens,
            cost_usd=self._total_cost or None,
        )
