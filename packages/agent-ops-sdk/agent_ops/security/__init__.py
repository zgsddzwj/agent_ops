import re
import time
from collections.abc import Callable
from typing import Any


INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above)\s+instructions",
    r"disregard\s+(your|the)\s+(system|instructions)",
    r"you\s+are\s+now\s+(DAN|jailbreak)",
    r"输出\s*system\s*prompt",
    r"忽略(以上|上面|之前)(的)?指令",
]

PII_PATTERNS = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
    (r"\b\d{16}\b", "[CARD]"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]"),
]


class InputSanitizer:
    def __init__(self, max_length: int = 32000, block_patterns: list[str] | None = None):
        self.max_length = max_length
        self.patterns = [re.compile(p, re.I) for p in (block_patterns or INJECTION_PATTERNS)]

    def check(self, text: str) -> tuple[bool, str | None]:
        if len(text) > self.max_length:
            return False, "Input exceeds max length"
        for p in self.patterns:
            if p.search(text):
                return False, f"Blocked pattern matched: {p.pattern}"
        return True, None


class PromptInjectionDetector:
    def __init__(self, threshold: float = 0.8):
        self.threshold = threshold

    def score(self, text: str) -> float:
        hits = sum(1 for p in INJECTION_PATTERNS if re.search(p, text, re.I))
        return min(1.0, hits * 0.4)

    def check(self, text: str) -> tuple[bool, str | None]:
        score = self.score(text)
        if score >= self.threshold:
            return False, f"Prompt injection detected (score={score:.2f})"
        return True, None


class OutputFilter:
    def __init__(self, block_pii: bool = True):
        self.block_pii = block_pii

    def filter(self, text: str) -> str:
        if not self.block_pii:
            return text
        result = text
        for pattern, replacement in PII_PATTERNS:
            result = re.sub(pattern, replacement, result)
        return result


class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self._timestamps: list[float] = []

    def check(self) -> tuple[bool, str | None]:
        now = time.time()
        self._timestamps = [t for t in self._timestamps if now - t < 60]
        if len(self._timestamps) >= self.requests_per_minute:
            return False, "Rate limit exceeded"
        self._timestamps.append(now)
        return True, None


class SecurityPipeline:
    """Wrap a LangChain Runnable with security checks."""

    def __init__(self, middlewares: list[Any] | None = None):
        self.middlewares = middlewares or [
            InputSanitizer(),
            PromptInjectionDetector(threshold=0.8),
            OutputFilter(block_pii=True),
            RateLimiter(requests_per_minute=60),
        ]
        self._audit_callback: Callable[[str, str, str], None] | None = None

    def on_block(self, callback: Callable[[str, str, str], None]) -> "SecurityPipeline":
        self._audit_callback = callback
        return self

    def _audit(self, event_type: str, input_text: str, reason: str) -> None:
        if self._audit_callback:
            self._audit_callback(event_type, input_text, reason)

    def _extract_input(self, input_data: Any) -> str:
        if isinstance(input_data, str):
            return input_data
        if isinstance(input_data, dict):
            for key in ("messages", "input", "query", "question"):
                if key in input_data:
                    val = input_data[key]
                    if isinstance(val, str):
                        return val
                    if isinstance(val, list) and val:
                        last = val[-1]
                        if isinstance(last, tuple):
                            return str(last[1])
                        if isinstance(last, dict):
                            return str(last.get("content", last))
                        return str(last)
        return str(input_data)

    def wrap(self, runnable: Any) -> "_SecuredRunnable":
        return _SecuredRunnable(runnable, self)


class _SecuredRunnable:
    def __init__(self, runnable: Any, pipeline: SecurityPipeline):
        self.runnable = runnable
        self.pipeline = pipeline

    def invoke(self, input_data: Any, config: dict | None = None, **kwargs: Any) -> Any:
        text = self.pipeline._extract_input(input_data)
        for mw in self.pipeline.middlewares:
            if hasattr(mw, "check"):
                if mw.__class__.__name__ == "RateLimiter":
                    ok, reason = mw.check()
                else:
                    ok, reason = mw.check(text)
                if not ok:
                    self.pipeline._audit("blocked", text, reason or "blocked")
                    raise SecurityError(reason or "Request blocked by security pipeline")

        result = self.runnable.invoke(input_data, config=config, **kwargs)

        for mw in self.pipeline.middlewares:
            if isinstance(mw, OutputFilter):
                if isinstance(result, str):
                    result = mw.filter(result)
                elif isinstance(result, dict) and "output" in result:
                    result["output"] = mw.filter(str(result["output"]))
        return result

    def ainvoke(self, input_data: Any, config: dict | None = None, **kwargs: Any) -> Any:
        return self.invoke(input_data, config=config, **kwargs)


class SecurityError(Exception):
    pass
