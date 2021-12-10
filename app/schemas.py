"""
Pydantic JSON objects used for passing messages in the two phase commit.
"""

from typing import List, Optional
from pydantic import BaseModel
from dataclasses import dataclass


class UserBase(BaseModel):
    name: str


class User(UserBase):
    class Config:
        orm_mode = True


class RequestPageCommit(BaseModel):
    """
    JSON message from the data server to the coordinator indicating
    that they want the coordinator to update the page to have the given data.
    page = the name fo the page to edit or create
    content = the content to display on the page
    """
    page: str
    content: str


class RequestUserCommit(BaseModel):
    """
    JSON message sent from the data server to the coordinator indicating
    that they want the coordinator to update the user to have the given data.
    name = the name of the user to edit or create
    admin = the permission level the user will have
    """
    name: str
    admin: bool


class PageCommit(BaseModel):
    """
    JSON message sent from the coordinator to the data server indicating
    that they want to start the process to commit a change to a page
    (1st step in 2PC).
    transaction_id = the id of the transaction
    name = the name of the page to update or create
    content = the data displayed on the page
    """
    transaction_id: int
    page: str
    content: str


class UserCommit(BaseModel):
    """
    JSON message sent from the coordinator to the data server indicating
    that they want to start the process to commit a change to a user
    (1st step in 2PC).
    transaction_id = the id of the transaction
    name = the name of the user to update or create
    admin = what level of permission the user has
    """
    transaction_id: int
    name: str
    admin: bool


class CommitReply(BaseModel):
    """
    JSON message sent from the data server to the coordinator
    indicating that they are willing to commit or not (2nd step in 2PC).
    transaction_id = the id of the transaction to commit or abort
    sender = the ip of the data server
    commit = if the data server is willing to commit or if it will abort
    """
    transaction_id: int
    sender: str
    commit: bool


class DoCommit(BaseModel):
    """
    JSON message sent from the coordinator to the data server
    indicating that they should proceed with the commit or abort
    the commit (3rd step in 2PC)
    transaction_id = the id of the transaction to commit or abort
    commit = if the data server should commit or abort
    """
    transaction_id: int
    commit: bool


class HaveCommit(BaseModel):
    """
    JSON message sent from the data server to the coordinator
    indicating that they have committed (4th step in the 2PC)
    transaction_id = the id of the transaction to commit
    sender = the ip of the data server
    commit = if the server commit or not
    """
    transaction_id: int
    sender: str
    commit: bool


@dataclass
class Page:
    """
    Represents a page.
    """
    name: str
    content: str
