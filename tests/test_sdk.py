import pytest
from agent_ops.client import estimate_cost


def test_estimate_cost_openai():
    cost = estimate_cost("openai", "gpt-4o", 1000, 500)
    assert cost is not None
    assert cost > 0


def test_estimate_cost_unknown():
    cost = estimate_cost(None, "unknown-model", 100, 100)
    assert cost is None
