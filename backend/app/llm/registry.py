from app.llm.base import BaseLLMProvider
from app.llm.deepseek import DeepSeekProvider
from app.llm.kimi import KimiProvider
from app.llm.qwen import QwenProvider

_providers: dict[str, type[BaseLLMProvider]] = {}
_instances: dict[str, BaseLLMProvider] = {}

# 注册三种 Provider
_providers["deepseek"] = DeepSeekProvider  # 最优: Writer/Supervisor/Architect
_providers["kimi"] = KimiProvider          # 中等: Inspector
_providers["qwen"] = QwenProvider           # 轻量: Guardian/Custodian


def get_provider(name: str) -> BaseLLMProvider:
    if name not in _instances:
        if name not in _providers:
            raise ValueError(f"Unknown provider: {name}. Available: {list(_providers.keys())}")
        _instances[name] = _providers[name]()
    return _instances[name]


def list_providers() -> list[str]:
    return list(_providers.keys())

async def cleanup_providers():
    """Close all cached provider clients (call on app shutdown)."""
    for name, instance in _instances.items():
        try:
            await instance.close()
        except Exception:
            pass
    _instances.clear()
