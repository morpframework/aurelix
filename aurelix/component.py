from fastapi.responses import RedirectResponse, JSONResponse
from fastapi import Request
from .exc import SearchException

import sqlite3
import transitions
def register_exception_views(app):
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
    
    