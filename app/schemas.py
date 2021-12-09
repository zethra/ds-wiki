from typing import List, Optional
from pydantic import BaseModel
from dataclasses import dataclass


class UserBase(BaseModel):
    name: str


class User(UserBase):
    class Config:
        orm_mode = True


class RequestPageCommit(BaseModel):
    page: str
    content: str


class RequestUserCommit(BaseModel):
    name: str
    admin: bool


class PageCommit(BaseModel):
    transaction_id: int
    page: str
    content: str


class UserCommit(BaseModel):
    transaction_id: int
    name: str
    admin: bool


class CommitReply(BaseModel):
    transaction_id: int
    sender: str
    commit: bool


class DoCommit(BaseModel):
    transaction_id: int
    commit: bool


class HaveCommit(BaseModel):
    transaction_id: int
    sender: str
    commit: bool


@dataclass
class Page:
    name: str
    content: str
