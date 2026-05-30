"""章节生成 API — SSE 流式输出"""
import asyncio, json
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth_middleware import get_current_user_id
from app.models.novel import Novel
from app.models.chapter import Chapter
from app.models.character import Character
from app.agents import get_agent, init_agents
from app.agents.tools.task_tool import task
from app.services.context_assembly import ContextAssembler
from app.genre import load_genre_config, get_genre_constraint_summary
from app.schemas.generation import GenerationRequest

router = APIRouter()
init_agents()


async def _verify_owner(novel_id: str, request: Request, db: AsyncSession):
    user_id = await get_current_user_id(request)
    r = await db.execute(select(Novel).where(Novel.id == novel_id, Novel.user_id == user_id))
    if not r.scalar(): raise HTTPException(404, "Novel not found")
    return (await db.execute(select(Novel).where(Novel.id == novel_id))).scalar()


@router.post("/{novel_id}/chapters/{chapter_number}/generate")
async def generate_chapter(
    novel_id: str, chapter_number: int, request: Request,
    focus: str = Query(""), model: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    novel = await _verify_owner(novel_id, request, db)
    chapter = (await db.execute(
        select(Chapter).where(Chapter.novel_id == novel_id, Chapter.chapter_number == chapter_number)
    )).scalar()
    if not chapter:
        chapter = Chapter(novel_id=novel_id, chapter_number=chapter_number, title=f"第{chapter_number}章", status="outline")
        db.add(chapter); await db.commit(); await db.refresh(chapter)

    # 加载资源
    assembler = ContextAssembler(novel_id, chapter_number, db)
    ctx_layers = await assembler.assemble()

    chars = (await db.execute(select(Character).where(Character.novel_id == novel_id, Character.importance >= 5))).scalars().all()
    char_profiles = [{"name": c.name, "role": c.role, "layer4": c.layer4_abilities, "voice": c.layer2_identity} for c in chars]

    try:
        genre_cfg = load_genre_config(novel.genre_id or "xianxia") if novel.genre_id else {}
    except ValueError:
        genre_cfg = {}

    genre_prompt = genre_cfg.get("prompt_segment", "")
    constraints = get_genre_constraint_summary(novel.genre_id or "xianxia") if novel.genre_id else ""
    forbidden = genre_cfg.get("forbidden_terms", {}).get("terms", [])

    chapter_plan = f"""## 第{chapter_number}章大纲
{ctx_layers['layer4_plan']}

## 前情提要
{ctx_layers['layer3_history']}

## 登场角色
{chr(10).join(f'- {c["name"]}({c["role"]}): {c["layer4"]}' for c in char_profiles)}
"""

    async def event_stream():
        # Phase 1: PreFlight
        yield f"data: {json.dumps({'phase': 'preflight', 'message': '正在检查类型和角色一致性...'})}\n\n"

        arch_result, guard_result = await asyncio.gather(
            task(f"分析第{chapter_number}章大纲:\n{chapter_plan}", "architect",
                 files={"outline": json.dumps({"chapter_number": chapter_number}),
                        "previous_summaries": ctx_layers['layer3_history'],
                        "foreshadows": "[]", "chapter_plan": chapter_plan}),
            task(f"生成第{chapter_number}章类型约束", "guardian",
                 files={"genre_config": json.dumps(genre_cfg, ensure_ascii=False)}),
        )
        yield f"data: {json.dumps({'phase': 'preflight_done', 'architect': arch_result.get('content', '')[:200]})}\n\n"

        # Phase 2: Writing
        yield f"data: {json.dumps({'phase': 'writing', 'message': '正文生成中...'})}\n\n"

        writer_agent = get_agent("writer")
        full_text = []
        async for chunk in writer_agent.generate_stream(
            type('ctx', (), {
                'system_prompt': writer_agent.config['system_prompt'],
                'task_description': chapter_plan,
                'files': {
                    'writing_plan': chapter_plan,
                    'genre_prompt_segment': genre_prompt,
                    'constraints': f"禁止术语({','.join(forbidden[:10])})" if forbidden else "",
                    'previous_anchor': ctx_layers['layer2_active'][:500],
                    'character_briefs': json.dumps(char_profiles, ensure_ascii=False),
                    'target_word_count': str(chapter.word_count or 4000),
                    'user_focus': focus or "",
                },
                'max_tokens': 40000,
            })()
        ):
            full_text.append(chunk)
            yield f"data: {json.dumps({'phase': 'writing', 'token': chunk})}\n\n"

        chapter_content = "".join(full_text)
        yield f"data: {json.dumps({'phase': 'writing_done', 'word_count': len(chapter_content)})}\n\n"

        # Phase 3: Review
        yield f"data: {json.dumps({'phase': 'review', 'message': '质量检查中...'})}\n\n"

        # Run guardian first (inspector needs its result, so cannot run in parallel)
        guard_check = await task(
            f"扫描正文类型合规性:\n\n{chapter_content[:8000]}", "guardian",
            files={"genre_config": json.dumps(genre_cfg, ensure_ascii=False)},
        )
        inspect_result = await task(
            "10维质量分析", "inspector",
            files={"chapter_content": chapter_content, "outline": chapter_plan,
                   "genre_config": json.dumps(genre_cfg, ensure_ascii=False),
                   "character_profiles": json.dumps(char_profiles, ensure_ascii=False),
                   "guardian_result": json.dumps(guard_check), "target_word_count": "4000"},
        )

        # Save chapter
        chapter.content = chapter_content
        chapter.word_count = len(chapter_content)
        chapter.status = "generated"
        await db.commit()

        verdict = "pass"
        if guard_check and not guard_check.get("passed", True):
            verdict = "regenerate"
        elif inspect_result and not inspect_result.get("passed", True):
            verdict = inspect_result.get("verdict", "rewrite")

        yield f"data: {json.dumps({'phase': 'done', 'verdict': verdict, 'word_count': len(chapter_content),
                                    'guardian_passed': guard_check.get('passed', True) if guard_check else None,
                                    'inspector_verdict': inspect_result.get('verdict') if inspect_result else None})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/{novel_id}/chapters/{chapter_number}/generate-simple")
