from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
import secrets

from .. import crud, models, schemas, security
from ..database import get_db

router = APIRouter(
    prefix="/api",
    tags=["RBAC System"],
    dependencies=[Depends(security.get_current_user)],
)

# --- Organization ---
@router.post("/organizations", response_model=schemas.Organization, status_code=status.HTTP_201_CREATED)
def create_organization(
    org: schemas.OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    return crud.create_organization(db=db, org=org, owner_id=current_user.id)

# --- Department ---
@router.post("/organizations/{org_id}/departments", response_model=schemas.Department, status_code=status.HTTP_201_CREATED)
def create_department_in_org(
    org_id: int,
    department: schemas.DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    db_org = crud.get_organization(db, org_id)
    if not db_org:
        raise HTTPException(status_code=404, detail="Organization not found")
    if db_org.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the organization owner can create departments")
    return crud.create_department(db=db, department=department, org_id=org_id)

# --- Membership & Roles ---
@router.post("/departments/{department_id}/members", response_model=schemas.DepartmentMembership)
def add_member_to_department(
    department_id: int,
    membership: schemas.DepartmentMembershipCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_permission_checker(models.RoleEnum.MANAGER))
):
    user_to_add = crud.get_user(db, membership.user_id)
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User to be added not found")
    existing_membership = crud.get_department_membership(db, user_id=membership.user_id, department_id=department_id)
    if existing_membership:
        raise HTTPException(status_code=400, detail="User is already a member of this department")
    return crud.create_department_membership(db, membership, department_id)

# --- Resources ---
@router.post("/departments/{department_id}/resources", response_model=schemas.Resource, status_code=status.HTTP_201_CREATED)
def create_resource_in_department(
    department_id: int,
    resource: schemas.ResourceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_permission_checker(models.RoleEnum.CONTRIBUTOR))
):
    return crud.create_resource(db=db, resource=resource, department_id=department_id)

@router.get("/resources/{resource_id}", response_model=schemas.Resource)
def view_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    resource = crud.get_resource(db, resource_id=resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # Check permission on the resource's department
    _ = security.get_permission_checker(models.RoleEnum.VIEWER)(
        department_id=resource.department_id, db=db, current_user=current_user
    )
    return resource

# --- Sharing ---
@router.post("/resources/{resource_id}/share", response_model=schemas.ShareableLink)
def create_shareable_link_for_resource(
    resource_id: int,
    link_details: schemas.ShareableLinkCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    resource = crud.get_resource(db, resource_id=resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    # Check permission to share (e.g., Manager level)
    _ = security.get_permission_checker(models.RoleEnum.MANAGER)(
        department_id=resource.department_id, db=db, current_user=current_user
    )
    
    token = secrets.token_urlsafe(32)
    db_link = crud.create_shareable_link(
        db=db,
        resource_id=resource_id,
        permission_level=link_details.permission_level,
        token=token,
        expires_in_minutes=link_details.expires_in_minutes
    )

    # Construct the full URL for the client
    guest_url = request.url_for('access_resource_via_guest_link', token=token)
    
    return schemas.ShareableLink(
        token=db_link.token,
        url=str(guest_url),
        permission_level=db_link.permission_level,
        expires_at=db_link.expires_at
    )