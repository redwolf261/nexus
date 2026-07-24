import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Optional
import os
from dotenv import load_dotenv
import secrets

load_dotenv()

# Securely load from .env or generate a highly secure fallback if missing for local dev only
raw_keys = os.getenv("NEXUS_JWT_KEYS", os.getenv("SECRET_KEY", secrets.token_urlsafe(32)))
JWT_KEYS = [k.strip() for k in raw_keys.split(",")] if "," in raw_keys else [raw_keys]
PRIMARY_KEY = JWT_KEYS[0]

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, PRIMARY_KEY, algorithm=ALGORITHM, headers={"kid": "0"})
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, PRIMARY_KEY, algorithm=ALGORITHM, headers={"kid": "0"})
    return encoded_jwt

def _decode_with_rotation(token: str, token_type: str) -> dict:
    # Try all keys in rotation starting with the primary
    for key in JWT_KEYS:
        try:
            payload = jwt.decode(token, key, algorithms=[ALGORITHM])
            if payload.get("type") == token_type:
                return payload
        except jwt.PyJWTError:
            continue
    return None

def decode_access_token(token: str) -> dict:
    return _decode_with_rotation(token, "access")

def decode_refresh_token(token: str) -> dict:
    return _decode_with_rotation(token, "refresh")
