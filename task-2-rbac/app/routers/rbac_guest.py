from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Tuple

from .. import crud, models, schemas, security
from ..database import get_db

router = APIRouter(
    prefix="/guest",
    tags=["Guest Access"]
)

# This is a special dependency that returns the link and resource if token is valid
GuestAccessDependency = Depends(security.get_resource_from_share_token)

@router.get("/access/{token}", response_model=schemas.Resource, name="access_resource_via_guest_link")
def read_resource_as_guest(
    link_and_resource: Tuple[models.ShareableLink, models.Resource] = GuestAccessDependency
):
    link, resource = link_and_resource
    # Both VIEW and EDIT permissions allow reading
    return resource

@router.put("/access/{token}", response_model=schemas.Resource)
def update_resource_as_guest(
    resource_update: schemas.ResourceCreate,
    db: Session = Depends(get_db),
    link_and_resource: Tuple[models.ShareableLink, models.Resource] = GuestAccessDependency
):
    link, resource = link_and_resource
    
    if link.permission_level != models.ShareableLinkPermission.EDIT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This link does not grant edit permissions."
        )
    
    return crud.update_resource(db=db, resource=resource, resource_update=resource_update)