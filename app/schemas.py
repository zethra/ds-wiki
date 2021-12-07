from typing import List, Optional

from pydantic import BaseModel

from dataclasses import dataclass

class UserBase(BaseModel):
    name: str

class User(UserBase):
    class Config:
        orm_mode = True

@dataclass
class Page:
    name: str
    content: str
