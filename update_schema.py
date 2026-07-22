import re

with open('backend/db/schema.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update imports
content = content.replace('ForeignKey, CheckConstraint, Index, DateTime,', 'ForeignKey, CheckConstraint, Index, DateTime, Enum,')
content = content.replace('from sqlalchemy.sql import func', 'from sqlalchemy.sql import func\nimport enum')

# 2. Add Role Enum, User, and AuditLog
auth_schema = """
class Role(str, enum.Enum):
    Admin = "Admin"
    Analyst = "Analyst"
    Supervisor = "Supervisor"
    ReadOnly = "ReadOnly"

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(Role), default=Role.ReadOnly)
    created_at = Column(DateTime, default=func.now())

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now())
    user_id = Column(String, ForeignKey('users.id'), index=True)
    action = Column(String)
    target_id = Column(String)
    request_id = Column(String)
    ip_address = Column(String)
    status = Column(String)
"""

content = content.replace('Base = declarative_base()', 'Base = declarative_base()\n' + auth_schema)

# 3. Update Investigation class to add owner_id and assigned_team
old_inv = """class Investigation(Base):
    __tablename__ = 'investigations'
    id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(Text)
    status = Column(String)
    priority = Column(String)
    created_by = Column(String)
    assigned_officer = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())"""

new_inv = """class Investigation(Base):
    __tablename__ = 'investigations'
    id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(Text)
    status = Column(String)
    priority = Column(String)
    created_by = Column(String)
    assigned_officer = Column(String)
    owner_id = Column(String, ForeignKey("users.id"))
    assigned_team = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())"""

content = content.replace(old_inv, new_inv)

with open('backend/db/schema.py', 'w', encoding='utf-8') as f:
    f.write(content)
