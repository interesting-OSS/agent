from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, AsyncSessionLocal
from app.models.base import Base
from app.models.user import User
from app.middleware.auth_middleware import DEFAULT_USER_ID
from app.security import hash_password
from sqlalchemy import select


async def ensure_default_user():
    """确保默认用户存在，跳过登录用。"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == DEFAULT_USER_ID))
        if not result.scalar():
            db.add(User(
                id=DEFAULT_USER_ID,
                email="dev@localhost",
                password_hash=hash_password("dev"),
                display_name="开发者",
            ))
            await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await ensure_default_user()
    yield
    # Cleanup LLM provider connections on shutdown
    from app.llm.registry import cleanup_providers
    await cleanup_providers()


app = FastAPI(title="Novel Writer", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


# == Step 4: Auth + Novels ==
from app.api.v1.auth import router as auth_router
from app.api.v1.novels import router as novels_router
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(novels_router, prefix="/api/v1/novels", tags=["novels"])

# == Step 6: Characters + Careers + World + Orgs + Relationships ==
from app.api.v1.characters import router as characters_router
from app.api.v1.careers import router as careers_router
from app.api.v1.world import router as world_router
from app.api.v1.organizations import router as orgs_router
from app.api.v1.relationships import router as rels_router
app.include_router(characters_router, prefix="/api/v1/novels", tags=["characters"])
app.include_router(careers_router, prefix="/api/v1/novels", tags=["careers"])
app.include_router(world_router, prefix="/api/v1/novels", tags=["world"])
app.include_router(orgs_router, prefix="/api/v1/novels", tags=["organizations"])
app.include_router(rels_router, prefix="/api/v1/novels", tags=["relationships"])

# == Step 8: Chapter Generation (SSE streaming) ==
from app.api.v1.generation import router as gen_router
app.include_router(gen_router, prefix="/api/v1/novels", tags=["generation"])

# == Step 9: Foreshadows + Analysis ==
from app.api.v1.foreshadows import router as fs_router
from app.api.v1.analysis import router as analysis_router
app.include_router(fs_router, prefix="/api/v1/novels", tags=["foreshadows"])
app.include_router(analysis_router, prefix="/api/v1/novels", tags=["analysis"])

# == Step 10: Revision + Export + Import ==
from app.api.v1.revision import router as rev_router
from app.api.v1.export import router as export_router
from app.api.v1.import_book import router as import_router
app.include_router(rev_router, prefix="/api/v1/novels", tags=["revision"])
app.include_router(export_router, prefix="/api/v1/novels", tags=["export"])
app.include_router(import_router, prefix="/api/v1", tags=["import"])


# == 类型配置列表接口（前端选择类型用）==
from app.genre.loader import list_available_genres, load_genre_config

@app.get("/api/v1/genre/list")
async def genre_list():
    genres = []
    for gid in list_available_genres():
        cfg = load_genre_config(gid)
        genres.append({"id": gid, "name": cfg.get("name", gid), "category": cfg.get("category", "")})
    return genres


@app.get("/api/v1/genre/{genre_id}")
async def genre_detail(genre_id: str):
    from app.genre.loader import load_genre_config
    return load_genre_config(genre_id)


# == 自动生成角色（扫描大纲，批量生成）==
@app.post("/api/v1/novels/{novel_id}/characters/auto")
async def auto_characters(novel_id: str):
    from app.services.auto_character import auto_generate_characters
    from app.llm.registry import get_provider
    from app.database import AsyncSessionLocal
    provider = get_provider("deepseek")
    async with AsyncSessionLocal() as db:
        names = await auto_generate_characters(novel_id, provider, db)
    return {"created": names}


# == 章节列表 ==
@app.get("/api/v1/novels/{novel_id}/chapters")
async def list_chapters(novel_id: str):
    from app.database import AsyncSessionLocal
    from app.models.chapter import Chapter
    from sqlalchemy import select
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Chapter).where(Chapter.novel_id == novel_id).order_by(Chapter.chapter_number)
        )
        return result.scalars().all()


# == 获取单章 ==
@app.get("/api/v1/novels/{novel_id}/chapters/{chapter_id}")
async def get_chapter(novel_id: str, chapter_id: str):
    from app.database import AsyncSessionLocal
    from app.models.chapter import Chapter
    from sqlalchemy import select
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Chapter).where(Chapter.id == chapter_id, Chapter.novel_id == novel_id)
        )
        ch = result.scalar()
        if not ch:
            from fastapi import HTTPException
            raise HTTPException(404, "Chapter not found")
        return ch
