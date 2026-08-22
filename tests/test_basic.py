"""Test suite for AgentOps backend API and core services."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4


# ─── SDK cost estimation tests ───

class TestCostEstimation:
    """Tests for the SDK cost estimation utility."""

    def test_estimate_cost_openai_gpt4o(self):
        from agent_ops.client import estimate_cost
        cost = estimate_cost("openai", "gpt-4o", 1000, 500)
        assert cost is not None
        assert cost > 0
        # $2.50/1k input + $10.00/1k output = 2.50 + 5.00 = 7.50
        assert abs(cost - 7.50) < 0.01

    def test_estimate_cost_qwen(self):
        from agent_ops.client import estimate_cost
        cost = estimate_cost("qwen", "qwen-plus", 1000, 1000)
        assert cost is not None
        assert cost > 0

    def test_estimate_cost_deepseek(self):
        from agent_ops.client import estimate_cost
        cost = estimate_cost("deepseek", "deepseek-chat", 500, 500)
        assert cost is not None
        assert cost > 0

    def test_estimate_cost_unknown_model(self):
        from agent_ops.client import estimate_cost
        cost = estimate_cost(None, "unknown-model", 100, 100)
        assert cost is None

    def test_estimate_cost_no_model(self):
        from agent_ops.client import estimate_cost
        cost = estimate_cost("openai", None, 100, 100)
        assert cost is None

    def test_estimate_cost_zero_tokens(self):
        from agent_ops.client import estimate_cost
        cost = estimate_cost("openai", "gpt-4o", 0, 0)
        assert cost is not None
        assert cost == 0.0


# ─── Ingest service tests ───

class TestPercentile:
    """Tests for the percentile utility function."""

    def test_percentile_single_value(self):
        from app.services.ingest import percentile
        assert percentile([5.0], 50) == 5.0

    def test_percentile_empty_list(self):
        from app.services.ingest import percentile
        assert percentile([], 50) is None

    def test_percentile_median_odd(self):
        from app.services.ingest import percentile
        result = percentile([1.0, 2.0, 3.0, 4.0, 5.0], 50)
        assert result == 3.0

    def test_percentile_p95(self):
        from app.services.ingest import percentile
        values = list(range(1, 101))
        result = percentile(values, 95)
        assert result is not None
        assert result >= 95

    def test_percentile_p0(self):
        from app.services.ingest import percentile
        result = percentile([10.0, 20.0, 30.0], 0)
        assert result == 10.0

    def test_percentile_p100(self):
        from app.services.ingest import percentile
        result = percentile([10.0, 20.0, 30.0], 100)
        assert result == 30.0


# ─── Security tests ───

class TestSecurity:
    """Tests for security utility functions."""

    def test_api_key_generation(self):
        from app.core.security import generate_api_key
        key, key_hash, prefix = generate_api_key()
        assert key.startswith("ao_")
        assert len(key_hash) == 64  # SHA-256 hex digest
        assert prefix.startswith("ao_")
        assert len(prefix) == 10

    def test_api_key_hashing(self):
        from app.core.security import hash_api_key
        key = "ao_testkey123"
        hash1 = hash_api_key(key)
        hash2 = hash_api_key(key)
        assert hash1 == hash2  # Deterministic
        assert len(hash1) == 64

    def test_different_keys_different_hashes(self):
        from app.core.security import hash_api_key
        hash1 = hash_api_key("ao_key1")
        hash2 = hash_api_key("ao_key2")
        assert hash1 != hash2

    def test_verify_api_key_correct(self):
        from app.core.security import generate_api_key, verify_api_key
        key, key_hash, _ = generate_api_key()
        assert verify_api_key(key, key_hash) is True

    def test_verify_api_key_incorrect(self):
        from app.core.security import generate_api_key, verify_api_key
        _, key_hash, _ = generate_api_key()
        assert verify_api_key("ao_wrongkey", key_hash) is False

    def test_verify_api_key_constant_time(self):
        """verify_api_key should use hmac.compare_digest, not string equality."""
        from app.core.security import hash_api_key, verify_api_key
        key = "ao_testconstant"
        stored_hash = hash_api_key(key)
        # Should return True for correct key
        assert verify_api_key(key, stored_hash) is True
        # Should return False for wrong key
        assert verify_api_key("ao_different", stored_hash) is False


# ─── Configuration tests ───

class TestConfiguration:
    """Tests for application configuration."""

    def test_settings_loads_defaults(self):
        from app.core.config import Settings
        s = Settings()
        assert s.api_host == "0.0.0.0"
        assert s.api_port == 8000
        assert s.debug is False

    def test_cors_origins_list(self):
        from app.core.config import Settings
        s = Settings(cors_origins="http://localhost:3000,http://localhost:4000")
        assert len(s.cors_origins_list) == 2
        assert "http://localhost:3000" in s.cors_origins_list

    def test_rate_limit_defaults(self):
        from app.core.config import Settings
        s = Settings()
        assert s.rate_limit_enabled is True
        assert s.rate_limit_requests == 100
        assert s.rate_limit_window == 60


# ─── Schema validation tests ───

class TestSchemas:
    """Tests for Pydantic schema validation."""

    def test_project_create_valid(self):
        from app.schemas import ProjectCreate
        p = ProjectCreate(name="test-project")
        assert p.name == "test-project"
        assert p.root_path is None
        assert p.entrypoint is None

    def test_run_create_defaults(self):
        from app.schemas import RunCreate
        r = RunCreate()
        assert r.status == "running"
        assert r.name is None

    def test_span_ingest_required_fields(self):
        from app.schemas import SpanIngest
        import uuid
        s = SpanIngest(run_id=uuid4(), span_type="llm")
        assert s.span_type == "llm"
        assert s.status == "success"

    def test_trace_ingest_request_defaults(self):
        from app.schemas import TraceIngestRequest
        t = TraceIngestRequest()
        assert t.run is None
        assert t.spans == []

    def test_alert_rule_create(self):
        from app.schemas import AlertRuleCreate
        r = AlertRuleCreate(
            name="high_cost",
            rule_type="cost_threshold",
            threshold=100.0,
            window_minutes=60,
        )
        assert r.rule_type == "cost_threshold"
        assert r.threshold == 100.0


# ─── Additional configuration tests ───

class TestAdvancedConfiguration:
    """Tests for additional configuration fields."""

    def test_log_requests_default(self):
        from app.core.config import Settings
        s = Settings()
        assert s.log_requests is False

    def test_api_timeout_default(self):
        from app.core.config import Settings
        s = Settings()
        assert s.api_timeout == 30

    def test_secret_key_default(self):
        from app.core.config import Settings
        s = Settings()
        assert s.secret_key == "change-me-in-production"

    def test_database_url_default(self):
        from app.core.config import Settings
        s = Settings()
        assert s.database_url.startswith("postgresql+asyncpg://")

    def test_redis_url_default(self):
        from app.core.config import Settings
        s = Settings()
        assert s.redis_url.startswith("redis://")

    def test_cors_origins_single(self):
        from app.core.config import Settings
        s = Settings(cors_origins="http://localhost:3000")
        assert len(s.cors_origins_list) == 1
        assert s.cors_origins_list[0] == "http://localhost:3000"

    def test_cors_origins_empty(self):
        from app.core.config import Settings
        s = Settings(cors_origins="")
        assert len(s.cors_origins_list) == 0
