"""TODO 管理工具"""
import json

_todos: dict[str, list[dict]] = {}  # session_id -> [{"content": "...", "status": "pending/in_progress/completed"}]


def write_todos(session_id: str, todos: list[dict]) -> str:
    """规划任务列表"""
    _todos[session_id] = [{"content": t["content"], "status": t.get("status", "pending")} for t in todos]
    lines = [f"- [{t['status']}] {t['content']}" for t in _todos[session_id]]
    return "任务已规划:\n" + "\n".join(lines)


def read_todos(session_id: str) -> str:
    """读取任务列表"""
    todos = _todos.get(session_id, [])
    if not todos:
        return "暂无任务"
    lines = [f"- [{t['status']}] {t['content']}" for t in todos]
    pending = [t for t in todos if t["status"] in ("pending", "in_progress")]
    done = [t for t in todos if t["status"] == "completed"]
    return f"任务进度: {len(done)}/{len(todos)} 已完成\n" + "\n".join(lines) + ("\n\n下一个: " + pending[0]["content"] if pending else "")


def mark_done(session_id: str, todo_index: int) -> str:
    """标记任务完成"""
    todos = _todos.get(session_id, [])
    if 0 <= todo_index < len(todos):
        todos[todo_index]["status"] = "completed"
        return f"已完成: {todos[todo_index]['content']}"
    return "任务不存在"
