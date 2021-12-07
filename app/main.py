from typing import Optional

from fastapi import FastAPI, Form
from fastapi.exceptions import HTTPException
from fastapi.param_functions import Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm.session import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

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
async def index(request: Request):
    return templates.TemplateResponse("index.html", {'request': request})

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

@app.get("/create")
async def create(request: Request):
    return templates.TemplateResponse("create.html", {'request': request})

@app.post("/create", response_model=schemas.User)
async def create_post(user: str = Form(...), db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_name(db, user)
    if existing_user:
        return HTTPException(status_code=400, detail="User already registered")
    else:
        new_user = crud.create_user(db, user)
        response = RedirectResponse("/", status_code=303)
        response.set_cookie(key='user', value=new_user.name)
        return response
