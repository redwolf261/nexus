from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from backend.auth.security import decode_access_token

def get_user_identity(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        token = auth.split(" ")[1]
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            return payload["sub"]
    return get_remote_address(request)

limiter = Limiter(key_func=get_user_identity)
