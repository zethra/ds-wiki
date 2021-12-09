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

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


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


@app.get("/")
async def index(request: Request, db: Session = Depends(get_db), user: Optional[str] = Cookie(None)):
    admin = False
    if user:
        current_user = crud.get_user_by_name(db, user)
        if current_user.admin:
            admin = True
    return templates.TemplateResponse("index.html", {'request': request, 'admin': admin, 'user': user})


@app.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {'request': request})


@app.post("/login")
async def login_post(user: str = Form(...), db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_name(db, user)
    if existing_user:
        response = RedirectResponse("/", status_code=303)
        response.set_cookie(key='user', value=existing_user.name)
        return response
    else:
        return HTTPException(status_code=400, detail="User doesn't exist")


@app.get("/logout")
async def logout():
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(key='user', value='')
    return response


@app.get("/create")
async def create(request: Request):
    return templates.TemplateResponse("create.html", {'request': request})


@app.post("/create")
async def create_post(user: str = Form(...), db: Session = Depends(get_db), coord: str = Depends(get_coordinator)):
    existing_user = crud.get_user_by_name(db, user)
    if existing_user:
        return HTTPException(status_code=400, detail="User already registered")
    else:
        admin = crud.no_users(db)
        # new_user = crud.create_user(db, user, admin)
        data = RequestUserCommit(name=user, admin=admin).dict()
        async with httpx.AsyncClient() as client:
            coord_response = await client.post(coord + '/request_user_commit', json=data)
        if coord_response.status_code == 200:
            response = RedirectResponse("/login", status_code=303)
            return response
        else:
            response = RedirectResponse("/create_user_failed", status_code=303)
            return response


@app.get("/edit_page/{page_name}")
async def edit_page(page_name: str, request: Request, db: Session = Depends(get_db),
                    coord: str = Depends(get_coordinator), user: Optional[str] = Cookie(None)):
    if user:
        existing_user = crud.get_user_by_name(db, user)
        page = crud.get_page(db, page_name)
        if page is None:
            if existing_user.admin:
                # page = crud.create_page(db, schemas.Page(page_name, ""))
                data = RequestPageCommit(page=page_name, content='')
                async with httpx.AsyncClient() as client:
                    coord_response = await client.post(coord + '/request_page_commit', json=data)
                if coord_response.status_code == 200:
                    # 200 indicates that the db has been updated
                    response = templates.TemplateResponse("edit_page.html", {'request': request, 'name': page.name, 'content': page.content})
                    return response
                else:
                    response = RedirectResponse("create_page_failed.html", status_code=303)
                    return response
            else:
                return RedirectResponse(f"/login", status_code=303)
        return templates.TemplateResponse("edit_page.html", {'request': request, 'name': page.name, 'content': page.content})
    else:
        return RedirectResponse(f"/login", status_code=303)


@app.post("/edit_page")
async def edit_page_post(name: str = Form(...), content: str = Form(...), db: Session = Depends(get_db),
                         coord: str = Depends(get_coordinator), user: Optional[str] = Cookie(None)):
    if user:
        # crud.update_page_content(db, name, content)
        data = RequestPageCommit(page=name, content=content).dict()
        async with httpx.AsyncClient() as client:
            coord_response = await client.post(coord + '/request_page_commit', json=data)
        if coord_response.status_code == 200:
            # 200 indicates that the db has been updated
            response = RedirectResponse(f"/page/{name}", status_code=303)
            return response
        else:
            response = RedirectResponse(f"/edit_page_failed/{name}", status_code=303)
            return response
    else:
        return RedirectResponse(f"/login", status_code=303)


@app.get("/create_page_failed")
async def create_page_failed(request: Request):
    return templates.TemplateResponse("create_page_failed.html", {'request': request})


@app.get("/edit_page_failed/{page_name}")
async def edit_page_failed(page_name: str, request: Request):
    return templates.TemplateResponse("edit_page_failed.html", {'request': request, 'name': page_name})


@app.get("/create_user_failed")
async def create_user_failed(request: Request):
    return templates.TemplateResponse("create_user_failed.html", {'request': request})


@app.get("/edit_admin_failed")
async def edit_admin_failed(request: Request):
    return templates.TemplateResponse("edit_admin_failed", {'request': request})


@app.get("/pages")
async def pages(request: Request, db: Session = Depends(get_db)):
    query = "%"
    res = []
    if query:
        for page in crud.search_page(db, query):
            res.append(page.name)
    return templates.TemplateResponse("all_pages.html", {'request': request, 'res': res})


@app.get("/page/{page_name}")
async def page(page_name: str, request: Request, db: Session = Depends(get_db)):
    page = crud.get_page(db, page_name)
    if page is None:
        page = crud.create_page(db, schemas.Page(page_name, ""))
    return templates.TemplateResponse("page.html", {'request': request, 'name': page.name, 'content': page.content})


@app.get("/create_page")
async def create_page(request: Request, user: Optional[str] = Cookie(None)):
    if user:
        return templates.TemplateResponse("create_page.html", {'request': request})
    else:
        return RedirectResponse(f"/login", status_code=303)


@app.post("/create_page")
async def create_page_post(name: str = Form(...)):
    response = RedirectResponse(f"/edit_page/{name}", status_code=303)
    return response


@app.get("/search")
async def search(request: Request, query: Optional[str] = None, db: Session = Depends(get_db)):
    res = []
    if query:
        for page in crud.search_page(db, query):
            res.append(page.name)
    return templates.TemplateResponse("search.html", {'request': request, 'res': res})


@app.get("/edit_admin")
async def edit_admin(request: Request, db: Session = Depends(get_db), user: Optional[str] = Cookie(None)):
    if user is None:
        return RedirectResponse(f"/login", status_code=303)
    current_user = crud.get_user_by_name(db, user)
    if not current_user.admin:
        return "Not admin"
    return templates.TemplateResponse("edit_admin.html", {'request': request, 'res': crud.get_users(db)})


@app.post("/edit_admin")
async def edit_admin_post(request: Request, db: Session = Depends(get_db),
                          coord: str = Depends(get_coordinator), user: Optional[str] = Cookie(None)):
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
                coord_response = await client.post(coord + '/request_user_commit', json=data)
            if coord_response.status_code != 200:
                success = False
                print('failed', u.name, 'admin')
            else:
                print(u.name, 'admin')
        else:
            # crud.update_admin(db, u.name, False)
            data = RequestUserCommit(name=u.name, admin=False).dict()
            async with httpx.AsyncClient() as client:
                coord_response = await client.post(coord + '/request_user_commit', json=data)
            if coord_response.status_code != 200:
                success = False
                print('failed', u.name, 'not admin')
            else:
                print(u.name, 'not admin')

        if success:
            return templates.TemplateResponse("edit_admin.html", {'request': request, 'res': crud.get_users(db)})
        else:
            return templates.TemplateResponse("edit_admin_failed.html", {'request': request})


@app.post("/can_page_commit")
async def can_page_commit(commit: PageCommit, db: Session = Depends(get_db), ip: str = Depends(get_ip)):
    if crud.tid_in_log(db, commit.transaction_id):
        db_log = crud.get_log(db, commit.transaction_id)
        if db_log.status == 'promised':
            return CommitReply(sender=ip, commit=True, transaction_id=commit.transaction_id)
        return CommitReply(sender=ip, commit=False, transaction_id=commit.transaction_id)
    else:
        crud.add_to_log(db, commit.transaction_id, 'page', 'promised', commit.page, commit.content, False)
        return CommitReply(sender=ip, commit=True, transaction_id=commit.transaction_id)


@app.post("/can_user_commit")
async def can_user_commit(commit: UserCommit, db: Session = Depends(get_db), ip: str = Depends(get_ip)):
    if crud.tid_in_log(db, commit.transaction_id):
        db_log = crud.get_log(db, commit.transaction_id)
        if db_log.status == 'promised':
            return CommitReply(transaction_id=commit.transaction_id, sender=ip, commit=True)
        return CommitReply(transaction_id=commit.transaction_id, sender=ip, commit=False)
    else:
        crud.add_to_log(db, commit.transaction_id, 'user', 'promised', commit.name, '', commit.admin)
        return CommitReply(transaction_id=commit.transaction_id, sender=ip, commit=True)


@app.post("/do_commit")
async def do_commit(commit: DoCommit, db: Session = Depends(get_db), ip: str = Depends(get_ip)):
    if crud.tid_in_log(db, commit.transaction_id):
        db_log = crud.get_log(db, commit.transaction_id)
        if db_log.status == 'promised':
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
    pass
