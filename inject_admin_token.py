import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal
from backend.db.schema import User, Role
from backend.auth.security import get_password_hash, create_access_token
from datetime import timedelta
import uuid

db = SessionLocal()

# Check if admin user exists
admin = db.query(User).filter(User.username == "admin").first()
if not admin:
    admin = User(
        id=str(uuid.uuid4()),
        username="admin",
        hashed_password=get_password_hash("admin123"),
        role=Role.Admin
    )
    db.add(admin)
    db.commit()

# Generate long-lived token for dev
token = create_access_token(
    {"sub": admin.username, "role": admin.role.value},
    timedelta(days=365)
)

print(f"Generated Admin Token: {token}")

# Patch api.ts
api_ts_path = "frontend/lib/api.ts"
with open(api_ts_path, "r", encoding="utf-8") as f:
    api_ts_content = f.read()

# Replace the axios instance creation to include Authorization header
target = """export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});"""

replacement = f"""export const apiClient = axios.create({{
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: {{ 
    "Content-Type": "application/json",
    "Authorization": "Bearer {token}"
  }},
  timeout: 15000,
}});"""

if target in api_ts_content:
    api_ts_content = api_ts_content.replace(target, replacement)
    with open(api_ts_path, "w", encoding="utf-8") as f:
        f.write(api_ts_content)
    print("Injected token into frontend/lib/api.ts")
else:
    print("Could not find axios target to patch in api.ts")
