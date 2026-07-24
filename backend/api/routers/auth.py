from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.db.schema import User
from backend.auth.security import verify_password, create_access_token, create_refresh_token, decode_refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.core.limiter import limiter

router = APIRouter(prefix="/api/auth", tags=["auth"])

class RefreshTokenRequest(BaseModel):
    pass # No longer needed in body, read from cookie

@router.post("/token")
@limiter.limit("10/minute")
def login_for_access_token(request: Request, response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # We will update these later to include token_version
    token_ver = getattr(user, "token_version", 1)
    access_token = create_access_token(
        data={"sub": user.username, "role": str(user.role), "version": token_ver}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.username, "role": str(user.role), "version": token_ver})
    
    # Set HttpOnly Cookies
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="lax", max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="lax", max_age=7 * 24 * 60 * 60)
    
    return {"access_token": access_token, "token_type": "bearer", "user": {"username": user.username, "role": str(user.role)}}

@router.post("/refresh")
@limiter.limit("10/minute")
def refresh_access_token(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")
        
    payload = decode_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
    if payload.get("version") != user.token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
        
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role, "version": user.token_version}
    )
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="lax", max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    return {"message": "Token refreshed"}
