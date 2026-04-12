import typer
from sqlmodel import SQLModel
from app.database import engine, get_cli_session
from app.repositories.user import UserRepository
from app.repositories.puzzle import DailyPuzzleRepository
from app.repositories.game_session import GameSessionRepository
from app.repositories.guess import GuessRepository
from app.services.auth_service import AuthService
from app.services.puzzle_service import PuzzleService
from app.services.game_service import GameService

cli = typer.Typer()


@cli.command("initialize") #Note use del database.db and reinitialize to avoid daily puzzle.
def initialize(): #Game resets at utc time midnight.
    SQLModel.metadata.create_all(engine)

    with get_cli_session() as db:
        user_repo = UserRepository(db)
        auth_service = AuthService(user_repo)
        puzzle_repo = DailyPuzzleRepository(db)
        puzzle_service = PuzzleService(puzzle_repo)

        existing = user_repo.get_by_username("bob")
        if not existing:
            auth_service.register_user(
                username="bob",
                email="bob@example.com",
                password="bobpass"
            )
            typer.echo("Created bob / bobpass")
        else:
            typer.echo("bob already exists")

        puzzle = puzzle_service.get_or_create_today_puzzle()
        typer.echo(f"Puzzle ready for {puzzle.puzzle_date}: {puzzle.secret_number}")

    typer.echo("Database initialized.")


@cli.command("create-puzzle")
def create_puzzle(secret: str):
    with get_cli_session() as db:
        puzzle_repo = DailyPuzzleRepository(db)
        puzzle_service = PuzzleService(puzzle_repo)
        puzzle = puzzle_service.create_today_puzzle(secret)
        typer.echo(f"Puzzle ready for {puzzle.puzzle_date}: {puzzle.secret_number}")


@cli.command("start-game")
def start_game(username: str):
    with get_cli_session() as db:
        user_repo = UserRepository(db)
        puzzle_repo = DailyPuzzleRepository(db)
        session_repo = GameSessionRepository(db)
        guess_repo = GuessRepository(db)

        game_service = GameService(
            user_repo=user_repo,
            puzzle_repo=puzzle_repo,
            session_repo=session_repo,
            guess_repo=guess_repo
        )

        session = game_service.start_game_for_user(username)
        typer.echo(f"Started session {session.id} for {username}")


@cli.command("guess")
def guess(username: str, guess_value: str):
    with get_cli_session() as db:
        user_repo = UserRepository(db)
        puzzle_repo = DailyPuzzleRepository(db)
        session_repo = GameSessionRepository(db)
        guess_repo = GuessRepository(db)

        game_service = GameService(
            user_repo, puzzle_repo, session_repo, guess_repo
        )

        try:
            guess_obj, session, answer = game_service.submit_guess(username, guess_value)

            typer.echo(f"\n Guess: {guess_value}")
            typer.echo(f" Bulls: {guess_obj.bulls} |  Cows: {guess_obj.cows}")
            typer.echo(
                f"📊 Status: {session.status} | Attempts: {session.attempts_used}/{session.max_attempts}"
            )

            if session.status == "won":
                typer.echo("You won the game!!!")

            elif session.status == "lost":
                typer.echo(f"You lost! The answer was {answer}.")

        except ValueError as e:
            typer.echo(f" Error: {e}")


@cli.command("history")
def history(username: str):
    with get_cli_session() as db:
        user_repo = UserRepository(db)
        puzzle_repo = DailyPuzzleRepository(db)
        session_repo = GameSessionRepository(db)
        guess_repo = GuessRepository(db)

        game_service = GameService(
            user_repo=user_repo,
            puzzle_repo=puzzle_repo,
            session_repo=session_repo,
            guess_repo=guess_repo
        )

        rows = game_service.get_user_history(username)
        for row in rows:
            typer.echo(row)


if __name__ == "__main__":
    cli()