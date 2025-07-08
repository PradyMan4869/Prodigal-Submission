from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from .models import RoleEnum, ShareableLinkPermission

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    class Config:
        orm_mode = True

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Resource Schemas ---
class ResourceBase(BaseModel):
    filename: str
    content: Optional[str] = None

class ResourceCreate(ResourceBase):
    pass

class Resource(ResourceBase):
    id: int
    department_id: int
    class Config:
        orm_mode = True

# --- Membership Schemas ---
class DepartmentMembershipCreate(BaseModel):
    user_id: int
    role: RoleEnum

class DepartmentMembership(BaseModel):
    id: int
    user: User
    role: RoleEnum
    class Config:
        orm_mode = True

# --- Department Schemas ---
class DepartmentBase(BaseModel):
    name: str

class DepartmentCreate(DepartmentBase):
    pass

class Department(DepartmentBase):
    id: int
    organization_id: int
    resources: List[Resource] = []
    members: List[DepartmentMembership] = []
    class Config:
        orm_mode = True

# --- Organization Schemas ---
class OrganizationBase(BaseModel):
    name: str

class OrganizationCreate(OrganizationBase):
    pass

class Organization(OrganizationBase):
    id: int
    owner_id: int
    departments: List[Department] = []
    class Config:
        orm_mode = True

# --- Shareable Link Schemas ---
class ShareableLinkCreate(BaseModel):
    permission_level: ShareableLinkPermission
    expires_in_minutes: Optional[int] = None

class ShareableLink(BaseModel):
    token: str
    url: str # We'll construct this dynamically
    permission_level: ShareableLinkPermission
    expires_at: Optional[datetime]
    class Config:
        orm_mode = True