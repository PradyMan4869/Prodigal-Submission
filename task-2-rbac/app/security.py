import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from . import crud, models, schemas
from .database import get_db

load_dotenv()

# --- Configuration ---
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# --- Hashing & JWT ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Core Dependencies ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

# --- Permission-Checking Dependencies ---
ROLE_HIERARCHY = {
    models.RoleEnum.VIEWER: 1,
    models.RoleEnum.CONTRIBUTOR: 2,
    models.RoleEnum.MANAGER: 3,
    models.RoleEnum.ADMIN: 4
}

def get_permission_checker(required_role: models.RoleEnum):
    def permission_checker(
        department_id: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
    ):
        membership = crud.get_department_membership(db, user_id=current_user.id, department_id=department_id)
        
        if not membership:
            # Maybe the user is the organization owner?
            department = crud.get_department(db, department_id)
            if not department or department.organization.owner_id != current_user.id:
                 raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this department")
            # Org owner has full ADMIN rights
            user_level = ROLE_HIERARCHY[models.RoleEnum.ADMIN]
        else:
            user_level = ROLE_HIERARCHY.get(membership.role, 0)

        required_level = ROLE_HIERARCHY.get(required_role, 99)

        if user_level < required_level:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Insufficient permissions. Requires {required_role.value}")
        
        return current_user
    
    return permission_checker

def get_resource_from_share_token(
    token: str,
    db: Session = Depends(get_db),
):
    link = crud.get_link_by_token(db, token=token)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share link not found or invalid")
    
    if link.expires_at and link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Share link has expired")
    
    resource = crud.get_resource(db, resource_id=link.resource_id)
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original resource not found")
        
    return link, resource