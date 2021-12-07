from sys import modules
import bcrypt
from sqlalchemy.orm import Session

from . import models, schemas

def get_user(db: Session, user_id: int) -> models.User:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_name(db: Session, name: str) -> models.User:
    return db.query(models.User).filter(models.User.name == name).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> models.User:
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: str) -> models.User:
    db_user = models.User(name=user)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_user_x(db: Session, user: schemas.User) -> models.User:
    db_user = models.User(name=user.name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
