"""墨庐 LangGraph 模块 — 工具定义。

将现有工具迁移为 LangChain @tool 装饰器风格。
"""

import json
from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from app.langgraph.guard_tools import scan_forbidden_terms
from app.langgraph.state import ChapterState


# ---------------------------------------------------------------------------
# think_tool — 思考/反思（所有 Agent 通用）
# ---------------------------------------------------------------------------

THINK_TOOL_DESCRIPTION = """暂停并反思当前进度。用于：

- 分析收到的信息
- 规划下一步行动
- 评估是否遗漏了什么
- 在质量检查后决定判定结果

参数:
- reflection: 你的反思内容，详细写下你的思考过程
"""


@tool(description=THINK_TOOL_DESCRIPTION)
def think_tool(
    reflection: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> str:
    """思考工具——记录 AI 的反思过程。"""
    return f"已记录思考:\n{reflection}"


# ---------------------------------------------------------------------------
# scan_forbidden_terms — Guardian 专用
# ---------------------------------------------------------------------------

SCAN_FORBIDDEN_TERMS_DESCRIPTION = """机械扫描章节正文中的禁止术语。100% 召回率，零幻觉。

参数:
- text: 待扫描的章节正文
- forbidden_terms: 禁止术语列表（逗号分隔或 JSON 数组）
"""


@tool(description=SCAN_FORBIDDEN_TERMS_DESCRIPTION)
def scan_forbidden_terms_tool(
    text: str,
    forbidden_terms: str,
) -> str:
    """扫描文本中的禁止术语。"""
    # 解析 forbidden_terms
    terms = []
    try:
        parsed = json.loads(forbidden_terms)
        if isinstance(parsed, list):
            terms = parsed
    except (json.JSONDecodeError, TypeError):
        terms = [t.strip() for t in forbidden_terms.split(",") if t.strip()]

    if not terms:
        return "无需检查：未提供禁止术语列表。"

    violations = scan_forbidden_terms(text, terms)
    if not violations:
        return "✅ 类型合规检查通过——未发现禁止术语。"

    lines = [f"# 类型合规检查报告\n发现 {len(violations)} 个违规项：\n"]
    for i, v in enumerate(violations, 1):
        lines.append(f"{i}. **{v['term']}** (严重度: {v['severity']})")
        lines.append(f"   位置: 第 {v['position']} 字符附近")
        lines.append(f"   上下文: {v['context']}\n")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# check_consistency — Custodian 专用（语义检查）
# ---------------------------------------------------------------------------

CHECK_CONSISTENCY_DESCRIPTION = """检查章节中角色行为是否与其档案一致。

你需要用 LLM 判断角色的行为是否符合其 6 层模型（世界观/自我认同/价值观/能力/技能/环境）。

参数:
- chapter_text: 章节正文（前 6000 字）
- character_profiles: 角色档案 JSON
"""


@tool(description=CHECK_CONSISTENCY_DESCRIPTION)
def check_consistency_tool(
    chapter_text: str,
    character_profiles: str,
) -> str:
    """检查角色一致性。此工具需要在 Agent 的 system prompt 中指导 LLM 进行分析。"""
    # 这个工具本身不做 LLM 调用，它返回数据让调用它的 Agent（Custodian）来分析
    try:
        profiles = json.loads(character_profiles) if isinstance(character_profiles, str) else character_profiles
    except json.JSONDecodeError:
        profiles = []

    if not profiles:
        return "无需检查：无角色档案。"

    char_names = [p.get("name", "?") for p in profiles]
    return f"""请检查以下角色在章节中的一致性：

角色列表: {', '.join(char_names)}

角色档案:
{json.dumps(profiles, ensure_ascii=False, indent=2)[:3000]}

章节正文:
{chapter_text[:4000]}

请分析每个登场角色的：
1. 行为是否与 layer1-3（世界观/自我认同/价值观）一致
2. 对话是否符合角色声音
3. 能力是否在 layer4 范围内

输出 JSON 格式的检查报告。"""


# ---------------------------------------------------------------------------
# 虚拟文件系统工具（LangGraph state 版）
# ---------------------------------------------------------------------------

LS_DESCRIPTION = """列出当前虚拟文件系统中的所有文件。"""

READ_FILE_DESCRIPTION = """读取虚拟文件系统中的文件内容。

参数:
- file_path: 文件路径
- offset: 起始行号（默认 0）
- limit: 最大行数（默认 2000）
"""

WRITE_FILE_DESCRIPTION = """将内容写入虚拟文件系统。

参数:
- file_path: 文件路径
- content: 要写入的完整内容
"""


@tool(description=LS_DESCRIPTION)
def ls_files(
    state: Annotated[ChapterState, InjectedState],
) -> str:
    """列出虚拟文件系统中的所有文件。"""
    files = state.get("files", {})
    if not files:
        return "(空目录)"
    return "\n".join(sorted(files.keys()))


@tool(description=READ_FILE_DESCRIPTION)
def read_file(
    file_path: str,
    state: Annotated[ChapterState, InjectedState],
    offset: int = 0,
    limit: int = 2000,
) -> str:
    """读取虚拟文件，支持分页。"""
    files = state.get("files", {})
    if file_path not in files:
        return f"错误: 文件 '{file_path}' 不存在"

    content = files[file_path]
    if not content:
        return "(空文件)"

    lines = content.splitlines()
    start = offset
    end = min(start + limit, len(lines))

    if start >= len(lines):
        return f"错误: 偏移量 {offset} 超出文件长度 ({len(lines)} 行)"

    result = []
    for i in range(start, end):
        result.append(f"{i + 1:6d}\t{lines[i][:2000]}")
    return "\n".join(result)


@tool(description=WRITE_FILE_DESCRIPTION)
def write_file(
    file_path: str,
    content: str,
    state: Annotated[ChapterState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """写入虚拟文件，返回 Command 更新 state。"""
    files = dict(state.get("files", {}))
    files[file_path] = content
    return Command(
        update={
            "files": files,
            "messages": [
                ToolMessage(f"已写入: {file_path} ({len(content)} 字符)", tool_call_id=tool_call_id)
            ],
        }
    )
