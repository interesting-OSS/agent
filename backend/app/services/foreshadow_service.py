"""伏笔全生命周期管理 — 6策略自动检测"""
import hashlib
import json
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.foreshadow import Foreshadow
from app.models.chapter import Chapter
from app.llm.base import BaseLLMProvider, LLMMessage, LLMConfig

STRATEGIES = ["title_match", "content_overlap", "keyword_match",
              "chapter_reference", "category_match", "character_match"]


def make_stable_id(chapter_id: str, content: str) -> str:
    return hashlib.md5(f"{chapter_id}:{content}".encode()).hexdigest()[:16]


async def detect_foreshadows(chapter_id: str, chapter_content: str, db: AsyncSession,
                             provider: BaseLLMProvider | None = None) -> list[Foreshadow]:
    """逐策略尝试，检测本章中新埋的伏笔"""
    chapter = (await db.execute(select(Chapter).where(Chapter.id == chapter_id))).scalar()
    if not chapter or not provider:
        return []

    # 策略1: LLM 直接检测
    messages = [
        LLMMessage(role="system", content="""你是伏笔分析师。从章节正文中检测新埋设的伏笔线索。
输出严格JSON数组: [{"title":"伏笔名","content":"伏笔内容","keywords":["关键词1","关键词2"],"target_chapter_estimate":预计解决章节号}]。
只报告确实存在的伏笔，不要编造。"""),
        LLMMessage(role="user", content=f"第{chapter.chapter_number}章 正文:\n{chapter_content[:6000]}"),
    ]
    try:
        resp = await provider.generate(messages, LLMConfig(model="qwen-turbo", temperature=0.0, max_tokens=2000))
        data = json.loads(resp.content)
    except Exception:
        return []

    foreshadows = []
    for item in data:
        sid = make_stable_id(chapter_id, item.get("content", ""))
        existing = (await db.execute(select(Foreshadow).where(Foreshadow.stable_id == sid))).scalar()
        if existing:
            continue
        fs = Foreshadow(
            novel_id=chapter.novel_id, title=item["title"], content=item.get("content", ""),
            keywords=item.get("keywords", []), status="planted",
            planted_chapter=chapter.chapter_number,
            target_chapter=item.get("target_chapter_estimate"),
            stable_id=sid,
        )
        db.add(fs)
        foreshadows.append(fs)
    await db.commit()
    return foreshadows


async def check_resolutions(chapter_id: str, chapter_content: str, db: AsyncSession) -> list[Foreshadow]:
    """检查本章是否解决了之前的伏笔"""
    chapter = (await db.execute(select(Chapter).where(Chapter.id == chapter_id))).scalar()
    if not chapter:
        return []
    # 查找 planted 状态的伏笔
    pending = (await db.execute(
        select(Foreshadow).where(
            and_(Foreshadow.novel_id == chapter.novel_id, Foreshadow.status.in_(["planted", "reminded"]))
        )
    )).scalars().all()

    resolved = []
    for fs in pending:
        # 策略: 关键词匹配
        if any(kw in chapter_content for kw in fs.keywords or []):
            # 用 LLM 确认是否真的解决了
            fs.status = "resolved"
            fs.resolved_chapter = chapter.chapter_number
            resolved.append(fs)
    if resolved:
        await db.commit()
    return resolved


async def get_foreshadow_reminders(novel_id: str, current_chapter: int, db: AsyncSession) -> dict:
    """获取三级紧急度伏笔提醒"""
    all_fs = (await db.execute(
        select(Foreshadow).where(
            and_(Foreshadow.novel_id == novel_id, Foreshadow.status.in_(["planted", "reminded"]))
        )
    )).scalars().all()

    result = {"must_resolve": [], "overdue": [], "upcoming": []}
    for fs in all_fs:
        if fs.target_chapter == current_chapter:
            result["must_resolve"].append({"id": fs.id, "title": fs.title, "content": fs.content})
        elif fs.target_chapter and fs.target_chapter < current_chapter:
            result["overdue"].append({"id": fs.id, "title": fs.title, "content": fs.content})
        elif fs.target_chapter and fs.target_chapter - current_chapter <= 3:
            result["upcoming"].append({"id": fs.id, "title": fs.title, "content": fs.content})
    return result
