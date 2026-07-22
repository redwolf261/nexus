import sys
import os
sys.path.append('.')

from backend.auth.security import create_access_token
from backend.db.schema import Role
from datetime import timedelta

token = create_access_token(
    {'sub': 'admin', 'role': Role.Admin.value},
    timedelta(days=365)
)

api_ts_path = 'frontend/lib/api.ts'
with open(api_ts_path, 'r', encoding='utf-8') as f:
    api_ts_content = f.read()

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
    with open(api_ts_path, 'w', encoding='utf-8') as f:
        f.write(api_ts_content)
    print('Successfully patched frontend API with mock admin token.')
else:
    print('Target not found in api.ts')
