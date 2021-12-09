from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "Users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    admin = Column(Boolean)


class Page(Base):
    __tablename__ = "Pages"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    content = Column(Text)


class Log(Base):
    __tablename__ = "Log"
    tid = Column(Integer, primary_key=True, index=True)
    type = Column(String)
    status = Column(String)
    name = Column(String)
    content = Column(Text)
    admin = Column(Boolean)


class PendingCommits(Base):
    __tablename__ = "PendingCommits"
    tid = Column(Integer, primary_key=True, index=True)
    sender = Column(String, primary_key=True, index=True)
    status = Column(String)
