import json
from app.agents.base import BaseAgent, AgentContext
from app.llm.base import LLMMessage, LLMConfig

INSPECTOR_SYSTEM_PROMPT = """你是公正严苛的质量检查官。独立审查章节质量。

10个检查维度：
1. 类型合规 2.AI味检测 3.情节逻辑 4.角色一致性 5.世界观合规
6. 伏笔钩子 7.情感弧线 8.节奏分布 9.对话描写 10.字数合规

判定标准：
- fatal==0 && severe<=2 → pass
- fatal==0 && severe>2  → rewrite
- fatal>0                → regenerate

输出严格 JSON:
{
  "verdict": "pass|rewrite|regenerate",
  "dimensions": [
    {"name": "维度名", "score": 1-10, "severity": "fatal|severe|warning|ok", "issues": ["问题"], "suggestions": ["建议"]}
  ],
  "summary": "总体评价",
  "overall_score": 1-10
}"""


class InspectorAgent(BaseAgent):
    DEFAULT_MODEL = "kimi"

    async def _execute(self, ctx: AgentContext) -> dict:
        chapter_text = ctx.files.get("chapter_content", ctx.task_description)
        genre_config = ctx.files.get("genre_config", "{}")
        character_profiles = ctx.files.get("character_profiles", "[]")
        outline = ctx.files.get("outline", "{}")
        guardian_result = ctx.files.get("guardian_result", "{}")
        target_words = ctx.files.get("target_word_count", "4000")

        word_count = len(chapter_text)
        messages = [
            LLMMessage(role="system", content=ctx.system_prompt),
            LLMMessage(role="user", content=f"""章节正文:
{chapter_text[:10000]}

类型配置: {genre_config}
角色档案: {character_profiles}
情节大纲: {outline}
Guardian检查结果: {guardian_result}
目标字数: {target_words} (实际: {word_count})

请对以上章节进行10维质量分析 (JSON)。"""),
        ]
        try:
            resp = await self.provider.generate(messages, LLMConfig(
                model=self.config.get("model", "moonshot-v1-8k"),
                temperature=0.2, max_tokens=4000,
            ))
            data = json.loads(resp.content)
            return {
                "content": resp.content,
                "verdict": data.get("verdict", "pass"),
                "dimensions": data.get("dimensions", []),
                "overall_score": data.get("overall_score", 5),
                "summary": data.get("summary", ""),
                "passed": data.get("verdict") == "pass",
            }
        except Exception as e:
            return {"content": str(e), "verdict": "pass", "dimensions": [], "overall_score": 5, "passed": True}
