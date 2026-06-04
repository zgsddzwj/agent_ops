from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str
    root_path: str | None = None
    entrypoint: str | None = None
    config_yaml: str | None = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    root_path: str | None
    entrypoint: str | None
    api_key_prefix: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectCreateResponse(ProjectResponse):
    api_key: str


class ProjectConfigUpdate(BaseModel):
    config_yaml: str


class RunCreate(BaseModel):
    id: UUID | None = None
    name: str | None = None
    status: str = "running"
    model_provider: str | None = None
    model_name: str | None = None
    metadata: dict | None = None


class RunUpdate(BaseModel):
    status: str | None = None
    latency_ms: float | None = None
    ttft_ms: float | None = None
    total_tokens: int | None = None
    cost_usd: float | None = None
    error: str | None = None


class SpanIngest(BaseModel):
    id: UUID | None = None
    run_id: UUID
    parent_id: UUID | None = None
    span_type: str
    name: str | None = None
    input: dict | None = None
    output: dict | None = None
    model: str | None = None
    provider: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    latency_ms: float | None = None
    ttft_ms: float | None = None
    tokens_per_sec: float | None = None
    cost_usd: float | None = None
    status: str = "success"
    error: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None


class TraceIngestRequest(BaseModel):
    run: RunCreate | None = None
    spans: list[SpanIngest] = Field(default_factory=list)


class RunResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str | None
    status: str
    model_provider: str | None
    model_name: str | None
    latency_ms: float | None
    ttft_ms: float | None
    total_tokens: int | None
    cost_usd: float | None
    error: str | None
    created_at: datetime
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class SpanResponse(BaseModel):
    id: UUID
    run_id: UUID
    parent_id: UUID | None
    span_type: str
    name: str | None
    input_json: dict | None
    output_json: dict | None
    model: str | None
    provider: str | None
    tokens_in: int | None
    tokens_out: int | None
    latency_ms: float | None
    ttft_ms: float | None
    tokens_per_sec: float | None
    cost_usd: float | None
    status: str
    error: str | None
    started_at: datetime | None
    ended_at: datetime | None

    model_config = {"from_attributes": True}


class MetricsSummary(BaseModel):
    total_runs: int
    error_rate: float
    total_cost_usd: float
    total_tokens: int
    avg_latency_ms: float | None
    p50_latency_ms: float | None
    p95_latency_ms: float | None
    p50_ttft_ms: float | None
    p95_ttft_ms: float | None


class TimeseriesPoint(BaseModel):
    bucket: datetime
    run_count: int
    total_cost_usd: float
    avg_latency_ms: float | None
    p95_latency_ms: float | None
    model_provider: str | None = None
    model_name: str | None = None


class EvalRunCreate(BaseModel):
    dataset_id: UUID | None = None
    suite_name: str | None = None
    baseline_id: UUID | None = None
    items: list[dict] | None = None


class EvalRunResponse(BaseModel):
    id: UUID
    project_id: UUID
    dataset_id: UUID | None
    suite_name: str | None
    status: str
    summary_json: dict | None
    created_at: datetime
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class EvalResultResponse(BaseModel):
    id: UUID
    input_text: str
    output_text: str | None
    score: float | None
    passed: bool | None
    metrics_json: dict | None
    latency_ms: float | None
    cost_usd: float | None
    error: str | None

    model_config = {"from_attributes": True}


class BenchmarkCreate(BaseModel):
    models: list[dict]
    dataset_id: UUID | None = None
    items: list[dict] | None = None
    repeat_count: int = 3


class BenchmarkResponse(BaseModel):
    id: UUID
    project_id: UUID
    models_json: list
    repeat_count: int
    status: str
    summary_json: dict | None
    created_at: datetime
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class SecurityScanCreate(BaseModel):
    suite_name: str | None = "prompt_injection"


class SecurityScanResponse(BaseModel):
    id: UUID
    project_id: UUID
    suite_name: str | None
    status: str
    pass_rate: float | None
    summary_json: dict | None
    created_at: datetime
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class AlertRuleCreate(BaseModel):
    name: str
    rule_type: str
    threshold: float
    window_minutes: int = 60
    webhook_url: str | None = None


class AlertRuleResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    rule_type: str
    threshold: float
    window_minutes: int
    webhook_url: str | None
    enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertEventResponse(BaseModel):
    id: UUID
    rule_id: UUID
    message: str
    value: float | None
    acknowledged: bool
    created_at: datetime

    model_config = {"from_attributes": True}
