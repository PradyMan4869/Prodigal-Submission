from sqlalchemy.orm import Session
from . import models, schemas, security
from datetime import datetime, timedelta

# --- User CRUD ---
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Organization CRUD ---
def get_organization(db: Session, org_id: int):
    return db.query(models.Organization).filter(models.Organization.id == org_id).first()

def create_organization(db: Session, org: schemas.OrganizationCreate, owner_id: int):
    db_org = models.Organization(**org.dict(), owner_id=owner_id)
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org

# --- Department CRUD ---
def get_department(db: Session, department_id: int):
    return db.query(models.Department).filter(models.Department.id == department_id).first()

def create_department(db: Session, department: schemas.DepartmentCreate, org_id: int):
    db_department = models.Department(**department.dict(), organization_id=org_id)
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department

# --- Membership CRUD ---
def get_department_membership(db: Session, user_id: int, department_id: int):
    return db.query(models.DepartmentMembership).filter(
        models.DepartmentMembership.user_id == user_id,
        models.DepartmentMembership.department_id == department_id
    ).first()

def create_department_membership(db: Session, membership: schemas.DepartmentMembershipCreate, department_id: int):
    db_membership = models.DepartmentMembership(**membership.dict(), department_id=department_id)
    db.add(db_membership)
    db.commit()
    db.refresh(db_membership)
    return db_membership

# --- Resource CRUD ---
def get_resource(db: Session, resource_id: int):
    return db.query(models.Resource).filter(models.Resource.id == resource_id).first()

def create_resource(db: Session, resource: schemas.ResourceCreate, department_id: int):
    db_resource = models.Resource(**resource.dict(), department_id=department_id)
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    return db_resource

def update_resource(db: Session, resource: models.Resource, resource_update: schemas.ResourceCreate):
    resource.filename = resource_update.filename
    resource.content = resource_update.content
    db.commit()
    db.refresh(resource)
    return resource

# --- Shareable Link CRUD ---
def create_shareable_link(db: Session, resource_id: int, permission_level: models.ShareableLinkPermission, token: str, expires_in_minutes: int = None):
    expires_at = None
    if expires_in_minutes:
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)

    db_link = models.ShareableLink(
        token=token,
        resource_id=resource_id,
        permission_level=permission_level,
        expires_at=expires_at
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

def get_link_by_token(db: Session, token: str):
    return db.query(models.ShareableLink).filter(models.ShareableLink.token == token).first()