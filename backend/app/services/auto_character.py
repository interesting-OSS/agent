from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.novel import Novel
from app.models.character import Character
from app.models.plot import OutlineNode
from app.llm.base import BaseLLMProvider


async def auto_generate_characters(novel_id: str, provider: BaseLLMProvider, db: AsyncSession):
    """扫描大纲节点，发现未创建的角色名，自动生成角色档案"""
    novel = (await db.execute(select(Novel).where(Novel.id == novel_id))).scalar()
    if not novel:
        return []

    # 获取已有角色名
    existing = (await db.execute(select(Character.name).where(Character.novel_id == novel_id))).scalars().all()
    existing_set = set(existing)

    # 扫描大纲中的角色提及
    nodes = (await db.execute(select(OutlineNode).where(OutlineNode.novel_id == novel_id))).scalars().all()
    mentioned_names: set[str] = set()
    for node in nodes:
        structure = node.structure or {}
        chars = structure.get("characters_involved", []) or []
        mentioned_names.update(chars)
        if node.causal_sentence:
            # 简单提取中文人名（2-4字）
            import re
            names = re.findall(r'[一-鿿]{2,4}', node.causal_sentence)
            mentioned_names.update(names)

    new_names = mentioned_names - existing_set - {"本章", "主角", "女主", "男主", "反派", "配角"}
    if not new_names:
        return []

    # 使用 LLM 批量生成角色档案
    from app.llm.base import LLMMessage, LLMConfig
    import json

    messages = [
        LLMMessage(role="system", content=f"""你是小说角色设计师。为以下角色创建简短档案。
小说类型: {novel.genre_id or '未知'}
已有角色: {', '.join(existing) if existing else '无'}
输出严格 JSON 数组: [{{"name":"...","role":"supporting/minor","layer1_worldview":"...","layer2_identity":"...","layer3_values":"...","layer4_abilities":"...","layer5_skills":"...","layer6_environment":"..."}}]"""),
        LLMMessage(role="user", content=f"请为这些角色创建档案: {', '.join(sorted(new_names)[:10])}"),
    ]
    resp = await provider.generate(messages, LLMConfig(model="deepseek-chat", temperature=0.7, max_tokens=4000))
    try:
        data = json.loads(resp.content)
    except json.JSONDecodeError:
        return []

    created = []
    for item in data:
        if item["name"] not in existing_set:
            char = Character(novel_id=novel_id, **item)
            db.add(char)
            created.append(item["name"])
    await db.commit()
    return created
