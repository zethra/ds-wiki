"""
Holds the common database operations that are used.
"""
from sqlalchemy.orm import Session

from . import models, schemas
from .schemas import RequestPageCommit, RequestUserCommit


def no_users(db: Session) -> bool:
    """
    :param db: The db session to check.
    :return: If there are no users currently registered in the db.
    """
    return db.query(models.User).count() == 0


def get_user(db: Session, user_id: int) -> models.User:
    """
    Get the user with the given id
    :param db: The db session to check.
    :param user_id: The unique id for the user we are checking.
    :return: The user with the given id, or None if DNE.
    """
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_name(db: Session, name: str) -> models.User:
    """
    Get the user with the given name.
    :param db: The db session to check.
    :param name: The name fo the user we are checking.
    :return: The user with the given name, or None if DNE.
    """
    return db.query(models.User).filter(models.User.name == name).first()


def get_users(db: Session) -> models.User:
    """
    Get all the users currently registered.
    :param db: The db session to check.
    :return: All of the users currently registered in the db.
    """
    return db.query(models.User).all()


def create_user(db: Session, user: str, admin: bool) -> models.User:
    """
    Add a user to the database.
    :param db: The db session to use.
    :param user: The name of the user to create.
    :param admin: If the user has admin rights.
    :return: The newly created user object.
    """
    db_user = models.User(name=user, admin=admin)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_admin(db: Session, user: str, admin: bool):
    """
    Update the admin rights for the given user.
    :param db: The db session to use.
    :param user: The name of the user to update.
    :param admin: The new value for the admin rights for the user.
    :return: None.
    """
    db.query(models.User).filter(models.User.name == user).update({models.User.admin: admin})
    db.commit()


def search_page(db: Session, name: str) -> models.Page:
    """
    Search for a page in the db with a name similar to the name argument.
    :param db: The db session to use.
    :param name: The name of the page to search for.
    :return: The pages with a name similar to the searched name.
    """
    print("Query: " + str(db.query(models.Page)))
    print("All: " + str(db.query(models.Page).all()))
    return db.query(models.Page).filter(models.Page.name.like('%' + name + '%')).all()


def all_pages(db: Session) -> models.Page:
    """
    Get a list of all pages in the db.
    :param db: The db session to use.
    :return: The list of all pages in the db.
    """
    return db.query(models.Page).all()


def get_page(db: Session, name: str) -> models.Page:
    """
    Get the page with the given name.
    :param db: The db session to check.
    :param name: The name of the page to find.
    :return: The desired page in the db, or None if DNE.
    """
    return db.query(models.Page).filter(models.Page.name == name).first()


def create_page(db: Session, page: schemas.Page) -> models.Page:
    """
    Create a page and add it to the db.
    :param db: The db session to check.
    :param page: The name of the page to create.
    :return: The created page.
    """
    db_page = models.Page(name=page.name, content=page.content)
    db.add(db_page)
    db.commit()
    db.refresh(db_page)
    return db_page


def tid_in_log(db: Session, tid: int) -> bool:
    """
    Check if the tid is already present in the commit log.
    :param db: The db session to check.
    :param tid: The tid to check for.
    :return: True if the tid is already present in the commit log, False otherwise.
    """
    return db.query(models.Log).filter(models.Log.tid == tid).count() > 0


def get_log(db: Session, tid: int) -> models.Log:
    """
    Get the commit log with the given tid.
    :param db: The db session to check.
    :param tid: The tid for the given commit.
    :return: The log with the data about that commit.
    """
    return db.query(models.Log).filter(models.Log.tid == tid).first()


def add_to_log(db: Session, tid: int, ttype: str, status: str, name: str, content: str = " ", admin: bool = False):
    """
    Add the given commit to the log.
    :param db: The db session to add to.
    :param tid: The transaction id for this transaction.
    :param ttype: The type of commit to be performed. {user, page}
    :param status: The current running status of the commit.
    :param name: The name of the page/user being committed.
    :param content: The content of the page being committed. "" for user.
    :param admin: The admin rights of the user being committed. None for page.
    :return: None
    """
    db_log = models.Log(tid=tid, type=ttype, status=status, name=name, conten=content, admin=admin)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)


def update_in_log(db: Session, tid: int, ttype: str, status: str, name: str, content: str = '', admin: bool = False):
    """
    Update the given commit (identified by tid) in the log.
    :param db: The db session to update in.
    :param tid: The transaction id for this transaction.
    :param ttype: The type of commit to be performed. {user, page}
    :param status: The current running status of the commit.
    :param name: The name of the page/user being committed.
    :param content: The content of the page being committed. "" for user.
    :param admin: The admin rights of the user being committed. None for page.
    :return: None
    """
    db_log = models.Log(tid=tid, type=ttype, status=status, name=name, conten=content, admin=admin)
    db.query(models.Log).filter(models.Log.tid == tid).update({models.Log.status: status, models.Log.name: name,
                                                               models.Log.content: content, models.Log.admin: admin})
    db.commit()
    db.refresh(db_log)


def update_page_content(db: Session, page_name: str, page_content: str):
    """
    Update the contents of the given page in the db.
    :param db: The db session to update in.
    :param page_name: The name of the page to update.
    :param page_content: The contents of the page to be updated.
    :return: None.
    """
    print('update page', page_name, 'with', page_content)
    db.query(models.Page).filter(models.Page.name == page_name).update({models.Page.content: page_content},
                                                                       synchronize_session=False)
    db.commit()


def create_or_update_user(db: Session, tid: int):
    """
    Commit the user commit to the db.
    :param db: The db session to use.
    :param tid: The tid of the entry in the log to commit.
    :return: None
    """
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
    """
    Commit the page coommit to the db.
    :param db: The db session to use.
    :param tid: The tid of the entry in the log to commit.
    :return: None.
    """
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


def new_page_commit_to_log(db: Session, commit: RequestPageCommit):
    """
    Create a new page commit entry in the log
    :param db: The db session to use.
    :param commit: The page commit to try to commit.
    :return: The tid of the newly created transaction log entry.
    """
    with db.begin():
        db_log = models.Log(type='page', status='pending', name=commit.page, content=commit.content, admin=False)
        db.refresh(db_log)  # updates db_log to have the db assigned tid
        tid = db_log.tid
    return tid


def new_user_commit_to_log(db: Session, commit: RequestUserCommit):
    """
    Create a new user commit entry in the log.
    :param db: The db session to use.
    :param commit: The user commit to try to commit.
    :return: The tid fo the newly created transaction log entry.
    """
    with db.begin():
        db_log = models.Log(type='page', status='pending', name=commit.name, content='', admin=commit.admin)
        db.refresh(db_log)
        tid = db_log.tid
    return tid
