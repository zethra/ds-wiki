"""
Webapp representing the 2 Phase Commit coordinator role.
Coordinates the distributed transaction to keep all data servers in sync.
"""

import asyncio
import httpx
from fastapi import FastAPI
from fastapi.param_functions import Depends
from sqlalchemy.orm.session import Session
from starlette.responses import Response
from starlette import status
from time import perf_counter

import start
from app import crud, models

from .database import SessionLocal, engine
from .schemas import PageCommit, UserCommit, CommitReply, DoCommit, HaveCommit, RequestUserCommit, RequestPageCommit

models.Base.metadata.create_all(bind=engine)

""" The webapp """
app = FastAPI()

""" Dictionary of useful config data """
CONFIG = {}

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
    return CONFIG['PORT']


def get_ip():
    """
    FastAPI Dependency Injection
    :return: The IP address that this server runs on.
    """
    return CONFIG['IP']


def get_servers():
    """
    FastAPI Dependency Injection
    :return: The list of IPs of data servers.
    """
    return CONFIG['SERVERS']


def get_coordinator():
    """
    FastAPI Dependency Injection
    :return: The IP of the 2PC coordinator server.
    """
    return CONFIG['COORD']


@app.on_event('startup')
async def startup_event():
    """
    Handles events that should occur on server startup.
    :return: None
    """
    # read in config
    conf = start.read_config()
    CONFIG['IP'] = conf['this_ip']
    CONFIG['PORT'] = conf['port']
    CONFIG['COORD'] = conf['coordinator']
    CONFIG['SERVERS'] = conf['replicas']
    # TODO check db log table for anything in a weird state and resolve it

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
    start = perf_counter()
    # Log table is basically a list of all commits we have attempted
    # PendingCommits tracks the status of any in-progress commits for each server participating (so pk is (tid, sender) )
    if crud.log_has_open_tranaction(db, 'page', commit.page):
        print('Aborting due to active transaction')
        return Response(status_code=status.HTTP_409_CONFLICT)

    tid = crud.new_page_commit_to_log(db, commit)

    can_commit = True
    requests = []
    for server_ip in data_servers:
        crud.new_commit_to_pending(db, tid, server_ip, 'requested')
        server_url = 'http://' + server_ip + ':8000' + '/can_page_commit'
        can_commit_data = PageCommit(transaction_id=tid, page=commit.page, content=commit.content).dict()
        requests.append((server_url, can_commit_data))

    send_can_commit = perf_counter()
    async with httpx.AsyncClient() as client:
        res = await asyncio.gather(*[client.post(url, json=req) for (url, req) in requests])
    got_can_commit = perf_counter()

    for server_response, server_ip in zip(res, data_servers):
        commit_reply = CommitReply.parse_obj(server_response.json())
        if commit_reply:
            can_commit = can_commit and commit_reply.commit
            if not commit_reply.commit:
                print('Aborting because', server_ip, 'aborted')
            crud.update_status_in_pending(db, tid, server_ip, 'promised')
        else:
            print('Aborting because', server_ip, 'sent invalid response')
            crud.update_status_in_pending(db, tid, server_ip, 'aborted')

    requests = []
    if can_commit:
        have_committed = True
        crud.update_in_log(db, tid, 'page', 'promised', commit.page, commit.content, False)
        for server_ip in data_servers:
            crud.update_status_in_pending(db, tid, server_ip, 'started')
            server_url = 'http://' + server_ip + ':8000' + '/do_commit'
            do_commit_data = DoCommit(transaction_id=tid, commit=True).dict()
            requests.append((server_url, do_commit_data))

        send_do_commit = perf_counter()

        async with httpx.AsyncClient() as client:
            res = await asyncio.gather(*[client.post(url, json=req) for (url, req) in requests])

        got_do_commit = perf_counter()

        for server_response, server_ip in zip(res, data_servers):
            have_commit_reply = HaveCommit.parse_obj(server_response.json())
            have_committed = have_committed and have_commit_reply.commit
            crud.update_status_in_pending(db, tid, server_ip, 'done')  # remove from PendingCommits db table
        crud.update_in_log(db, tid, 'page', 'done', commit.page, commit.content, False)

        done = perf_counter()

        print(f"""Start took: {send_can_commit - start}
Can commit took: {got_can_commit - send_can_commit}
Decision took: {send_do_commit - got_can_commit}
Do commit took: {got_do_commit - send_do_commit}
Finishing took: {done - got_do_commit}""")
        return Response(status_code=status.HTTP_200_OK)

    else:
        crud.update_in_log(db, tid, 'page', 'aborted', commit.page, commit.content, False)
        for server_ip in data_servers:
            crud.update_status_in_pending(db, tid, server_ip, 'aborting')
            async with httpx.AsyncClient() as client:
                server_url = 'http://' + server_ip + ':8000' + '/do_commit'
                do_commit_data = DoCommit(transaction_id=tid, commit=False).dict()
                server_response = await client.post(server_url, json=do_commit_data)
            have_commit_reply = HaveCommit.parse_obj(server_response.json())
            crud.update_status_in_pending(db, tid, server_ip, 'done')  # remove from PendingCommits db table
        crud.update_in_log(db, tid, 'page', 'aborted', commit.page, commit.content, False)
        return Response(status_code=status.HTTP_409_CONFLICT)


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
    if crud.log_has_open_tranaction(db, 'user', commit.name):
        return Response(status_code=status.HTTP_409_CONFLICT)

    tid = crud.new_user_commit_to_log(db, commit)

    can_commit = True
    for server_ip in data_servers:
        crud.new_commit_to_pending(db, tid, server_ip, 'requested')
        async with httpx.AsyncClient() as client:
            server_url = 'http://' + server_ip + ':8000' + '/can_user_commit'
            can_commit_data = UserCommit(transaction_id=tid, name=commit.name, admin=commit.admin).dict()
            server_response = await client.post(server_url, json=can_commit_data)
        commit_reply = CommitReply.parse_obj(server_response.json())
        can_commit = can_commit and commit_reply.commit
        if commit_reply:
            crud.update_status_in_pending(db, tid, server_ip, 'promised')
        else:
            crud.update_status_in_pending(db, tid, server_ip, 'aborted')

    if can_commit:
        have_committed = True
        crud.update_in_log(db, tid, 'user', 'promised', commit.name, '', commit.admin)
        for server_ip in data_servers:
            crud.update_status_in_pending(db, tid, server_ip, 'started')
            async with httpx.AsyncClient() as client:
                server_url = 'http://' + server_ip + ':8000' + '/do_commit'
                do_commit_data = DoCommit(transaction_id=tid, commit=True).dict()
                server_response = await client.post(server_url, json=do_commit_data)
            have_commit_reply = HaveCommit.parse_obj(server_response.json())
            have_committed = have_committed and have_commit_reply.commit
            crud.update_status_in_pending(db, tid, server_ip, 'done')  # remove from PendingCommits db table
        crud.update_in_log(db, tid, 'user', 'done', commit.name, '', commit.admin)
        return Response(status_code=status.HTTP_200_OK)

    else:
        crud.update_in_log(db, tid, 'user', 'aborted', commit.name, '', commit.admin)
        for server_ip in data_servers:
            crud.update_status_in_pending(db, tid, server_ip, 'aborting')
            async with httpx.AsyncClient() as client:
                server_url = 'http://' + server_ip + ':8000' + '/do_commit'
                do_commit_data = DoCommit(transaction_id=tid, commit=False).dict()
                server_response = await client.post(server_url, json=do_commit_data)
            have_commit_reply = HaveCommit.parse_obj(server_response.json())
            crud.update_status_in_pending(db, tid, server_ip, 'done')  # remove from PendingCommits db table
        crud.update_in_log(db, tid, 'user', 'aborted', commit.name, '', commit.admin)
        return Response(status_code=status.HTTP_409_CONFLICT)
