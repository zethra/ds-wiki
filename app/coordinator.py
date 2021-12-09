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

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_port():
    return start.PORT


def get_ip():
    return start.IP


def get_servers():
    return start.SERVERS


def get_coordinator():
    return start.COORD


# This is used when a server forwards a client edit for a page request
@app.post("/request_page_commit")
async def request_page_commit(commit: RequestPageCommit):
    # create a pending commit in the log
    # send can_commit to each of the servers for the transaction
    # if all are willing to commit:
        # send do_commit:commit to all
        # once they all succeed at that
        # return 200
    # if not
        # send do_commit: abort to all
        # return 409
    pass


@app.post("/request_user_commit")
async def request_user_commit(commit: RequestUserCommit):
    # create a pending commit in the log
    # add each server to the pending_commit log as requested
    # send can_commit to each of the servers for the transaction
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
