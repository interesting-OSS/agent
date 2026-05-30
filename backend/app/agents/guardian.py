from app.agents.base import BaseAgent, AgentContext
from app.agents.tools.guard_tools import scan_forbidden_terms, mark_issues
from app.llm.base import LLMMessage, LLMConfig


GUARDIAN_SYSTEM_PROMPT = """你是类型合规的终极守卫者。
你的唯一工作：检查文本是否严格遵守了类型规则。
- 你不关心文字好不好看
- 你不关心情节有没有漏洞
- 你只关心：文本中是否出现了禁止术语？

输出 JSON:
{
  "violations": [
    {"term": "违规词", "position": 1234, "context": "...", "severity": "fatal"}
  ],
  "passed": true/false
}"""


class GuardianAgent(BaseAgent):
    DEFAULT_MODEL = "qwen-turbo"

    async def _execute(self, ctx: AgentContext) -> dict:
        # 解析任务：从 ctx.files 中获取类型配置和待检查文本
        genre_config = ctx.files.get("genre_config", "{}")
        text = ctx.task_description

        # 解析 forbidden_terms
        import json
        try:
            config = json.loads(genre_config) if isinstance(genre_config, str) else genre_config
        except json.JSONDecodeError:
            config = {}
        forbidden_terms = config.get("forbidden_terms", {}).get("terms", [])

        # 策略1：机械扫描（快速、准确、零幻觉）
        violations = scan_forbidden_terms(text, forbidden_terms)

        # 策略2：如果机械扫描通过但文本较长，用 LLM 做语义检查
        if not violations and len(text) > 5000:
            violations = await self._llm_scan(text, config)

        return {
            "content": mark_issues(violations),
            "violations": violations,
            "passed": len(violations) == 0,
        }

    async def _llm_scan(self, text: str, config: dict) -> list[dict]:
        """语义扫描——检测间接违规（如同义词替换）"""
        forbidden = config.get("forbidden_terms", {}).get("terms", [])
        if not forbidden:
            return []

        messages = [
            LLMMessage(role="system", content=GUARDIAN_SYSTEM_PROMPT),
            LLMMessage(role="user", content=f"""检查以下文本，看是否出现这些禁止术语或它们的同义替换：
禁止术语: {", ".join(forbidden)}

待检查文本:
{text[:8000]}"""),
        ]
        try:
            resp = await self.provider.generate(messages, LLMConfig(
                model=self.config.get("model", self.DEFAULT_MODEL),
                temperature=0.0,
                max_tokens=2000,
            ))
            import json
            data = json.loads(resp.content)
            return data.get("violations", [])
        except Exception:
            return []
