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

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = bcrypt.hashpw(user.password.encode("uft-8"), bcrypt.gensalt())
    db_user = models.User(name=user.name, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, user: schemas.UserAuth):
    db_user_info = get_user_by_name(db, user.name)
    return bcrypt.checkpw(user.password.encode('uft-8'), db_user_info.hashed_password.encode('uft-8'))
