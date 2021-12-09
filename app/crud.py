from sys import modules
import bcrypt
from sqlalchemy.orm import Session

from . import models, schemas


def no_users(db: Session) -> bool:
    return db.query(models.User).count() == 0


def get_user(db: Session, user_id: int) -> models.User:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_name(db: Session, name: str) -> models.User:
    return db.query(models.User).filter(models.User.name == name).first()


def get_users(db: Session) -> models.User:
    return db.query(models.User).all()


def create_user(db: Session, user: str, admin: bool) -> models.User:
    db_user = models.User(name=user, admin=admin)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_admin(db: Session, user: str, admin: bool):
    db.query(models.User).filter(models.User.name == user).update({models.User.admin: admin})
    db.commit()


def search_page(db: Session, name: str) -> models.Page:
    print("Query: " + str(db.query(models.Page)))
    print("All: " + str(db.query(models.Page).all()))
    return db.query(models.Page).filter(models.Page.name.like('%' + name + '%')).all()


def all_pages(db: Session) -> models.Page:
    return db.query(models.Page).all()


def get_page(db: Session, name: str) -> models.Page:
    return db.query(models.Page).filter(models.Page.name == name).first()


def create_page(db: Session, page: schemas.Page) -> models.Page:
    db_page = models.Page(name=page.name, content=page.content)
    db.add(db_page)
    db.commit()
    db.refresh(db_page)
    return db_page


def tid_in_log(db: Session, tid: int) -> bool:
    return db.query(models.Log).filter(models.Log.tid == tid).count() > 0


def get_log(db: Session, tid: int) -> models.Log:
    return db.query(models.Log).filter(models.Log.tid == tid).first()


def add_to_log(db: Session, tid: int, ttype: str, status: str, name: str, content: str = " ", admin: bool = False):
    db_log = models.Log(tid=tid, type=ttype, status=status, name=name, conten=content, admin=admin)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)


def update_in_log(db: Session, tid: int, ttype: str, status: str, name: str, content: str = '', admin: bool = False):
    db_log = models.Log(tid=tid, type=ttype, status=status, name=name, conten=content, admin=admin)
    db.query(models.Log).filter(models.Log.tid == tid).update({models.Log.status: status, models.Log.name: name,
                                                               models.Log.content: content, models.Log.admin: admin})
    db.commit()
    db.refresh(db_log)


def update_page_content(db: Session, page_name: str, page_content: str):
    print('update page', page_name, 'with', page_content)
    db.query(models.Page).filter(models.Page.name == page_name).update({models.Page.content: page_content},
                                                                       synchronize_session=False)
    db.commit()


def create_or_update_user(db: Session, tid: int):
    db_user = None
    with db.begin():  # commits at end or rollback on exception
        to_commit = get_log(db, tid)
        existing_user = get_user_by_name(db, to_commit.name)
        if existing_user:
            db.query(models.User).filter(models.User.name == to_commit.name).update({models.User.admin: to_commit.admin})
        else:
            db_user = models.User(name=to_commit.name, admin=to_commit.admin)
            db.add(db_user)
    if db_user:
        db.refresh(db_user)


def create_or_update_page(db: Session, tid: int):
    db_page = None
    with db.begin():  # commits at end or rollback on exception
        to_commit = get_log(db, tid)
        existing_page = get_page(db, to_commit.name)
        if existing_page:
            db.query(models.Page).filter(models.Page.name == to_commit.name).update({models.Page.content: to_commit.content})
        else:
            db_page = models.Page(name=to_commit.name, content=to_commit.content)
            db.add(db_page)
    if db_page:
        db.refresh(db_page)

