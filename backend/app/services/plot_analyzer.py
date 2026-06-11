"""10维章节分析 — Inspector Agent 的支撑服务（已迁移到 LangGraph）"""
import json

from langchain_core.messages import HumanMessage

from app.langgraph.agents import create_agent_instance


async def analyze_chapter(novel_id: str, chapter_id: str, content: str,
                          genre_config: str = "{}", character_profiles: str = "[]",
                          outline: str = "{}", target_words: str = "4000",
                          db=None) -> dict:
    """调用 Inspector Agent，执行10维分析"""
    inspector = create_agent_instance("inspector")

    prompt = f"""章节正文:
{content[:10000]}

类型配置: {genre_config}
角色档案: {character_profiles}
情节大纲: {outline}
Guardian检查结果: {{}}
目标字数: {target_words} (实际: {len(content)})

请对以上章节进行10维质量分析 (JSON)。"""

    result = await inspector.ainvoke({"messages": [HumanMessage(content=prompt)]})
    msgs = result.get("messages", [])
    last_content = ""
    for m in reversed(msgs):
        if hasattr(m, "content") and m.content and m.type == "ai":
            last_content = m.content
            break

    try:
        data = json.loads(last_content)
    except json.JSONDecodeError:
        data = {"verdict": "pass", "summary": last_content[:200]}

    return {
        "verdict": data.get("verdict", "pass"),
        "dimensions": data.get("dimensions", []),
        "overall_score": data.get("overall_score", 5),
        "summary": data.get("summary", ""),
        "raw": last_content,
    }
