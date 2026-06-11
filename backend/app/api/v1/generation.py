"""章节生成 API — 基于 LangGraph 流水线 + SSE 流式输出"""
import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.novel import Novel
from app.models.chapter import Chapter
from app.models.character import Character
from app.services.context_assembly import ContextAssembler
from app.genre import load_genre_config, get_genre_constraint_summary
from app.langgraph.generation_graph import (
    build_chapter_graph,
    run_chapter_generation,
    assemble_context_node,
    preflight_node,
    write_chapter_node,
    review_chapter_node,
    decide_verdict,
)

router = APIRouter()


async def _verify_novel_exists(novel_id: str, db: AsyncSession):
    r = await db.execute(select(Novel).where(Novel.id == novel_id))
    if not r.scalar():
        raise HTTPException(404, "Novel not found")
    return r.scalar()


async def _build_initial_state(
    novel_id: str,
    chapter_number: int,
    db: AsyncSession,
    focus: str = "",
) -> dict:
    """构建 LangGraph 流水线的初始状态。

    包含: DB 查询 (ContextAssembler、角色、类型配置) 组装为 state dict。
    """
    novel = await _verify_novel_exists(novel_id, db)
    chapter = (await db.execute(
        select(Chapter).where(Chapter.novel_id == novel_id, Chapter.chapter_number == chapter_number)
    )).scalar()

    if not chapter:
        chapter = Chapter(
            novel_id=novel_id, chapter_number=chapter_number,
            title=f"第{chapter_number}章", status="outline"
        )
        db.add(chapter)
        await db.commit()
        await db.refresh(chapter)

    # ContextAssembler
    assembler = ContextAssembler(novel_id, chapter_number, db)
    ctx_layers = await assembler.assemble()

    # 角色
    chars = (await db.execute(
        select(Character).where(Character.novel_id == novel_id, Character.importance >= 5)
    )).scalars().all()
    char_profiles = [
        {"name": c.name, "role": c.role, "layer4": c.layer4_abilities, "voice": c.layer2_identity}
        for c in chars
    ]

    # 类型配置
    try:
        genre_cfg = load_genre_config(novel.genre_id or "xianxia") if novel.genre_id else {}
    except ValueError:
        genre_cfg = {}
    constraints = get_genre_constraint_summary(novel.genre_id or "xianxia") if novel.genre_id else ""

    # 大纲文本
    chapter_plan = f"""## 第{chapter_number}章大纲
{ctx_layers['layer4_plan']}

## 前情提要
{ctx_layers['layer3_history']}

## 登场角色
{chr(10).join(f'- {c["name"]}({c["role"]}): {c["layer4"]}' for c in char_profiles)}
"""

    target_words = chapter.word_count or 4000

    return {
        "novel_id": novel_id,
        "chapter_number": chapter_number,
        "chapter_plan": chapter_plan,
        "genre_config": genre_cfg,
        "character_profiles": char_profiles,
        "context_layers": ctx_layers,
        "user_focus": focus,
        "target_word_count": target_words,
        "messages": [],
        "files": {},
        "todos": [],
        # 用于保存回 DB
        "_chapter_obj": chapter,
        "_db": db,
    }


