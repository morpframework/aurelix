from fastapi import FastAPI, Request, HTTPException
import pydantic
import typing
from fastapi.responses import RedirectResponse, JSONResponse
import databases
import sqlalchemy as sa
from .settings import settings
from .crud.routes import register_collection
from .crud.sqla import SQLACollection
from .crud.base import SearchException
from .crud.lowcode import load_app_models
from .db import database as db
from .db import engine
from .db import metadata
import os
import sqlite3
import transitions

app = FastAPI(title='Aether Data Management Engine', docs_url='/')
load_app_models(app, os.path.join(os.path.dirname(__file__), 'model'))

metadata.create_all(engine)

@app.exception_handler(SearchException)
async def search_exception_handler(request: Request, exc: SearchException):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.message},
    )

@app.exception_handler(sqlite3.IntegrityError)
async def integrity_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )

@app.exception_handler(transitions.core.MachineError)
async def sm_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.value},
    )

