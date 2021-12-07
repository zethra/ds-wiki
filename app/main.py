from typing import Optional

from fastapi import FastAPI, Form
from fastapi.exceptions import HTTPException
from fastapi.param_functions import Cookie, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm.session import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app import crud, models, schemas

from .database import SessionLocal, engine

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

@app.get("/")
async def index(request: Request, db: Session = Depends(get_db), user: Optional[str] = Cookie(None)):
    admin = False
    if user:
        current_user = crud.get_user_by_name(db, user)
        if current_user.admin:
            admin = True
    return templates.TemplateResponse("index.html", {'request': request, 'admin': admin})

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
async def create_post(user: str = Form(...), db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_name(db, user)
    if existing_user:
        return HTTPException(status_code=400, detail="User already registered")
    else:
        admin = crud.no_users(db)
        new_user = crud.create_user(db, user, admin)
        response = RedirectResponse("/", status_code=303)
        response.set_cookie(key='user', value=new_user.name)
        return response

@app.get("/edit_page/{page_name}")
async def edit_page(page_name: str, request: Request, db: Session = Depends(get_db), user: Optional[str] = Cookie(None)):
    if user:
        page = crud.get_page(db, page_name)
        if page is None:
            page = crud.create_page(db, schemas.Page(page_name, ""))
        return templates.TemplateResponse("edit_page.html", {'request': request, 'name': page.name, 'content': page.content})
    else:
        return RedirectResponse(f"/login", status_code=303)

@app.post("/edit_page")
async def edit_page_post(name: str = Form(...), content: str = Form(...), db: Session = Depends(get_db), user: Optional[str] = Cookie(None)):
    if user:
        crud.update_page_content(db, name, content)
        response = RedirectResponse(f"/page/{name}", status_code=303)
        return response
    else:
        return RedirectResponse(f"/login", status_code=303)

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
async def edit_admin_post(request: Request, db: Session = Depends(get_db), user: Optional[str] = Cookie(None)):
    if user is None:
        return RedirectResponse(f"/login", status_code=303)
    current_user = crud.get_user_by_name(db, user)
    if not current_user.admin:
        return "Not admin"
    form_data = await request.form()
    print(form_data)
    for u in crud.get_users(db):
        if u.name in form_data:
            crud.update_admin(db, u.name, True)
            print(u.name, 'admin')
        else:
            print(u.name, 'not admin')
            crud.update_admin(db, u.name, False)
    return templates.TemplateResponse("edit_admin.html", {'request': request, 'res': crud.get_users(db)})
