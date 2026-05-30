def scan_forbidden_terms(text: str, forbidden_terms: list[str]) -> list[dict]:
    """机械扫描——速度快、零幻觉、100%召回。不依赖 LLM。"""
    violations = []
    for term in forbidden_terms:
        idx = text.find(term)
        if idx >= 0:
            # 提取上下文
            start = max(0, idx - 20)
            end = min(len(text), idx + len(term) + 20)
            context = text[start:end]
            violations.append({
                "term": term,
                "position": idx,
                "context": f"...{context}...",
                "severity": "fatal",
            })
    return violations


def mark_issues(violations: list[dict]) -> str:
    """生成人类可读的违规报告"""
    if not violations:
        return "类型合规检查通过——未发现禁止术语。"
    lines = ["# 类型合规检查报告\n", f"发现 {len(violations)} 个违规项：\n"]
    for i, v in enumerate(violations, 1):
        lines.append(f"{i}. **{v['term']}** (严重度: {v['severity']})")
        lines.append(f"   位置: 第 {v['position']} 字符附近")
        lines.append(f"   上下文: {v['context']}\n")
    return "\n".join(lines)
