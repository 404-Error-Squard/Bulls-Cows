from datetime import date
from app.models.puzzle import DailyPuzzle
from app.repositories.puzzle import DailyPuzzleRepository


class PuzzleService:
    def __init__(self, puzzle_repo: DailyPuzzleRepository):
        self.puzzle_repo = puzzle_repo

    def create_today_puzzle(self, secret_number: str) -> DailyPuzzle:
        existing = self.puzzle_repo.get_by_date(date.today())
        if existing:
            return existing

        puzzle = DailyPuzzle(
            puzzle_date=date.today(),
            secret_number=secret_number
        )
        return self.puzzle_repo.create(puzzle)

    def get_today_puzzle(self):
        return self.puzzle_repo.get_by_date(date.today())