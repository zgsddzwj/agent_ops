"""LLM provider registry for benchmarks."""

from dataclasses import dataclass


@dataclass
class ProviderConfig:
    provider: str
    default_env_key: str
    langchain_class: str | None = None


PROVIDERS = {
    "openai": ProviderConfig("openai", "OPENAI_API_KEY", "langchain_openai.ChatOpenAI"),
    "qwen": ProviderConfig("qwen", "DASHSCOPE_API_KEY", "langchain_community.chat_models.ChatTongyi"),
    "deepseek": ProviderConfig("deepseek", "DEEPSEEK_API_KEY", "langchain_openai.ChatOpenAI"),
    "anthropic": ProviderConfig("anthropic", "ANTHROPIC_API_KEY", "langchain_anthropic.ChatAnthropic"),
    "zhipu": ProviderConfig("zhipu", "ZHIPUAI_API_KEY", "langchain_community.chat_models.ChatZhipuAI"),
}


def get_provider(name: str) -> ProviderConfig | None:
    return PROVIDERS.get(name)
