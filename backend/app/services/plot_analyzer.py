"""10维章节分析 — Inspector Agent 的支撑服务"""
import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents import get_agent
from app.llm.base import BaseLLMProvider


async def analyze_chapter(novel_id: str, chapter_id: str, content: str,
                          genre_config: str = "{}", character_profiles: str = "[]",
                          outline: str = "{}", target_words: str = "4000",
                          db: AsyncSession | None = None) -> dict:
    """调用 Inspector Agent，执行10维分析"""
    inspector = get_agent("inspector")
    if not inspector:
        return {"verdict": "pass", "error": "Inspector agent not available"}

    result = await inspector.run(
        task=content,
        files={
            "chapter_content": content,
            "genre_config": genre_config,
            "character_profiles": character_profiles,
            "outline": outline,
            "guardian_result": "{}",
            "target_word_count": target_words,
        }
    )
    return {
        "verdict": result.get("verdict", "pass"),
        "dimensions": result.get("dimensions", []),
        "overall_score": result.get("overall_score", 5),
        "summary": result.get("summary", ""),
        "raw": result.get("content", ""),
    }