@router.post("/{novel_id}/chapters/{chapter_number}/generate")
async def generate_chapter(
    novel_id: str,
    chapter_number: int,
    focus: str = Query(""),
    model: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    """生成章节 — SSE 流式输出。基于 LangGraph 流水线。"""
    initial_state = await _build_initial_state(novel_id, chapter_number, db, focus)
    chapter = initial_state["_chapter_obj"]

    graph = build_chapter_graph()

    async def event_stream():
        final_state = initial_state
        chapter_content = ""

        try:
            # 使用 astream 遍历图的每个节点输出
            async for event in graph.astream(
                initial_state,
                stream_mode="updates",
            ):
                # event 是 {node_name: output} 的字典
                node_name = list(event.keys())[0] if event else "unknown"
                node_output = event.get(node_name, {})

                if node_name == "assemble_context":
                    yield f"data: {json.dumps({'phase': 'preflight', 'message': '正在检查类型和角色一致性...'})}\n\n"

                elif node_name == "preflight":
                    arch_report = node_output.get("architect_report", {})
                    yield f"data: {json.dumps({'phase': 'preflight_done', 'architect': json.dumps(arch_report, ensure_ascii=False)[:200]})}\n\n"

                elif node_name == "write_chapter":
                    yield f"data: {json.dumps({'phase': 'writing', 'message': '正文生成中...'})}\n\n"
                    # 写手节点的内容
                    content = node_output.get("chapter_content", "")
                    if content:
                        chapter_content = content
                        # 分块发送（模拟 token 流）
                        chunk_size = 50
                        for i in range(0, len(content), chunk_size):
                            token = content[i:i + chunk_size]
                            yield f"data: {json.dumps({'phase': 'writing', 'token': token})}\n\n"
                    yield f"data: {json.dumps({'phase': 'writing_done', 'word_count': len(chapter_content)})}\n\n"

                elif node_name == "review_chapter":
                    yield f"data: {json.dumps({'phase': 'review', 'message': '质量检查中...'})}\n\n"

                    guardian_report = node_output.get("guardian_report", {})
                    inspector_report = node_output.get("inspector_report", {})

                    # 判定
                    verdict = "pass"
                    if guardian_report and not guardian_report.get("passed", True):
                        violations = guardian_report.get("violations", [])
                        if any(v.get("severity") == "fatal" for v in violations):
                            verdict = "regenerate"
                    if verdict == "pass" and inspector_report:
                        verdict = inspector_report.get("verdict", "pass")

                    # 保存章节
                    if chapter_content:
                        chapter.content = chapter_content
                        chapter.word_count = len(chapter_content)
                        chapter.status = "generated"
                        await db.commit()

                    yield f"data: {json.dumps({
                        'phase': 'done',
                        'verdict': verdict,
                        'word_count': len(chapter_content),
                        'guardian_passed': guardian_report.get('passed', True) if guardian_report else None,
                        'inspector_verdict': inspector_report.get('verdict') if inspector_report else None,
                    })}\n\n"

                    final_state = {**final_state, **node_output, "verdict": verdict}

                # 更新累积状态
                final_state = {**final_state, **node_output}

        except Exception as e:
            yield f"data: {json.dumps({'phase': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/{novel_id}/chapters/{chapter_number}/generate-simple")
async def generate_simple(
    novel_id: str,
    chapter_number: int,
    db: AsyncSession = Depends(get_db),
):
    """简单生成（非流式），使用 LangGraph 流水线。"""
    initial_state = await _build_initial_state(novel_id, chapter_number, db)
    chapter = initial_state["_chapter_obj"]

    # 运行流水线
    final_state = await run_chapter_generation(
        novel_id=novel_id,
        chapter_number=chapter_number,
        chapter_plan=initial_state["chapter_plan"],
        genre_config=initial_state["genre_config"],
        character_profiles=initial_state["character_profiles"],
        context_layers=initial_state["context_layers"],
        user_focus=initial_state.get("user_focus", ""),
        target_word_count=initial_state.get("target_word_count", 4000),
    )

    chapter_content = final_state.get("chapter_content", "")
    guardian_report = final_state.get("guardian_report", {})
    inspector_report = final_state.get("inspector_report", {})

    # 判定
    verdict = "pass"
    if guardian_report and not guardian_report.get("passed", True):
        violations = guardian_report.get("violations", [])
        if any(v.get("severity") == "fatal" for v in violations):
            verdict = "regenerate"
    if verdict == "pass" and inspector_report:
        verdict = inspector_report.get("verdict", "pass")

    # 保存章节
    if chapter_content:
        chapter.content = chapter_content
        chapter.word_count = len(chapter_content)
        chapter.status = "generated"
        await db.commit()

    return {
        "content": chapter_content,
        "word_count": len(chapter_content),
        "verdict": verdict,
        "guardian_passed": guardian_report.get("passed", True) if guardian_report else None,
        "guardian_violations": len(guardian_report.get("violations", [])) if guardian_report else 0,
        "inspector_verdict": inspector_report.get("verdict", "") if inspector_report else "",
        "inspector_score": inspector_report.get("overall_score", 0) if inspector_report else 0,
    }
