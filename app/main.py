"""
Webapp for a data server.
"""

from typing import Optional

import httpx
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
from .schemas import PageCommit, DoCommit, UserCommit, CommitReply, HaveCommit, RequestUserCommit, RequestPageCommit

models.Base.metadata.create_all(bind=engine)

""" The webapp """
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

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


@app.get("/")
async def index(request: Request, db: Session = Depends(get_db), user: Optional[str] = Cookie(None)):
    """
    GET route handler for the home page of the webapp.
    :param request: The client request for the page.
    :param db: Dependency for the db session.
    :param user: The user name cookie.
    :return: The home page to be displayed to the client.
    """
    admin = False
    if user:
        current_user = crud.get_user_by_name(db, user)
        if current_user and current_user.admin:
            admin = True
    return templates.TemplateResponse("index.html", {'request': request, 'admin': admin, 'user': user})


@app.get("/login")
async def login(request: Request):
    """
    GET route handler for the login page of the webapp.
    :param request: The client request for the page.
    :return: The login page to be displayed to the client.
    """
    return templates.TemplateResponse("login.html", {'request': request})


@app.post("/login")
async def login_post(request: Request, user: str = Form(...), db: Session = Depends(get_db)):
    """
    POST route handler for the login page of the webapp
    :param user: The form data for the user name to use to login.
    :param db: Dependency for the db session.
    :return: The response to the user based on their login attempt.
    """
    existing_user = crud.get_user_by_name(db, user)
    if existing_user:
        response = RedirectResponse("/", status_code=303)
        response.set_cookie(key='user', value=existing_user.name)
        return response
    else:
        return templates.TemplateResponse("user_not_found.html", {'request': request, 'user': user})


@app.get("/logout")
async def logout():
    """
    GET route handler for the logout page of the webapp.
    :return: The logout page to be displayed to the client.
    """
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(key='user', value='')
    return response


@app.get("/create")
async def create(request: Request):
    """
    GET route handler for the create user page of the webapp.
    :param request: The request sent in from the client.
    :return: The create user page for the client.
    """
    return templates.TemplateResponse("create.html", {'request': request})


@app.post("/create")
async def create_post(user: str = Form(...), db: Session = Depends(get_db), coord: str = Depends(get_coordinator)):
    """
    POST route handler for the create user page of the webapp.
    :param user: The name of the user to create.
    :param db: The db session to get the data from.
    :param coord: The coordinator server ip.
    :return: The redirect for the user to the page associated with logging in or failed creation of the user.
    """
    existing_user = crud.get_user_by_name(db, user)
    if existing_user:
        return HTTPException(status_code=400, detail="User already registered")
    else:
        admin = crud.no_users(db)
        # new_user = crud.create_user(db, user, admin)
        data = RequestUserCommit(name=user, admin=admin).dict()
        async with httpx.AsyncClient() as client:
            coord_url = 'http://' + coord + ':8000' + '/request_user_commit'
            print(f'create_post: connecting to {coord_url}')
            coord_response = await client.post(coord_url, json=data)
        if coord_response.status_code == 200:
            response = RedirectResponse("/login", status_code=303)
            return response
        else:
            response = RedirectResponse("/create_user_failed", status_code=303)
            return response


@app.get("/edit_page/{page_name}")
async def edit_page(page_name: str, request: Request, db: Session = Depends(get_db),
                    coord: str = Depends(get_coordinator), user: Optional[str] = Cookie(None)):
    """
    GET route handler for the webpage to edit a page on the page_name topic.
    :param page_name: The name of the page requested by the client.
    :param request: The request the client passed
    :param db: The database session to get info from.
    :param coord: The ip of the coordinator server for 2PC.
    :param user: The user accessing the page.
    :return: Either the edit webpage or the login screen if the user is not logged in.
    """
    if user:
        existing_user = crud.get_user_by_name(db, user)
        page = crud.get_page(db, page_name)
        if page is None:
            if existing_user.admin:
                # page = crud.create_page(db, schemas.Page(page_name, ""))
                data = RequestPageCommit(page=page_name, content='').dict()
                async with httpx.AsyncClient() as client:
                    coord_url = 'http://' + coord + ':8000' + '/request_page_commit'
                    coord_response = await client.post(coord_url, json=data)
                if coord_response.status_code == 200:
                    # 200 indicates that the db has been updated
                    page = crud.get_page(db, page_name)
                    response = templates.TemplateResponse("edit_page.html", {'request': request, 'name': page.name, 'content': page.content})
                    return response
                else:
                    response = RedirectResponse("/create_page_failed", status_code=303)
                    return response
            else:
                return RedirectResponse(f"/login", status_code=303)
        return templates.TemplateResponse("edit_page.html", {'request': request, 'name': page.name, 'content': page.content})
    else:
        return RedirectResponse(f"/login", status_code=303)


