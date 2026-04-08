from fastapi import Depends, HTTPException
from pydantic import BaseModel

from . import api_router
from app.database import get_session
from app.repositories.user import UserRepository
from app.repositories.puzzle import DailyPuzzleRepository
from app.repositories.game_session import GameSessionRepository
from app.repositories.guess import GuessRepository
from app.services.game_service import GameService


class StartGameRequest(BaseModel):
    username: str


class GuessRequest(BaseModel):
    username: str
    guess_value: str


@api_router.post("/game/start")
def start_game(payload: StartGameRequest, db=Depends(get_session)):
    try:
        game_service = GameService(
            user_repo=UserRepository(db),
            puzzle_repo=DailyPuzzleRepository(db),
            session_repo=GameSessionRepository(db),
            guess_repo=GuessRepository(db),
        )

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
def submit_guess(payload: GuessRequest, db=Depends(get_session)):
    try:
        game_service = GameService(
            user_repo=UserRepository(db),
            puzzle_repo=DailyPuzzleRepository(db),
            session_repo=GameSessionRepository(db),
            guess_repo=GuessRepository(db),
        )

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
def get_history(username: str, db=Depends(get_session)):
    try:
        game_service = GameService(
            user_repo=UserRepository(db),
            puzzle_repo=DailyPuzzleRepository(db),
            session_repo=GameSessionRepository(db),
            guess_repo=GuessRepository(db),
        )

        history = game_service.get_user_history(username)

        return {
            "username": username,
            "history": history,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
