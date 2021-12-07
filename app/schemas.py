from typing import List, Optional

from pydantic import BaseModel

class UserBase(BaseModel):
    name: str

class User(UserBase):
    class Config:
        orm_mode = True

