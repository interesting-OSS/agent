"""ChromaDB 向量记忆 — 章节内容嵌入 + 语义检索"""
from app.config import settings
import json

_client = None

async def _get_client():
    global _client
    if _client is None:
        import chromadb
        _client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
    return _client

async def index_chapter(chapter_id: str, content: str, novel_id: str):
    try:
        client = await _get_client()
        import hashlib
        coll_name = f"novel_{hashlib.sha256(novel_id.encode()).hexdigest()[:16]}"
        collection = client.get_or_create_collection(coll_name)
        collection.add(documents=[content[:8000]], ids=[chapter_id])
    except Exception:
        pass

async def search_similar(query: str, novel_id: str, top_k: int = 5) -> list[str]:
    try:
        client = await _get_client()
        import hashlib
        coll_name = f"novel_{hashlib.sha256(novel_id.encode()).hexdigest()[:16]}"
        collection = client.get_or_create_collection(coll_name)
        results = collection.query(query_texts=[query], n_results=top_k)
        return results.get("documents", [[]])[0] or []
    except Exception:
        return []
