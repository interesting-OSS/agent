from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.organization import Organization
from app.models.plot import OutlineNode
from app.llm.base import BaseLLMProvider, LLMMessage, LLMConfig
import json


async def auto_generate_organizations(novel_id: str, provider: BaseLLMProvider, db: AsyncSession):
    """扫描大纲节点，发现未创建的组织名，自动生成组织档案"""
    existing = (await db.execute(select(Organization.name).where(Organization.novel_id == novel_id))).scalars().all()
    existing_set = set(existing)

    nodes = (await db.execute(select(OutlineNode).where(OutlineNode.novel_id == novel_id))).scalars().all()
    # 从大纲中提取可能的组织名（关键词匹配）
    org_keywords = ["宗", "门", "派", "会", "团", "殿", "阁", "楼", "盟", "族", "国", "军", "局", "司", "院", "府", "教", "寺", "工会", "商会", "学院"]
    mentioned_orgs: set[str] = set()
    for node in nodes:
        text = (node.title or "") + (node.causal_sentence or "")
        for kw in org_keywords:
            import re
            matches = re.findall(rf'[一-鿿]{{1,4}}{kw}', text)
            mentioned_orgs.update(matches)

    new_orgs = mentioned_orgs - existing_set
    if not new_orgs:
        return []

    messages = [
        LLMMessage(role="system", content="你是组织势力设计师。为以下组织名创建简短描述。输出严格JSON数组：[{\"name\":\"...\",\"org_type\":\"faction/guild/family/kingdom/cult/company\",\"description\":\"...\",\"importance\":1-10}]"),
        LLMMessage(role="user", content=f"为这些组织创建档案: {', '.join(sorted(new_orgs)[:10])}"),
    ]
    resp = await provider.generate(messages, LLMConfig(model="deepseek-chat", temperature=0.7, max_tokens=3000))
    try:
        data = json.loads(resp.content)
    except json.JSONDecodeError:
        return []

    created = []
    for item in data:
        if item["name"] not in existing_set:
            org = Organization(novel_id=novel_id, **{k: v for k, v in item.items() if k in ["name", "org_type", "description", "importance"]})
            db.add(org)
            created.append(item["name"])
    await db.commit()
    return created
