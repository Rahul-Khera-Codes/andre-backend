from datetime import (
    datetime,
    timedelta,
    timezone
)
from typing import Annotated

from fastapi import (
    Depends,
    status,
    Request
)
from fastapi.exceptions import HTTPException
import jwt
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from backend.models.v1.users import User
from backend.schema.v1.auth import (
    RefreshToken,
    UserBase,
    UserPasswordBase,
    UserRegisterRequest,
)
from backend.core.hashing import get_password_hash, verify_password
from backend.core.oauth import oauth2_scheme
from backend.core.database import get_db
from common.config import settings


class UserUtil:
    @classmethod
    async def check_user_exists(cls, user_details: UserRegisterRequest, db: Session):
        users = db.query(User).filter_by(username=user_details.username).all()
        if users.__len__() != 0:
            return True
        return False
    
    
    @classmethod
    async def create_user(cls, user_details: UserRegisterRequest, db: Session):
        hash_password = await get_password_hash(user_details.password)
        user = User(username=user_details.username, email=user_details.email, password = hash_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    
    @classmethod
    async def get_user(cls, username: str, db: Session):
        user = db.query(User).filter_by(username=username).one()
        return user
    

    @classmethod
    async def authenticate_user(cls, username: str, password: str, db: Session):
        user = await cls.get_user(username, db)
        if not user:
            return 
        if not await verify_password(password, user.password):
            return 
        return user


    @classmethod
    async def create_access_token(cls, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    
    @classmethod
    async def create_refresh_token(cls, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=15)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @classmethod
    async def get_password_hash(cls, raw_password: str) -> str:
        return await get_password_hash(raw_password)
    
    @classmethod
    async def change_password(cls, current_user: User, password: UserPasswordBase, db: Session) -> None:
        current_user.password = await cls.get_password_hash(password.password)
        # db.add(current_user)
        db.commit()
        db.refresh(current_user)
        return current_user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        token_type = payload.get("type")
        if username is None or token_type == 'refresh':
            raise credentials_exception
        token_data = UserBase(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = await UserUtil.get_user(username=token_data.username, db=db)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    # if current_user.disabled:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


class GetRefreshFromRequest:
    async def __call__(self, request: Request) -> str:
        body = await request.json()
        refresh = RefreshToken(**body)
        return refresh.token

async def get_refresh_user(token: Annotated[str, Depends(GetRefreshFromRequest())], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid token"
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        token_type = payload.get("type")
        if username is None or token_type == 'access':
            raise credentials_exception
        token_data = UserBase(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = await UserUtil.get_user(username=token_data.username, db=db)
    if user is None:
        raise credentials_exception
    return user