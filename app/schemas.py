from typing import List, Optional

from pydantic import BaseModel

class UserBase(BaseModel):
    name: str

class UserCreate(UserBase):
    password: str

class UserAuth(UserBase):
    password: str

class User(UserBase):
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str
