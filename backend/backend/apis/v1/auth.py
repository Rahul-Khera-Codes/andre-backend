from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.responses import Response, JSONResponse
from sqlalchemy.orm import Session

from common.config import settings
from backend.core.database import get_db
from backend.models.v1.users import User
from backend.schema.v1.auth import (
    AccessToken,
    RefreshToken,
    UserPasswordBase,
    UserLoginRequest,
    UserLoginResponse,
    UserRegisterRequest, 
    UserRegisterResponse,
    Token
)
from backend.utils.users import (
    get_current_active_user, 
    get_refresh_user,
    UserUtil, 
)


auth_router_v1 = APIRouter(prefix="/auth", tags=["auth"])


@auth_router_v1.post("/register", response_model=UserRegisterResponse)
async def auth_register(user_details: UserRegisterRequest, db: Session = Depends(get_db)):
    print(user_details)
    if await UserUtil.check_user_exists(user_details=user_details, db=db):
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            detail="User already exists"
        )
    user = await UserUtil.create_user(user_details=user_details, db=db)
    
    return JSONResponse(
        {"message": "Register successful with username: {}".format(user.username)},
        status_code=status.HTTP_201_CREATED
    )


@auth_router_v1.post("/login")
async def auth_login(user_details: UserLoginRequest, db: Session = Depends(get_db)):
    # if username does not exists.
    if not await UserUtil.check_user_exists(user_details=user_details, db=db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User doesn't exists"
        )
    
    user = await UserUtil.authenticate_user(username=user_details.username, password=user_details.password, db=db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await UserUtil.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token_expires = timedelta(days=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token = await UserUtil.create_refresh_token(
        data={"sub": user.username}, expires_delta=refresh_token_expires
    )
    
    token = Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
        
    return JSONResponse(
        token.model_dump(),
        status_code=status.HTTP_200_OK
    )
    
    
@auth_router_v1.post("/refresh", response_model=AccessToken)
async def auth_login(current_user: Annotated[User, Depends(get_refresh_user)]):
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await UserUtil.create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    
    token = AccessToken(token=access_token)
        
    return JSONResponse(
        token.model_dump(),
        status_code=status.HTTP_200_OK
    )
    

@auth_router_v1.post("/password-change")
async def auth_change_password(
    current_user: Annotated[User, Depends(get_current_active_user)],
    password: UserPasswordBase,
    db: Session = Depends(get_db)
):
    user = await UserUtil.change_password(current_user, password, db)
    return {"message": "Passsword change successfully."}



# @app.get("/login/google")
# async def login_via_google(request: Request):
#     redirect_uri = request.url_for('auth_google_callback')
#     return await oauth.google.authorize_redirect(request, redirect_uri)

# @app.get("/auth/callback")
# async def auth_google_callback(request: Request):
#     token = await oauth.google.authorize_access_token(request)
#     user_info = token['userinfo']  # Google OpenID Connect provides this
#     # Here you can create/get the user in DB and generate your JWT
#     return {"user": user_info}