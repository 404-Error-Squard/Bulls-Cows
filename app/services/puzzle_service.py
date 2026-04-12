from datetime import datetime, timezone
import random
from app.models.puzzle import DailyPuzzle
from app.repositories.puzzle import DailyPuzzleRepository

class PuzzleService:
    def __init__(self, puzzle_repo):
        self.puzzle_repo = puzzle_repo

    def generate_secret_number(self) -> str:
        digits = random.sample("0123456789", 4)
        return "".join(digits)

    def get_or_create_today_puzzle(self):
        today = datetime.now(timezone.utc).date()
        existing = self.puzzle_repo.get_by_date(today)
        if existing:
            return existing

        puzzle = DailyPuzzle(
            puzzle_date=today,
            secret_number=self.generate_secret_number()
        )
        return self.puzzle_repo.create(puzzle)

    def create_today_puzzle(self, secret_number: str):
        today = datetime.now(timezone.utc).date()
        existing = self.puzzle_repo.get_by_date(today)
        if existing:
            return existing

        puzzle = DailyPuzzle(
            puzzle_date=today,
            secret_number=secret_number
        )
        return self.puzzle_repo.create(puzzle)