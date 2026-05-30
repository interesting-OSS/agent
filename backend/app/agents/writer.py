import json
from app.agents.base import BaseAgent, AgentContext
from app.llm.base import LLMMessage, LLMConfig

WRITER_SYSTEM_PROMPT = """你是一流的小说写手。你只负责根据写作计划写出精彩的章节正文。

你的上下文中包含了完整的写作计划、类型约束、角色参考和前文锚点。

注意事项：
- 你只负责写，不负责检查——检查是Guardian和Inspector的事
- 严格遵守[constraints]中的禁止术语列表，一字不漏
- 按照类型文风蓝图来写——西幻用西幻的味，仙侠用仙侠的味
- 确保章末有一个有效的钩子
- 目标字数在写作计划的 target_word_count 中指定"""


class WriterAgent(BaseAgent):
    DEFAULT_MODEL = "deepseek-chat"

    async def _execute(self, ctx: AgentContext) -> dict:
        """生成章节正文"""
        writing_plan = ctx.files.get("writing_plan", ctx.task_description)
        genre_prompt = ctx.files.get("genre_prompt_segment", "")
        constraints = ctx.files.get("constraints", "")
        previous_anchor = ctx.files.get("previous_anchor", "")
        character_briefs = ctx.files.get("character_briefs", "")
        target_words = ctx.files.get("target_word_count", "4000")
        user_focus = ctx.files.get("user_focus", "")

        system_prompt = f"""{ctx.system_prompt}

## 类型文风要求
{genre_prompt}

## 写作约束
{constraints}

## 角色简要
{character_briefs}

## 前文关键锚点
{previous_anchor}

## 目标字数
{target_words} 字左右"""

        user_prompt = f"""写作计划:
{writing_plan}

用户特殊指示:
{user_focus or '无'}

请开始写作。"""

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        # 流式生成
        full_text = []
        try:
            async for chunk in self.provider.generate_stream(messages, LLMConfig(
                model=self.config.get("model", self.DEFAULT_MODEL),
                max_tokens=8000, temperature=0.8,
            )):
                full_text.append(chunk)
        except Exception as e:
            return {"content": f"Writer error: {e}", "passed": False}

        content = "".join(full_text)
        return {
            "content": content,
            "word_count": len(content),
            "passed": True,
        }

    async def generate_stream(self, ctx: AgentContext):
        """返回异步迭代器，供 SSE 使用"""
        writing_plan = ctx.files.get("writing_plan", ctx.task_description)
        genre_prompt = ctx.files.get("genre_prompt_segment", "")
        constraints = ctx.files.get("constraints", "")
        previous_anchor = ctx.files.get("previous_anchor", "")
        character_briefs = ctx.files.get("character_briefs", "")
        target_words = ctx.files.get("target_word_count", "4000")
        user_focus = ctx.files.get("user_focus", "")

        system_prompt = f"""{ctx.system_prompt}

## 类型文风要求
{genre_prompt}

## 写作约束
{constraints}

## 角色简要
{character_briefs}

## 前文关键锚点
{previous_anchor}

## 目标字数
{target_words} 字左右"""

        user_prompt = f"写作计划:\n{writing_plan}\n\n用户指示:\n{user_focus or '无'}\n\n请开始写作。"

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        async for chunk in self.provider.generate_stream(messages, LLMConfig(
            model=self.config.get("model", self.DEFAULT_MODEL),
            max_tokens=8000, temperature=0.8,
        )):
            yield chunk
