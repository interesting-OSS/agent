"""多格式导出 — MD / TXT / PDF(预留) / EPUB(预留) / DOCX(预留)"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chapter import Chapter
from app.models.novel import Novel
import json


async def export_novel(novel_id: str, fmt: str, db: AsyncSession, options: dict | None = None) -> bytes:
    novel = (await db.execute(select(Novel).where(Novel.id == novel_id))).scalar()
    if not novel:
        raise ValueError("Novel not found")
    chapters = (await db.execute(
        select(Chapter).where(Chapter.novel_id == novel_id).order_by(Chapter.chapter_number)
    )).scalars().all()

    if fmt in ("md", "markdown"):
        lines = [f"# {novel.title}\n\n", f"> 类型: {novel.genre_id} | 总字数: {novel.word_count}\n\n"]
        for ch in chapters:
            lines.append(f"## 第{ch.chapter_number}章 {ch.title or ''}\n\n")
            lines.append(ch.content or "(暂无内容)")
            lines.append("\n\n---\n\n")
        return "".join(lines).encode("utf-8")

    if fmt == "txt":
        lines = [f"{novel.title}\n\n"]
        for ch in chapters:
            lines.append(f"第{ch.chapter_number}章 {ch.title or ''}\n\n")
            lines.append(ch.content or "")
            lines.append("\n\n")
        return "".join(lines).encode("utf-8")

    # PDF/EPUB/DOCX require additional libraries
    if fmt == "pdf":
        try:
            from weasyprint import HTML
            html = f"<h1>{novel.title}</h1>" + "".join(f"<h2>第{ch.chapter_number}章</h2><p>{ch.content}</p>" for ch in chapters)
            return HTML(string=html).write_pdf()
        except ImportError:
            raise NotImplementedError("Install weasyprint for PDF export")
    if fmt == "epub":
        raise NotImplementedError("EPUB export: install ebooklib")
    if fmt == "docx":
        raise NotImplementedError("DOCX export: install python-docx")

    raise ValueError(f"Unknown format: {fmt}")
