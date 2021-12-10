"""
Webapp representing the 2 Phase Commit coordinator role.
Coordinates the distributed transaction to keep all data servers in sync.
"""

from typing import Optional

from fastapi import FastAPI, Form
from fastapi.exceptions import HTTPException
from fastapi.param_functions import Cookie, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm.session import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse

import start
from app import crud, models, schemas

from .database import SessionLocal, engine
from .schemas import PageCommit, UserCommit, CommitReply, DoCommit, HaveCommit, RequestUserCommit, RequestPageCommit

models.Base.metadata.create_all(bind=engine)

""" The webapp """
app = FastAPI()


def get_db():
    """
    FastAPI Dependency Injection giving access to the db to route handlers.
    :return: The db session to be used to access the db.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_port():
    """
    FastAPI Dependency Injection
    :return: The port to run the webserver on.
    """
    return start.PORT


def get_ip():
    """
    FastAPI Dependency Injection
    :return: The IP address that this server runs on.
    """
    return start.IP


def get_servers():
    """
    FastAPI Dependency Injection
    :return: The list of IPs of data servers.
    """
    return start.SERVERS


def get_coordinator():
    """
    FastAPI Dependency Injection
    :return: The IP of the 2PC coordinator server.
    """
    return start.COORD


# This is used when a server forwards a client edit for a page request
@app.post("/request_page_commit")
async def request_page_commit(commit: RequestPageCommit, db: Session = Depends(get_db),
                              data_servers=Depends(get_servers)):
    """
    Route handler for data servers requesting to commit a change to a page.
    :param commit: The page commit JSON message to attempt to commit.
    :param db: The database to store the log in.
    :param data_servers: The data servers participating in the 2PC.
    :return: The response indicating the success of the commit.
    """
    # Log table is basically a list of all commits we have attempted
    # PendingCommits tracks the status of any in-progress commits for each server participating (so pk is (tid, sender) )

    # new transaction
        # find the largest transaction id (tid) in the log so far (or 1 if it dne)
        # create a new item in the log with status pending commit and all the other data to fill in
    # end transaction

    # for each server in data_servers:
        # add (tid, server) to PendingCommits db table with sender=server_ip and status=requested
        # send PageCommit msg to /can_page_commit
        # check response msg (CommitReply) and see if commit is True
        # update status in PendingCommits db table for that tid+sender with status=promised or aborted

    # if all commitReply are true:
        # change status of commit in log to promised
        # foreach server in data_servers:
            # update status in PendingCommits db table for that tid+sender with status=started
            # send DoCommit with commit=True to /do_commit
            # collect responses (HaveCommit msgs)
            # remove from PendingCommits db table
        # change status of commit in log to done
        # return status code 200

    # if at least one commitreply had false:
        # change status of commit in log to aborted
        # foreach server in data_servers:
            # send DoCommit with commit=FALSE to /do_commit
            # collect responses (HaveCommit msgs)
        # return some error status code
    pass


@app.post("/request_user_commit")
async def request_user_commit(commit: RequestUserCommit, db: Session = Depends(get_db),
                              data_servers=Depends(get_servers)):
    """
    Route handler for data servers requesting to commit a change to a user.
    :param commit: The user commit JSON message to attempt to commit.
    :param db: The database to store the log in.
    :param data_servers: The data servers participating in the 2PC.
    :return: The response indicating the success of the commit.
    """
    # same as above but for user commits
    pass

#
# @app.post("/commit_promise")
# async def commit_promise(promise: CommitReply):
#     #
#     pass
#
#
# @app.post("/have_committed")
# async def have_committed(reply: HaveCommit):
#     # move sender from pending to committed for that tid
#     # if this is the fourth server, then remove them all from the database
#     pass
