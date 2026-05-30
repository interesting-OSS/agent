"""书籍导入拆解 — TXT → 结构化数据"""
from app.llm.base import BaseLLMProvider, LLMMessage, LLMConfig
import json

async def import_book(text: str, provider: BaseLLMProvider) -> dict:
    """上传 TXT 文件，AI 逆向拆解"""
    messages = [
        LLMMessage(role="system", content="""你是小说结构分析师。分析文本，输出JSON:
{
  "title": "推测标题",
  "genre_guess": "推测类型",
  "characters": [{"name":"","role":"","traits":"","relationships":""}],
  "world_setting": "世界观描述",
  "plot_summary": "情节梗概",
  "writing_style": "写作风格分析",
  "chapter_count": 推测章节数
}"""),
        LLMMessage(role="user", content=f"分析以下小说:\n{text[:15000]}"),
    ]
    resp = await provider.generate(messages, LLMConfig(model="deepseek-chat", temperature=0.3, max_tokens=4000))
    try:
        return json.loads(resp.content)
    except json.JSONDecodeError:
        return {"error": "解析失败", "raw": resp.content}
