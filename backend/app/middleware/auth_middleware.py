from fastapi import Request
from app.security import decode_token

DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000000"


async def get_current_user_id(request: Request) -> str:
    """获取当前用户 ID。未登录时返回默认用户，方便开发阶段跳过登录。"""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        payload = decode_token(token)
        if payload is not None:
            return payload["sub"]
    # 开发模式：无 token 时使用默认用户
    return DEFAULT_USER_ID
