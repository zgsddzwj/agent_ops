"""Shared utilities for CLI and worker."""

from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ModelCandidate:
    provider: str
    model: str
    env_key: str | None = None


@dataclass
class ProjectManifest:
    project: str
    framework: str = "langchain"
    entrypoint: str = ""
    invoke_method: str = "invoke"
    input_key: str = "messages"
    input_format: str = "chat"
    env_file: str = ".env"
    eval_datasets: str = "./evals/"
    eval_suites: list[str] = field(default_factory=lambda: ["smoke", "regression"])
    swap_hook: str | None = None
    model_candidates: list[ModelCandidate] = field(default_factory=list)
    root_path: Path = field(default_factory=Path)

    @classmethod
    def load(cls, project_path: Path) -> "ProjectManifest":
        config_path = project_path / ".agent-ops.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"No .agent-ops.yaml found in {project_path}")

        with config_path.open() as f:
            data = yaml.safe_load(f) or {}

        invoke = data.get("invoke", {})
        eval_cfg = data.get("eval", {})
        models_cfg = data.get("models", {})
        candidates = []
        for c in models_cfg.get("candidates", []):
            candidates.append(
                ModelCandidate(
                    provider=c["provider"],
                    model=c["model"],
                    env_key=c.get("env_key"),
                )
            )

        return cls(
            project=data.get("project", project_path.name),
            framework=data.get("framework", "langchain"),
            entrypoint=data.get("entrypoint", ""),
            invoke_method=invoke.get("method", "invoke"),
            input_key=invoke.get("input_key", "messages"),
            input_format=invoke.get("input_format", "chat"),
            env_file=data.get("env_file", ".env"),
            eval_datasets=eval_cfg.get("datasets", "./evals/"),
            eval_suites=eval_cfg.get("suites", ["smoke", "regression"]),
            swap_hook=models_cfg.get("swap_hook"),
            model_candidates=candidates,
            root_path=project_path.resolve(),
        )

    def load_env(self) -> None:
        env_path = self.root_path / self.env_file
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

    def config_yaml(self) -> str:
        return (self.root_path / ".agent-ops.yaml").read_text()


DEFAULT_MANIFEST = """project: {name}
framework: langgraph
entrypoint: app.agent:graph
invoke:
  method: invoke
  input_key: messages
  input_format: chat
env_file: .env
eval:
  datasets: ./evals/
  suites: [smoke, regression, security]
models:
  swap_hook: app.agent:set_llm
  candidates:
    - provider: openai
      model: gpt-4o
      env_key: OPENAI_API_KEY
    - provider: openai
      model: gpt-4o-mini
    - provider: qwen
      model: qwen-plus
      env_key: DASHSCOPE_API_KEY
    - provider: qwen
      model: qwen-turbo
    - provider: deepseek
      model: deepseek-chat
      env_key: DEEPSEEK_API_KEY
    - provider: anthropic
      model: claude-sonnet-4-20250514
      env_key: ANTHROPIC_API_KEY
security:
  policies: ./security/policies.yaml
"""

DEFAULT_SMOKE_EVAL = """name: smoke
items:
  - input: "Hello, what can you help me with?"
    expected_behavior: respond
    metadata:
      category: greeting
  - input: "What is 2+2?"
    expected_output: "4"
    metadata:
      category: math
"""

DEFAULT_SECURITY_POLICY = """max_input_length: 32000
block_pii_in_output: true
rate_limit_per_minute: 60
"""


class AgentInvoker:
    def __init__(self, manifest: ProjectManifest):
        self.manifest = manifest
        self._agent = None

    def _load_agent(self) -> Any:
        if self._agent is not None:
            return self._agent
        if str(self.manifest.root_path) not in sys.path:
            sys.path.insert(0, str(self.manifest.root_path))
        module_path, _, attr = self.manifest.entrypoint.partition(":")
        if not attr:
            raise ValueError(f"Invalid entrypoint: {self.manifest.entrypoint}")
        module = importlib.import_module(module_path)
        self._agent = getattr(module, attr)
        return self._agent

    def swap_model(self, provider: str, model: str) -> None:
        if not self.manifest.swap_hook:
            return
        module_path, _, attr = self.manifest.swap_hook.partition(":")
        if str(self.manifest.root_path) not in sys.path:
            sys.path.insert(0, str(self.manifest.root_path))
        module = importlib.import_module(module_path)
        swap_fn = getattr(module, attr)
        swap_fn(provider, model)
        self._agent = None

    def build_input(self, text: str) -> Any:
        if self.manifest.input_format == "str":
            return text
        if self.manifest.input_format == "dict":
            return {self.manifest.input_key: text}
        return {self.manifest.input_key: [("user", text)]}

    def invoke(self, text: str, config: dict | None = None) -> tuple[Any, float | None]:
        import time

        agent = self._load_agent()
        input_data = self.build_input(text)
        start = time.perf_counter()
        method = getattr(agent, self.manifest.invoke_method, agent.invoke)
        result = method(input_data, config=config or {})
        latency_ms = (time.perf_counter() - start) * 1000
        return result, latency_ms

    def extract_output(self, result: Any) -> str:
        if isinstance(result, str):
            return result
        if isinstance(result, dict):
            for key in ("output", "answer", "content", "messages"):
                if key in result:
                    val = result[key]
                    if isinstance(val, str):
                        return val
                    if isinstance(val, list) and val:
                        last = val[-1]
                        if hasattr(last, "content"):
                            return str(last.content)
                        if isinstance(last, dict):
                            return str(last.get("content", last))
                        if isinstance(last, tuple):
                            return str(last[1])
        return str(result)


def load_dataset(path: Path) -> list[dict]:
    with path.open() as f:
        data = yaml.safe_load(f)
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Invalid dataset format: {path}")


def find_suite_dataset(suite_name: str, project_path: Path | None = None) -> Path | None:
    candidates = []
    if project_path:
        candidates.extend([
            project_path / "evals" / f"{suite_name}.yaml",
            project_path / "evals" / "suites" / f"{suite_name}.yaml",
        ])
    repo_root = Path(__file__).resolve().parents[3]
    candidates.extend([
        repo_root / "evals" / "suites" / f"{suite_name}.yaml",
        repo_root / "evals" / "datasets" / f"{suite_name}.yaml",
    ])
    for c in candidates:
        if c.exists():
            return c
    return None


def parse_models_arg(models_str: str) -> list[ModelCandidate]:
    result = []
    for part in models_str.split(","):
        part = part.strip()
        if ":" in part:
            provider, model = part.split(":", 1)
            result.append(ModelCandidate(provider=provider.strip(), model=model.strip()))
    return result
