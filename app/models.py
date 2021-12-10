"""
Objects representing database rows in the SQL database/ORM model.
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    """
    Object mapping for a User in the ORM.
    id = unique identifier
    name = username
    admin = if this user has admin permissions
    """
    __tablename__ = "Users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    admin = Column(Boolean)


class Page(Base):
    """
    Object mapping for a Page in the ORM.
    id = unique identifier
    name = page name
    content = editable page content
    """
    __tablename__ = "Pages"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    content = Column(Text)


class Log(Base):
    """
    Object mapping for a Log entry in the ORM.
    Acts as a tagged union of either a commit for a user or a page.
    With more complexity/data types, this should be split into a tid and type mapping to other databases,
    one for each type of data being stored.
    tid = transaction id
    type = The type of commit {page, user}
    status = The status of the commit.
    name = The name of the page or user
    content = The contents for a webpage. Empty string for a user.
    admin = The admin rights for the user. False for a page.
    """
    __tablename__ = "Log"
    tid = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type = Column(String)
    status = Column(String)
    name = Column(String)
    content = Column(Text)
    admin = Column(Boolean)


class PendingCommits(Base):
    """
    Object mapping for the status of a given commit on a given data server.
    tid = transaction id

    """
    __tablename__ = "PendingCommits"
    tid = Column(Integer, primary_key=True, index=True)
    sender = Column(String, primary_key=True, index=True)
    status = Column(String)
