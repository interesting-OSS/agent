import json
from app.agents.base import BaseAgent, AgentContext
from app.llm.base import LLMMessage, LLMConfig

CUSTODIAN_SYSTEM_PROMPT = """你是角色一致性的守护者。
你的工作：
- 检查每个登场角色的行为是否符合其6层模型（世界观/自我认同/价值观/能力/技能/环境）
- 检查对话是否符合角色声音
- 检查职业阶段限制是否被遵守
- 预测本章角色心理状态变化

你不关心情节是否精彩，只关心角色是否演"歪"了。

输出严格 JSON:
{
  "consistency_issues": [
    {"character": "角色名", "issue": "问题描述", "severity": "severe/warning", "layer_violated": "layer1-6"}
  ],
  "voice_issues": [
    {"character": "角色名", "issue": "对话不符合角色设定", "example": "违反的台词"}
  ],
  "career_issues": [
    {"character": "角色名", "issue": "超出职业阶段能力范围"}
  ],
  "state_predictions": [
    {"character": "角色名", "predicted_emotion": "...", "predicted_location": "...", "knowledge_update": "..."}
  ],
  "summary": "一句话总结角色一致性情况"
}"""


class CustodianAgent(BaseAgent):
    DEFAULT_MODEL = "qwen-turbo"

    async def _execute(self, ctx: AgentContext) -> dict:
        # 从 files 提取角色档案
        character_profiles = ctx.files.get("character_profiles", "[]")
        chapter_text = ctx.task_description

        try:
            profiles = json.loads(character_profiles) if isinstance(character_profiles, str) else character_profiles
        except json.JSONDecodeError:
            profiles = []

        if not profiles:
            return {"content": "无角色档案，跳过检查", "issues": [], "passed": True}

        messages = [
            LLMMessage(role="system", content=ctx.system_prompt),
            LLMMessage(role="user", content=f"""角色档案:
{json.dumps(profiles, ensure_ascii=False, indent=2)}

章节正文:
{chapter_text[:6000]}

请检查角色一致性并输出 JSON。"""),
        ]

        try:
            resp = await self.provider.generate(messages, LLMConfig(
                model=self.config.get("model", self.DEFAULT_MODEL),
                temperature=0.1,
                max_tokens=3000,
            ))
            data = json.loads(resp.content)
            issues = (
                data.get("consistency_issues", []) +
                data.get("voice_issues", []) +
                data.get("career_issues", [])
            )
            return {
                "content": resp.content,
                "issues": issues,
                "state_predictions": data.get("state_predictions", []),
                "passed": len(issues) == 0,
            }
        except Exception as e:
            return {"content": f"Custodian check error: {e}", "issues": [], "passed": True}
