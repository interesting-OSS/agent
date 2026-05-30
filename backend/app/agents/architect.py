import json
from app.agents.base import BaseAgent, AgentContext
from app.llm.base import LLMMessage, LLMConfig

ARCHITECT_SYSTEM_PROMPT = """你是情节逻辑的守护者。
每次新章节需要你审查：
1. 前面章节的情节因果链是否完整
2. 所有未解决伏笔的状态（哪些该在本章处理）
3. 本章大纲在时间线上是否合理
4. 本应考虑但可能遗漏的关键事件

输出严格 JSON:
{
  "causality": {"status": "ok|broken", "issues": ["问题描述"]},
  "foreshadow_reminders": [{"id": "...", "title": "...", "urgency": "must_resolve|overdue|upcoming"}],
  "key_events_this_chapter": ["应在本章发生的事件"],
  "conflict_priority": ["建议优先解决的冲突"],
  "continuity_notes": "连续性问题备注",
  "summary": "一句话情节评估"
}"""


class ArchitectAgent(BaseAgent):
    DEFAULT_MODEL = "deepseek-chat"

    async def _execute(self, ctx: AgentContext) -> dict:
        # 从 files 提取上下文
        outline = ctx.files.get("outline", "{}")
        previous_summaries = ctx.files.get("previous_summaries", "[]")
        foreshadows = ctx.files.get("foreshadows", "[]")
        chapter_plan = ctx.files.get("chapter_plan", ctx.task_description)

        messages = [
            LLMMessage(role="system", content=ctx.system_prompt),
            LLMMessage(role="user", content=f"""本章大纲:
{chapter_plan}

前文摘要:
{previous_summaries}

活跃伏笔:
{foreshadows}

请生成 PreFlight 报告 (JSON)。"""),
        ]
        try:
            resp = await self.provider.generate(messages, LLMConfig(
                model=self.config.get("model", self.DEFAULT_MODEL),
                temperature=0.3, max_tokens=3000,
            ))
            return {"content": resp.content, "report": json.loads(resp.content), "passed": True}
        except Exception as e:
            return {"content": str(e), "report": {}, "passed": False}
