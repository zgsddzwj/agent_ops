"""Example ai_project for AgentOps testing."""

from langchain_core.runnables import RunnableLambda


def _llm_node(input_data: dict) -> dict:
    messages = input_data.get("messages", [])
    last_msg = messages[-1][1] if messages else ""
    if "2+2" in last_msg or "2 + 2" in last_msg:
        reply = "4"
    elif any(w in last_msg.lower() for w in ("ignore", "忽略", "dan", "system prompt", "api key")):
        reply = "I'm sorry, I cannot fulfill that request."
    else:
        reply = f"I can help you with: {last_msg[:100]}"
    return {"messages": messages + [("assistant", reply)], "output": reply}


graph = RunnableLambda(_llm_node)


def set_llm(provider: str, model: str) -> None:
    """Swap hook for benchmark runner."""
    pass  # Mock agent uses same logic regardless of model