@app.post("/edit_page")
async def edit_page_post(name: str = Form(...), content: str = Form(...), db: Session = Depends(get_db),
                         coord: str = Depends(get_coordinator), user: Optional[str] = Cookie(None)):
    """
    POST route handler for applying the edits made by a user.
    :param name: The name of the page that was edited.
    :param content: The new value for the content for the page.
    :param db: The database where info can be found.
    :param coord: The ip of the coordinator for 2PC.
    :param user: The user making the edits.
    :return: Redirect to login if the user is not logged in, or either the page, or a page indicating edit failure.
    """
    if user:
        # crud.update_page_content(db, name, content)
        data = RequestPageCommit(page=name, content=content).dict()
        async with httpx.AsyncClient() as client:
            coord_url = 'http://' + coord + ':8000' + '/request_page_commit'
            coord_response = await client.post(coord_url, json=data)
        if coord_response.status_code == 200:
            # 200 indicates that the db has been updated
            response = RedirectResponse(f"/page/{name}", status_code=303)
            return response
        else:
            response = RedirectResponse(f"/edit_page_failed/{name}", status_code=303)
            return response
    else:
        return RedirectResponse(f"/login", status_code=303)


@app.get("/pages")
async def pages(request: Request, db: Session = Depends(get_db)):
    """
    GET route handler for the webpage linking all available wiki pages.
    :param request: The request passed in by the client.
    :param db: The db session to pull the page info from.
    :return: The webpage showing all of the pages.
    """
    query = "%"
    res = []
    if query:
        for page in crud.search_page(db, query):
            res.append(page.name)
    return templates.TemplateResponse("all_pages.html", {'request': request, 'res': res})


@app.get("/page/{page_name}")
async def page(page_name: str, request: Request, db: Session = Depends(get_db)):
    """
    GET route handler for a specific wiki page.
    :param page_name: The name of the page to access.
    :param request: The request from the client.
    :param db: The database where the page info is stored.
    :return: The desired wiki webpage, or a page not found page if page DNE.
    """
    page = crud.get_page(db, page_name)
    if page is None:
        return templates.TemplateResponse("page_not_found.html", {'request': request, 'name': page_name})
    else:
        return templates.TemplateResponse("page.html", {'request': request, 'name': page.name, 'content': page.content})


@app.get("/create_page")
async def create_page(request: Request, user: Optional[str] = Cookie(None)):
    """
    GET route handler for creating a page.
    :param request: The request from the client.
    :param user: The user creating the page.
    :return: The create page webpage, or a login page if the client is not logged in.
    """
    if user:
        return templates.TemplateResponse("create_page.html", {'request': request})
    else:
        return RedirectResponse(f"/login", status_code=303)


@app.post("/create_page")
async def create_page_post(name: str = Form(...)):
    """
    POST route handler for creating a page.
    :param name: The name of the page to be created.
    :return: Redirect to the edit page webpage for that page.
    """
    response = RedirectResponse(f"/edit_page/{name}", status_code=303)
    return response


@app.get("/search")
async def search(request: Request, query: Optional[str] = None, db: Session = Depends(get_db)):
    """
    GET route handler for the search webpage.
    :param request: The request from the client.
    :param query: The query parameters with the search query.
    :param db: The database with the webpages.
    :return: The search webpage.
    """
    res = []
    if query:
        for page in crud.search_page(db, query):
            res.append(page.name)
    return templates.TemplateResponse("search.html", {'request': request, 'res': res})


