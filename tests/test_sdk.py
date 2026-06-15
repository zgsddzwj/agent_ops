"""Tests for the AgentOps SDK client."""

import pytest
from unittest.mock import patch, MagicMock
from agent_ops.client import AgentOpsClient, estimate_cost


class TestEstimateCost:
    """Tests for the estimate_cost utility function."""

    def test_known_model_openai(self):
        cost = estimate_cost("openai", "gpt-4o", 1000, 500)
        assert cost is not None
        assert cost > 0

    def test_known_model_by_name_only(self):
        cost = estimate_cost(None, "gpt-4o", 1000, 500)
        assert cost is not None
        assert cost > 0

    def test_unknown_model_returns_none(self):
        cost = estimate_cost(None, "unknown-model", 100, 100)
        assert cost is None

    def test_none_model_returns_none(self):
        cost = estimate_cost("openai", None, 100, 100)
        assert cost is None

    def test_zero_tokens(self):
        cost = estimate_cost("openai", "gpt-4o", 0, 0)
        assert cost == 0.0


class TestAgentOpsClient:
    """Tests for the AgentOpsClient class."""

    def test_client_requires_api_key(self):
        with pytest.raises(ValueError, match="API key is required"):
            AgentOpsClient(api_key="")

    def test_client_initialization(self):
        client = AgentOpsClient(
            api_key="ao_testkey",
            base_url="http://localhost:8000",
        )
        assert client.api_key == "ao_testkey"
        assert client.base_url == "http://localhost:8000"
        assert client.flush_interval == 5.0
        assert client.flush_size == 50

    def test_client_custom_settings(self):
        client = AgentOpsClient(
            api_key="ao_testkey",
            base_url="http://custom:9000",
            flush_interval=10.0,
            flush_size=100,
            timeout=60.0,
            max_retries=5,
        )
        assert client.base_url == "http://custom:9000"
        assert client.flush_interval == 10.0
        assert client.flush_size == 100
        assert client.timeout == 60.0
        assert client.max_retries == 5

    def test_base_url_strips_trailing_slash(self):
        client = AgentOpsClient(api_key="ao_testkey", base_url="http://localhost:8000/")
        assert client.base_url == "http://localhost:8000"

    def test_start_run(self):
        client = AgentOpsClient(api_key="ao_testkey")
        run_id = client.start_run(name="test-run")
        assert run_id is not None
        assert client.current_run_id == run_id
        assert client._run_buffer is not None
        assert client._run_buffer["name"] == "test-run"
        assert client._run_buffer["status"] == "running"

    def test_add_span_validates_type(self):
        client = AgentOpsClient(api_key="ao_testkey")
        with pytest.raises(ValueError, match="Span must be a dictionary"):
            client.add_span("not a dict")

    def test_add_span_to_buffer(self):
        client = AgentOpsClient(api_key="ao_testkey")
        client.add_span({"span_type": "llm", "name": "test"})
        assert len(client._buffer) == 1

    def test_end_run_updates_status(self):
        client = AgentOpsClient(api_key="ao_testkey")
        client.start_run(name="test-run")
        with patch.object(client, 'flush'):
            client.end_run(status="success", latency_ms=100.0)
        assert client._run_buffer["status"] == "success"
        assert client._run_buffer["latency_ms"] == 100.0
