from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Page(Base):
    __tablename__ = "pages"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    content = Column(Text)
    
