from fastapi import Depends, HTTPException, status, WebSocket, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Callable

from backend.database import get_db
from backend.db.schema import User, Role
from backend.auth.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Check cookie first, then fallback to Authorization header for testing/API clients
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.split(" ")[1]
            
    if not token:
        # Seamless hackathon/demo mode fallback: if no token is passed, default to admin user
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            return admin_user
        raise credentials_exception
        
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
        
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    token_ver = getattr(user, "token_version", 1)
    if user is None or payload.get("version") != token_ver:
        raise credentials_exception
    return user

def require_role(min_role: Role) -> Callable:
    def role_checker(current_user: User = Depends(get_current_user)):
        roles_hierarchy = [Role.ReadOnly, Role.Analyst, Role.Supervisor, Role.ACP, Role.DCP, Role.Admin]

        try:
            user_level = roles_hierarchy.index(current_user.role)
            min_level = roles_hierarchy.index(min_role)
        except ValueError:
            raise HTTPException(status_code=403, detail="Invalid role definition")
            
        if user_level < min_level:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return current_user
    return role_checker

async def get_ws_current_user(websocket: WebSocket, db: Session = Depends(get_db)) -> User:
    token = websocket.cookies.get("access_token")
    if not token:
        # Fallback to authorization header if provided (useful for testing)
        auth = websocket.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.split(" ")[1]
            
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
        
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
        
    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    return user
