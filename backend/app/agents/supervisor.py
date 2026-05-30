import asyncio
import json
from app.agents.base import BaseAgent, AgentContext
from app.agents.tools.task_tool import task
from app.agents.tools.todo_tools import write_todos, read_todos, mark_done
from app.agents.tools.file_tools import init_session, get_files, write_file, read_file, merge_files
from app.llm.base import LLMMessage, LLMConfig

SUPERVISOR_SYSTEM_PROMPT = """你是小说创作的主编，协调所有AI Agent完成创作流程。

你的职责：
1. 规划任务流程 (write_todos)
2. 委托 guardian 做类型合规检查
3. 委托 custodian 做角色一致性检查
4. 跟踪进度 (read_todos)
5. 汇总结果并写入虚拟文件系统

可用Agent: guardian (类型检查), custodian (角色检查)"""


class SupervisorAgent(BaseAgent):
    DEFAULT_MODEL = "deepseek-chat"

    async def run_pipeline(self, session_id: str, chapter_content: str,
                           genre_config: str = "{}", character_profiles: str = "[]") -> dict:
        """执行标准生成后检查流程：Guardian + Custodian 并行审查"""
        init_session(session_id)
        write_file(session_id, "chapter_draft.md", chapter_content)
        write_file(session_id, "genre_config.json", genre_config)
        write_file(session_id, "character_profiles.json", character_profiles)

        write_todos(session_id, [
            {"content": "Guardian 类型合规检查", "status": "pending"},
            {"content": "Custodian 角色一致性检查", "status": "pending"},
            {"content": "汇总检查结果", "status": "pending"},
        ])

        # 并行委托
        async def run_guardian():
            return await task(
                f"检查以下正文的类型合规性。\n\n{chapter_content[:8000]}",
                "guardian",
                files={"genre_config": genre_config},
            )

        async def run_custodian():
            return await task(
                chapter_content[:8000],
                "custodian",
                files={"character_profiles": character_profiles},
            )

        g_result, c_result = await asyncio.gather(run_guardian(), run_custodian())
        mark_done(session_id, 0)
        mark_done(session_id, 1)

        # 汇总
        mark_done(session_id, 2)
        summary = {
            "guardian": g_result,
            "custodian": c_result,
            "all_passed": g_result.get("passed", True) and c_result.get("passed", True),
        }
        write_file(session_id, "supervisor_report.json", json.dumps(summary, ensure_ascii=False, indent=2))

        return {"content": json.dumps(summary, ensure_ascii=False, indent=2),
                "files": get_files(session_id), "session_id": session_id}

    async def _execute(self, ctx: AgentContext) -> dict:
        """LLM 驱动的灵活编排"""
        session_id = ctx.files.get("session_id", "default")
        init_session(session_id)

        for name, content in ctx.files.items():
            if name not in ("session_id",):
                write_file(session_id, name, content)

        messages = [
            LLMMessage(role="system", content=ctx.system_prompt),
            LLMMessage(role="user", content=f"""任务: {ctx.task_description}
已有文件: {', '.join(get_files(session_id).keys()) or '无'}
请决定行动。输出JSON: {{"action":"write_todos/run_agents/report","agent_to_call":"guardian/custodian","agent_task":"..."}}"""),
        ]
        try:
            resp = await self.provider.generate(messages, LLMConfig(
                model=self.config.get("model", self.DEFAULT_MODEL),
                temperature=0.3, max_tokens=1000,
            ))
            plan = json.loads(resp.content)
        except json.JSONDecodeError:
            plan = {"action": "report"}

        if plan.get("action") in ("run_agents", "write_todos"):
            return await self.run_pipeline(
                session_id,
                chapter_content=ctx.task_description,
                genre_config=ctx.files.get("genre_config", "{}"),
                character_profiles=ctx.files.get("character_profiles", "[]"),
            )

        return {"content": json.dumps(plan), "files": get_files(session_id)}
