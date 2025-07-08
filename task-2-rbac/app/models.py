from sqlalchemy import (Column, Integer, String, Enum, ForeignKey, 
                        DateTime, UniqueConstraint)
from sqlalchemy.orm import relationship
from .database import Base
import enum as python_enum
from datetime import datetime

class RoleEnum(str, python_enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    CONTRIBUTOR = "contributor"
    VIEWER = "viewer"

class ShareableLinkPermission(str, python_enum.Enum):
    VIEW = "view"
    EDIT = "edit"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User")
    departments = relationship("Department", back_populates="organization", cascade="all, delete-orphan")

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    organization = relationship("Organization", back_populates="departments")
    resources = relationship("Resource", back_populates="department", cascade="all, delete-orphan")
    members = relationship("DepartmentMembership", back_populates="department", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint('name', 'organization_id', name='_name_org_uc'),)

class DepartmentMembership(Base):
    __tablename__ = "department_memberships"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    
    # --- THE DEFINITIVE FIX IS HERE ---
    # This tells SQLAlchemy to use a VARCHAR + CHECK constraint, which Alembic understands perfectly.
    role = Column(Enum(RoleEnum, native_enum=False), nullable=False)
    
    user = relationship("User")
    department = relationship("Department", back_populates="members")
    __table_args__ = (UniqueConstraint('user_id', 'department_id', name='_user_dept_uc'),)

class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    content = Column(String)
    department_id = Column(Integer, ForeignKey("departments.id"))
    department = relationship("Department", back_populates="resources")

class ShareableLink(Base):
    __tablename__ = "shareable_links"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id"))

    # --- THE DEFINITIVE FIX IS HERE ---
    permission_level = Column(Enum(ShareableLinkPermission, native_enum=False), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    resource = relationship("Resource")