import uvicorn
from fastapi import FastAPI, Request, status
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from app.routers import templates, static_files, router, api_router
from app.config import get_settings
from contextlib import asynccontextmanager
from contextlib import asynccontextmanager
from sqlmodel import SQLModel
from app.database import engine, get_cli_session
from app.repositories.user import UserRepository
from app.services.auth_service import AuthService

@asynccontextmanager
async def lifespan(app):
    SQLModel.metadata.create_all(engine)

    with get_cli_session() as db:
        user_repo = UserRepository(db)
        auth_service = AuthService(user_repo)

        existing = user_repo.get_by_username("bob")
        if not existing:
            auth_service.register_user(
                username="bob",
                email="bob@example.com",
                password="bobpass"
            )

    yield

app = FastAPI(middleware=[
    Middleware(SessionMiddleware, secret_key=get_settings().secret_key)
],
    lifespan=lifespan
)   

app.include_router(router)
app.include_router(api_router)
app.mount("/static", static_files, name="static")

@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def unauthorized_redirect_handler(request: Request, exc: Exception):
    return templates.TemplateResponse(
        request=request, 
        name="401.html",
    )

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=get_settings().app_host, port=get_settings().app_port, reload=get_settings().env.lower()!="production")