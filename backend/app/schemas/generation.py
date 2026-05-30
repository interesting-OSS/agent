# Step 8: 生成请求/响应 schema
from pydantic import BaseModel

class GenerationRequest(BaseModel):
    style_overrides: dict | None = None
    focus_instructions: str | None = None
    model: str | None = None  # 覆盖默认模型

class GenerationProgress(BaseModel):
    phase: str  # preflight / writing / review
    progress: float = 0.0
    message: str = ""
