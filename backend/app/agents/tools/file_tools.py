"""虚拟文件系统 —— Agent 间通过文件共享信息"""
_files: dict[str, dict[str, str]] = {}  # session_id -> {filename: content}


def init_session(session_id: str):
    if session_id not in _files:
        _files[session_id] = {}


def ls(session_id: str, prefix: str = "") -> str:
    """列出虚拟文件"""
    init_session(session_id)
    files = _files[session_id]
    if not files:
        return "(空目录)"
    names = sorted(files.keys())
    if prefix:
        names = [n for n in names if n.startswith(prefix)]
    return "\n".join(names) if names else "(无匹配文件)"


def read_file(session_id: str, filename: str) -> str:
    """读取虚拟文件"""
    init_session(session_id)
    content = _files[session_id].get(filename, "")
    if not content:
        return f"(文件不存在: {filename})"
    return content


def write_file(session_id: str, filename: str, content: str) -> str:
    """写入虚拟文件"""
    init_session(session_id)
    _files[session_id][filename] = content
    return f"已写入: {filename} ({len(content)} 字符)"


def get_files(session_id: str) -> dict[str, str]:
    """获取所有文件（用于 Agent 间传递）"""
    init_session(session_id)
    return dict(_files[session_id])


def merge_files(session_id: str, new_files: dict[str, str]):
    """合并文件（用于子Agent结果回传）"""
    init_session(session_id)
    _files[session_id].update(new_files)
