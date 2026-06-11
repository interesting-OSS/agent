"""墨庐 LangGraph 模块 — 状态定义。

基于 LangGraph AgentState，扩展章节生成所需的所有字段。
"""

from typing import Annotated, Literal, NotRequired

from langchain.agents import AgentState


# ---------------------------------------------------------------------------
# Reducer — 合并 files 字典
# ---------------------------------------------------------------------------

def file_reducer(left: dict | None, right: dict | None) -> dict:
    """合并虚拟文件系统，右侧优先。"""
    if left is None:
        return right or {}
    elif right is None:
        return left
    else:
        return {**left, **right}


# ---------------------------------------------------------------------------
# Todo 类型
# ---------------------------------------------------------------------------

class TodoItem(dict):
    """结构化任务项。"""
    content: str
    status: Literal["pending", "in_progress", "completed"]


# ---------------------------------------------------------------------------
# ChapterState
# ---------------------------------------------------------------------------

class ChapterState(AgentState):
    """章节生成流水线状态。

    继承 LangGraph AgentState（含 messages），扩展小说写作专用字段。
    """

    # ---- 输入参数 ----
    novel_id: NotRequired[str]
    chapter_number: NotRequired[int]
    genre_config: NotRequired[dict]          # 类型配置 (genre YAML 解析结果)
    character_profiles: NotRequired[list[dict]]  # 角色档案列表
    user_focus: NotRequired[str]             # 用户特殊指示

    # ---- 上下文 ----
    context_layers: NotRequired[dict]         # ContextAssembler.assemble() 的 4 层输出
    chapter_plan: NotRequired[str]            # 本章大纲文本
    target_word_count: NotRequired[int]       # 目标字数

    # ---- PreFlight 输出 ----
    architect_report: NotRequired[dict]       # Architect 的情节/伏笔/因果报告
    guardian_pre_check: NotRequired[dict]     # Guardian 出版前检查

    # ---- Writing 输出 ----
    chapter_content: NotRequired[str]         # 生成的章节正文
    chapter_word_count: NotRequired[int]      # 实际字数

    # ---- Review 输出 ----
    guardian_report: NotRequired[dict]        # Guardian 合规报告
    inspector_report: NotRequired[dict]       # Inspector 10 维质量报告

    # ---- 判定 ----
    verdict: NotRequired[str]                 # pass | rewrite | regenerate

    # ---- 虚拟文件系统 (用于 Agent 间上下文传递) ----
    files: Annotated[NotRequired[dict[str, str]], file_reducer]
    todos: NotRequired[list[dict]]
