from fastapi import Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from . import router, api_router, templates
from app.database import get_session
from app.dependencies import SessionDep
from app.dependencies.auth import AuthDep
from app.repositories.user import UserRepository
from app.repositories.puzzle import DailyPuzzleRepository
from app.repositories.game_session import GameSessionRepository
from app.repositories.guess import GuessRepository
from app.services.game_service import GameService
from app.utilities.flash import flash


def build_game_service(db):
    return GameService(
        user_repo=UserRepository(db),
        puzzle_repo=DailyPuzzleRepository(db),
        session_repo=GameSessionRepository(db),
        guess_repo=GuessRepository(db),
    )


# -------------------------
# JINJA ROUTES
# -------------------------

@router.get("/game", response_class=HTMLResponse)
async def game_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    game_service = build_game_service(db)

    try:
        history = game_service.get_user_history(user.username)
    except ValueError:
        history = []

    active_session = history[-1] if history else None

    return templates.TemplateResponse(
        request=request,
        name="game.html",
        context={
            "user": user,
            "active_session": active_session,
            "history": history,
        },
    )


@router.post("/game/start")
async def start_game_action(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    game_service = build_game_service(db)

    try:
        game_service.start_game_for_user(user.username)
        flash(request, "Game started successfully.", "success")
    except ValueError as e:
        flash(request, str(e), "danger")

    return RedirectResponse(url="/game", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/game/guess")
async def submit_guess_action(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    guess_value: str = Form(...),
):
    game_service = build_game_service(db)

    try:
        guess_obj, session, answer = game_service.submit_guess(user.username, guess_value)

        if session.status == "won":
            flash(
                request,
                f"Guess {guess_obj.guess_value}: {guess_obj.bulls} Bulls, {guess_obj.cows} Cows. You won!",
                "success",
            )
        elif session.status == "lost":
            flash(
                request,
                f"Guess {guess_obj.guess_value}: {guess_obj.bulls} Bulls, {guess_obj.cows} Cows. You lost. The answer was {answer}.",
                "danger",
            )
        else:
            flash(
                request,
                f"Guess {guess_obj.guess_value}: {guess_obj.bulls} Bulls, {guess_obj.cows} Cows.",
                "info",
            )

    except ValueError as e:
        flash(request, str(e), "danger")

    return RedirectResponse(url="/game", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/game/history", response_class=HTMLResponse)
async def history_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    game_service = build_game_service(db)

    try:
        history = game_service.get_user_history(user.username)
    except ValueError:
        history = []

    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={
            "user": user,
            "history": history,
        },
    )


class StartGameRequest(BaseModel):
    username: str


class GuessRequest(BaseModel):
    username: str
    guess_value: str


@api_router.post("/game/start")
async def start_game_api(payload: StartGameRequest, db=Depends(get_session)):
    try:
        game_service = build_game_service(db)
        session = game_service.start_game_for_user(payload.username)

        return {
            "message": "Game started successfully.",
            "session_id": session.id,
            "status": session.status,
            "attempts_used": session.attempts_used,
            "max_attempts": session.max_attempts,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.post("/game/guess")
async def submit_guess_api(payload: GuessRequest, db=Depends(get_session)):
    try:
        game_service = build_game_service(db)
        guess_obj, session = game_service.submit_guess(
            payload.username,
            payload.guess_value,
        )

        return {
            "message": "Guess submitted successfully.",
            "guess": guess_obj.guess_value,
            "bulls": guess_obj.bulls,
            "cows": guess_obj.cows,
            "status": session.status,
            "attempts_used": session.attempts_used,
            "max_attempts": session.max_attempts,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/game/history/{username}")
async def history_api(username: str, db=Depends(get_session)):
    try:
        game_service = build_game_service(db)
        history = game_service.get_user_history(username)
        return {
            "username": username,
            "history": history,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
