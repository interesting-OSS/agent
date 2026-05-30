import yaml
from pathlib import Path

GENRE_DIR = Path(__file__).parent / "configs"
_cache: dict[str, dict] = {}


def load_genre_config(genre_id: str) -> dict:
    if genre_id in _cache:
        return _cache[genre_id]

    path = GENRE_DIR / f"{genre_id}.yaml"
    if not path.exists():
        raise ValueError(f"Unknown genre: {genre_id}. Available: {list_available_genres()}")

    with open(path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    _cache[genre_id] = config
    return config


def list_available_genres() -> list[str]:
    return [p.stem for p in GENRE_DIR.glob("*.yaml")]


def get_genre_constraint_summary(genre_id: str) -> str:
    """生成约束摘要，用于注入 Writer 的 <constraints>[P0]"""
    config = load_genre_config(genre_id)
    terms = "、".join(config.get("forbidden_terms", {}).get("terms", []))
    return f"""禁止术语（绝对不用）：{terms}

文风要求：
{config.get('prompt_segment', '')}

类型禁忌：
{chr(10).join(f'- {t}' for t in config.get('taboos', []))}
"""


def reload_cache():
    """清除缓存，重新加载所有配置"""
    _cache.clear()
