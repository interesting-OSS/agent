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
