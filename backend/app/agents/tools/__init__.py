from app.agents.tools.task_tool import task, set_registry
from app.agents.tools.todo_tools import write_todos, read_todos, mark_done
from app.agents.tools.file_tools import ls, read_file, write_file, get_files, merge_files, init_session
from app.agents.tools.guard_tools import scan_forbidden_terms, mark_issues

TOOL_REGISTRY: dict[str, str] = {
    "write_todos": "规划任务列表",
    "read_todos": "读取任务列表",
    "task": "委托子Agent执行任务",
    "read_file": "读取虚拟文件",
    "write_file": "写入虚拟文件",
    "think_tool": "强制Agent停下来思考",
    "scan_forbidden_terms": "扫描正文中的禁止术语",
    "mark_issues": "生成违规报告",
    "check_consistency": "检查角色/世界观一致性",
    "search_foreshadows": "搜索相关伏笔",
}
