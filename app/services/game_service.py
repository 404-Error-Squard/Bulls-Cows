from datetime import datetime
from app.models.game_session import GameSession
from app.models.guess import Guess


class GameService:
    def __init__(self, user_repo, puzzle_repo, session_repo, guess_repo):
        self.user_repo = user_repo
        self.puzzle_repo = puzzle_repo
        self.session_repo = session_repo
        self.guess_repo = guess_repo

    def validate_guess(self, guess_value: str):
        if len(guess_value) != 4:
            raise ValueError("Guess must be exactly 4 digits.")
        if not guess_value.isdigit():
            raise ValueError("Guess must contain only digits.")
        if len(set(guess_value)) != 4:
            raise ValueError("Guess must not contain repeated digits.")

    def score_guess(self, secret: str, guess: str):
        bulls = sum(1 for i in range(4) if secret[i] == guess[i])
        cows = sum(1 for char in guess if char in secret) - bulls
        return bulls, cows

    def start_game_for_user(self, username: str):
        user = self.user_repo.get_by_username(username)
        if not user:
            raise ValueError("User not found.")

        puzzle = self.puzzle_repo.get_by_date(datetime.utcnow().date())
        if not puzzle:
            raise ValueError("No puzzle exists for today.")

        existing_session = self.session_repo.get_user_session_for_puzzle(user.id, puzzle.id)
        if existing_session:
            return existing_session

        session = GameSession(
            user_id=user.id,
            puzzle_id=puzzle.id
        )
        return self.session_repo.create(session)

    def submit_guess(self, username: str, guess_value: str):
        self.validate_guess(guess_value)

        user = self.user_repo.get_by_username(username)
        if not user:
            raise ValueError("User not found.")

        puzzle = self.puzzle_repo.get_by_date(datetime.utcnow().date())
        if not puzzle:
            raise ValueError("No puzzle exists for today.")

        session = self.session_repo.get_user_session_for_puzzle(user.id, puzzle.id)
        if not session:
            raise ValueError("No active session for this user.")

        if session.status != "active":
            raise ValueError("This session is already completed.")

        bulls, cows = self.score_guess(puzzle.secret_number, guess_value)

        guess = Guess(
            session_id=session.id,
            guess_value=guess_value,
            bulls=bulls,
            cows=cows
        )
        self.guess_repo.create(guess)

        session.attempts_used += 1

        if bulls == 4:
            session.status = "won"
            session.completed_at = datetime.utcnow()
        elif session.attempts_used >= session.max_attempts:
            session.status = "lost"
            session.completed_at = datetime.utcnow()

        self.session_repo.update(session)

        return {
            "guess": guess_value,
            "bulls": bulls,
            "cows": cows,
            "status": session.status,
            "attempts_used": session.attempts_used
        }

    def get_user_history(self, username: str):
        user = self.user_repo.get_by_username(username)
        if not user:
            raise ValueError("User not found.")

        sessions = self.session_repo.get_sessions_by_user(user.id)
        history = []

        for session in sessions:
            guesses = self.guess_repo.get_by_session(session.id)
            history.append({
                "session_id": session.id,
                "puzzle_id": session.puzzle_id,
                "status": session.status,
                "attempts_used": session.attempts_used,
                "guesses": [
                    {
                        "guess_value": g.guess_value,
                        "bulls": g.bulls,
                        "cows": g.cows
                    }
                    for g in guesses
                ]
            })

        return history