@app.get("/edit_admin")
async def edit_admin(request: Request, db: Session = Depends(get_db), user: Optional[str] = Cookie(None)):
    """
    GET route handler for the edit admin webpage.
    :param request: The request from the client.
    :param db: The database with the user information.
    :param user: The user that wants to change admin rights for other users.
    :return: The edit admin page if the user is an admin, or the message "Not admin"
    """
    if user is None:
        return RedirectResponse(f"/login", status_code=303)
    current_user = crud.get_user_by_name(db, user)
    if not current_user.admin:
        return "Not admin"
    return templates.TemplateResponse("edit_admin.html", {'request': request, 'res': crud.get_users(db)})


@app.post("/edit_admin")
async def edit_admin_post(request: Request, db: Session = Depends(get_db),
                          coord: str = Depends(get_coordinator), user: Optional[str] = Cookie(None)):
    """
    POST route handler for the edit admin webpage. Handles updating admin status for users.
    :param request: The request from the client.
    :param db: The database with the user information.
    :param coord: The ip of the coordinator for 2PC.
    :param user: The user that wants to change the admin rights of other users.
    :return: login page if no user, Not admin message if not an admin user, edit_admin page if successful,
             or edit_admin_failed page if something went wrong with the update.
    """
    if user is None:
        return RedirectResponse(f"/login", status_code=303)
    current_user = crud.get_user_by_name(db, user)
    if not current_user.admin:
        return "Not admin"
    form_data = await request.form()
    print(form_data)
    success = True
    for u in crud.get_users(db):
        if u.name in form_data:
            # crud.update_admin(db, u.name, True)
            data = RequestUserCommit(name=u.name, admin=True).dict()
            async with httpx.AsyncClient() as client:
                coord_url = 'http://' + coord + ':8000' + '/request_user_commit'
                coord_response = await client.post(coord_url, json=data)
            if coord_response.status_code != 200:
                success = False
                print('failed', u.name, 'admin')
            else:
                print(u.name, 'admin')
        else:
            # crud.update_admin(db, u.name, False)
            data = RequestUserCommit(name=u.name, admin=False).dict()
            async with httpx.AsyncClient() as client:
                coord_url = 'http://' + coord + ':8000' + '/request_user_commit'
                coord_response = await client.post(coord_url, json=data)
            if coord_response.status_code != 200:
                success = False
                print('failed', u.name, 'not admin')
            else:
                print(u.name, 'not admin')

        if success:
            return templates.TemplateResponse("edit_admin.html", {'request': request, 'res': crud.get_users(db)})
        else:
            return templates.TemplateResponse("edit_admin_failed.html", {'request': request})


@app.get("/create_page_failed")
async def create_page_failed(request: Request):
    """
    GET route handler for when a page creation fails.
    :param request: The request sent by the client.
    :return: The page indicating that page creation failed.
    """
    return templates.TemplateResponse("create_page_failed.html", {'request': request})


@app.get("/edit_page_failed/{page_name}")
async def edit_page_failed(page_name: str, request: Request):
    """
    GET route handler for when a page edit fails.
    :param page_name: The page that failed to be edited.
    :param request: The request from the client.
    :return: The edit failed webpage.
    """
    return templates.TemplateResponse("edit_page_failed.html", {'request': request, 'name': page_name})


@app.get("/create_user_failed")
async def create_user_failed(request: Request):
    """
    GET route handler for when a create user fails.
    :param request: The request from the client.
    :return: The create user failed webpage.
    """
    return templates.TemplateResponse("create_user_failed.html", {'request': request})


@app.get("/edit_admin_failed")
async def edit_admin_failed(request: Request):
    """
    GET route handler for when an edit admin fails.
    :param request: The request from the client.
    :return: The edit admin failed webpage.
    """
    return templates.TemplateResponse("edit_admin_failed", {'request': request})


