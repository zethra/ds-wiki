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
async def request_page_commit(commit: RequestPageCommit, db: Session = Depends(get_db),
                              data_servers=Depends(get_servers())):
    # new transaction:
        # find the largest transaction id (tid) in the log so far (or 1 if it dne)
        # create a new item in the log with status pending commit and all the other data to fill in
    # end transaction

    # for each server in data_servers:
        # send PageCommit msg to /can_page_commit
        # check response msg (CommitReply) and see if commit is True

    # if all commitReply are true:
        # foreach server in data_servers:
            #send DoCommit with commit=True to /do_commit
            # collect responses (HaveCommit msgs)
        # return status code 200

    # if at least one commitreply had false:
        # foreach server in data_servers:
            # send DoCommit with commit=FALSE to /do_commit
            # collect responses (HaveCommit msgs)
        # return some error status code
    pass


@app.post("/request_user_commit")
async def request_user_commit(commit: RequestUserCommit):
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