async def generate_simple(novel_id: str, chapter_number: int, request: Request, db: AsyncSession = Depends(get_db)):
    """简单生成（非流式），快速测试"""
    novel = await _verify_owner(novel_id, request, db)
    writer = get_agent("writer")
    inspector = get_agent("inspector")
    guardian = get_agent("guardian")

    genre_cfg = load_genre_config(novel.genre_id or "xianxia") if novel.genre_id else {}
    forbidden = genre_cfg.get("forbidden_terms", {}).get("terms", [])
    constraints = get_genre_constraint_summary(novel.genre_id or "xianxia") if novel.genre_id else ""

    chars = (await db.execute(select(Character).where(Character.novel_id == novel_id, Character.importance >= 5))).scalars().all()
    char_profiles = [{"name": c.name, "role": c.role, "layer4": c.layer4_abilities, "layer2": c.layer2_identity} for c in chars]

    assembler = ContextAssembler(novel_id, chapter_number, db)
    ctx = await assembler.assemble()

    plan = f"""类型: {genre_cfg.get('name', '')}
风格: {constraints}
角色: {json.dumps(char_profiles, ensure_ascii=False)[:500]}
故事背景: {ctx['layer3_history'][:500]}
当前章节: {ctx['layer4_plan']}
目标字数: 2000字"""

    writer_ctx = type('ctx', (), {
        'system_prompt': writer.config['system_prompt'],
        'task_description': '写正文',
        'files': {'writing_plan': plan, 'genre_prompt_segment': genre_cfg.get('prompt_segment', ''),
                   'constraints': f"禁止: {','.join(forbidden[:10])}" if forbidden else "",
                   'previous_anchor': ctx['layer2_active'][:300],
                   'character_briefs': json.dumps(char_profiles, ensure_ascii=False),
                   'target_word_count': '2000', 'user_focus': ''},
        'max_tokens': 40000,
    })()

    full_text = []
    async for chunk in writer.generate_stream(writer_ctx):
        full_text.append(chunk)
    content = "".join(full_text)

    # Guardian check
    g_result = await task(f"扫描正文:\n\n{content[:6000]}", "guardian",
                          files={"genre_config": json.dumps(genre_cfg, ensure_ascii=False)})

    # Save
    chapter = (await db.execute(
        select(Chapter).where(Chapter.novel_id == novel_id, Chapter.chapter_number == chapter_number)
    )).scalar()
    if chapter:
        chapter.content = content; chapter.word_count = len(content); chapter.status = "generated"
    else:
        chapter = Chapter(novel_id=novel_id, chapter_number=chapter_number, title=f"第{chapter_number}章",
                          content=content, word_count=len(content), status="generated")
        db.add(chapter)
    await db.commit()

    return {
        "content": content, "word_count": len(content),
        "guardian_passed": g_result.get("passed", True) if g_result else None,
        "guardian_violations": len(g_result.get("violations", [])) if g_result else 0,
    }