@app.post("/can_page_commit")
async def can_page_commit(commit: PageCommit, db: Session = Depends(get_db), ip: str = Depends(get_ip)):
    """
    POST route handler for when the coordinator wants to commit a page change.
    :param commit: The page commit that the coordinator wants to perform.
    :param db: The database with the commit log.
    :param ip: The IP of this data server.
    :return: JSON CommitReply stating if this data server is willing to commit or not.
    """
    if crud.tid_in_log(db, commit.transaction_id):
        db_log = crud.get_log(db, commit.transaction_id)
        if db_log.status == 'promised':
            return CommitReply(sender=ip, commit=True, transaction_id=commit.transaction_id)
        else:
            # should this change status to aborted in log?
            return CommitReply(sender=ip, commit=False, transaction_id=commit.transaction_id)
    else:
        crud.add_to_log(db, commit.transaction_id, 'page', 'promised', commit.page, commit.content, False)
        return CommitReply(sender=ip, commit=True, transaction_id=commit.transaction_id)


@app.post("/can_user_commit")
async def can_user_commit(commit: UserCommit, db: Session = Depends(get_db), ip: str = Depends(get_ip)):
    """
    POST route handler for when the coordinator wants to commit a user change. Adds the commit to the commit log.
    1st Phase of 2PC.
    :param commit: The user commit that the coordinator wants to perform.
    :param db: The database with the commit log.
    :param ip: The IP of this data server.
    :return: JSON CommitReply stating if this data server is willing to commit or not.
    """
    if crud.tid_in_log(db, commit.transaction_id):
        db_log = crud.get_log(db, commit.transaction_id)
        if db_log.status == 'promised':
            return CommitReply(transaction_id=commit.transaction_id, sender=ip, commit=True)
        else:
            # should this change status to aborted in log?
            return CommitReply(transaction_id=commit.transaction_id, sender=ip, commit=False)
    else:
        crud.add_to_log(db, commit.transaction_id, 'user', 'promised', commit.name, '', commit.admin)
        return CommitReply(transaction_id=commit.transaction_id, sender=ip, commit=True)


@app.post("/do_commit")
async def do_commit(commit: DoCommit, db: Session = Depends(get_db), ip: str = Depends(get_ip)):
    """
    POST route handler for when the coordinator wants this data server to perform the commit that it promised
    it could do. If the coordinator has commit=False, then abort the commit.
    If commit=true, commits the pending commit from the log.
    2nd Phase of 2PC.
    :param commit: JSON message with the transaction id to commit.
    :param db: The database with the commit log and the tables where the data is to be committed.
    :param ip: The ip of this data server.
    :return: JSON HaveCommit message indicating whether or not this data server has commit or not.
    """
    if crud.tid_in_log(db, commit.transaction_id):
        db_log = crud.get_log(db, commit.transaction_id)
        if not commit.commit:  # coordinator decided to abort the commit
            crud.update_in_log(db, commit.transaction_id, db_log.type, 'aborted', db_log.name, db_log.content, db_log.admin)
            return HaveCommit(transaction_id=commit.transaction_id, sender=ip, commit=False)
        else:
            if db_log.status == 'promised' or db_log.status == 'committed':
                crud.update_in_log(db, commit.transaction_id, db_log.type, 'committed', db_log.name, db_log.content, db_log.admin)
                if db_log.type == 'user':
                    crud.create_or_update_user(db, commit.transaction_id)
                elif db_log.type == 'page':
                    crud.create_or_update_page(db, commit.transaction_id)
                return HaveCommit(transaction_id=commit.transaction_id, sender=ip, commit=True)
            else:
                crud.update_in_log(db, commit.transaction_id, db_log.type, 'aborted', db_log.name, db_log.content, db_log.admin)
                return HaveCommit(transaction_id=commit.transaction_id, sender=ip, commit=False)
    else:
        crud.add_to_log(db, commit.transaction_id, '', 'aborted', '', '', False)
        return HaveCommit(transaction_id=commit.transaction_id, sender=ip, commit=False)
