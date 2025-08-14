from typing import Literal

from pydantic import BaseModel, field_validator


class UserBase(BaseModel):
    username: str
    
    @field_validator("username", mode='before')
    @classmethod
    def validate_username(cls, value):
        if value is None:
            raise ValueError("Username cannot be empty")
        
        return value.lower()
    
class UserEmailBase(BaseModel):
    email: str
    
    @field_validator("email", mode='before')
    @classmethod
    def validate_email(cls, value):
        if value is None or not value:
            raise ValueError("Email cannot be empty")
        
        return value.lower()
    
class UserPasswordBase(BaseModel):
    password: str
    
    @field_validator("password", mode='before')
    @classmethod
    def validate_password(cls, value):
        # TODO: put password validation
        return value


class UserRegisterRequest(UserBase, UserEmailBase, UserPasswordBase):
    ...


class UserRegisterResponse(BaseModel):
    message: str


class UserLoginRequest(UserBase, UserPasswordBase):
    ...

    
class UserLoginResponse(BaseModel):
    ...


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal['bearer']
    
class AccessToken(BaseModel):
    token: str
    

class RefreshToken(BaseModel):
    token: str
    