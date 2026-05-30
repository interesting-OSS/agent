"""上下文组装服务 — 分层预算: Bible ~8K + Active ~20K + History ~15K + Plan ~3K = ~46K"""
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.novel import Novel
from app.models.chapter import Chapter
from app.models.character import Character
from app.models.foreshadow import Foreshadow
from app.models.plot import OutlineNode
from app.genre import load_genre_config, get_genre_constraint_summary


class ContextAssembler:
    def __init__(self, novel_id: str, chapter_number: int, db: AsyncSession):
        self.novel_id = novel_id
        self.chapter_number = chapter_number
        self.db = db
        self.budget = 46000

    async def assemble(self) -> dict:
        return {
            "layer1_bible": await self._build_bible(),
            "layer2_active": await self._build_active(),
            "layer3_history": await self._build_history(),
            "layer4_plan": await self._build_plan(),
        }

    async def _build_bible(self) -> str:
        """L1: 静态圣经 (~8K)"""
        novel = (await self.db.execute(select(Novel).where(Novel.id == self.novel_id))).scalar()
        if not novel or not novel.genre_id:
            return ""
        try:
            config = load_genre_config(novel.genre_id)
        except ValueError:
            return f"类型: {novel.genre_id}"

        chars = (await self.db.execute(select(Character).where(Character.novel_id == self.novel_id))).scalars().all()
        char_summary = "\n".join(f"- {c.name}({c.role}): {(c.layer1_worldview or '')[:80]}" for c in chars)

        return f"""## 类型: {config['name']}
视角: {config['writing_blueprint']['perspective']}
氛围: {config['writing_blueprint']['atmosphere']}

## 角色总览
{char_summary}

## 类型铁律
{chr(10).join(f'- {t}' for t in config.get('taboos', []))}
"""

    async def _build_active(self) -> str:
        """L2: 活跃上下文 (~20K)"""
        parts = []
        # 上一章全文
        prev = (await self.db.execute(
            select(Chapter).where(Chapter.novel_id == self.novel_id, Chapter.chapter_number == self.chapter_number - 1)
        )).scalar()
        if prev:
            parts.append(f"## 上一章全文\n{(prev.content or '')[:3000]}")
            if prev.summary:
                parts.append(f"## 上一章摘要\n{prev.summary}")

        # 登场角色
        chars = (await self.db.execute(
            select(Character).where(Character.novel_id == self.novel_id, Character.importance >= 5)
        )).scalars().all()
        for c in chars:
            parts.append(f"## {c.name}({c.role})\n{c.layer4_abilities}\n状态: {json.dumps(c.current_state or {}, ensure_ascii=False)}")

        return "\n\n".join(parts)

    async def _build_history(self) -> str:
        """L3: 压缩历史 (~15K)"""
        chapters = (await self.db.execute(
            select(Chapter).where(Chapter.novel_id == self.novel_id, Chapter.chapter_number < self.chapter_number)
            .order_by(Chapter.chapter_number).limit(10)
        )).scalars().all()
        return "\n".join(f"第{ch.chapter_number}章 {ch.title}: {ch.summary or (ch.content or '')[:200]}" for ch in chapters)

    async def _build_plan(self) -> str:
        """L4: 章节计划 (~3K)"""
        outline = (await self.db.execute(
            select(OutlineNode).where(OutlineNode.novel_id == self.novel_id)
            .order_by(OutlineNode.sequence_order)
        )).scalars().all()
        current = [o for o in outline if o.sequence_order == self.chapter_number]
        if current:
            return f"本章大纲: {current[0].title}\n{current[0].causal_sentence or ''}\n{json.dumps(current[0].structure or {}, ensure_ascii=False)}"
        return f"第{self.chapter_number}章"

    def trim_to_budget(self, context: dict) -> dict:
        """P2→P1→P0 裁剪"""
        total = sum(len(v) for v in context.values())
        if total <= self.budget:
            return context
        # 先裁 history
        excess = total - self.budget
        for key in ["layer3_history", "layer2_active", "layer1_bible"]:
            if excess <= 0:
                break
            val = context.get(key, "")
            if len(val) > 500:
                context[key] = val[:max(0, len(val) - excess)] + "\n...(已裁剪)"
                excess = 0
        return context
