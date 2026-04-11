from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Request, status, Form
from app.dependencies import SessionDep
from . import router, templates
from app.services.auth_service import AuthService
from app.repositories.user import UserRepository
from app.utilities.flash import flash
from app.config import get_settings


def _cookie_settings():
    is_production = get_settings().env.lower() == "production"
    return {"secure": is_production, "samesite": "none" if is_production else "lax"}

# View route responsible for UI
@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url=request.url_for("login_view"), status_code=status.HTTP_303_SEE_OTHER)
    cookie_settings = _cookie_settings()
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite=cookie_settings["samesite"],
        secure=cookie_settings["secure"],
    )
    return response