from sys import modules
import bcrypt
from sqlalchemy.orm import Session

from . import models, schemas

def get_user(db: Session, user_id: int) -> models.User:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_name(db: Session, name: str) -> models.User:
    return db.query(models.User).filter(models.User.name == name).first()

def get_users(db: Session) -> models.User:
    return db.query(models.User).all()

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

def search_page(db: Session, name: str) -> models.Page:
    return db.query(models.Page).filter(models.Page.name.like('%' + name + '%')).all()

def get_page(db: Session, name: str) -> models.Page:
    return db.query(models.Page).filter(models.Page.name == name).first()

def create_page(db: Session, page: schemas.Page) -> models.Page:
    db_page = models.Page(name=page.name, content=page.content)
    db.add(db_page)
    db.commit()
    db.refresh(db_page)
    return db_page

def update_page_content(db: Session, page_name: str, page_content: str):
    print('update page', page_name, 'with', page_content)
    db.query(models.Page).filter(models.Page.name == page_name).update({models.Page.content: page_content}, synchronize_session = False)
    db.commit()
