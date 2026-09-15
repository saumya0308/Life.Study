from dataclasses import dataclass
from typing import Iterable

DIFFICULTY_POINTS = {
    "easy": 100,
    "medium": 150,
    "hard": 200,
}

TREASURE_STREAK = 3
TREASURE_BONUS = 300
MAX_TORCHES = 5


@dataclass(frozen=True)
class AnswerOutcome:
    correct: bool
    points_awarded: int
    torch_lost: bool
    treasure_unlocked: bool
    new_streak: int


def resolve_answer(
    *,
    is_correct: bool,
    difficulty: str,
    current_streak: int,
    torches_remaining: int,
) -> AnswerOutcome:
    if is_correct:
        new_streak = current_streak + 1
        treasure_unlocked = new_streak >= TREASURE_STREAK
        points = DIFFICULTY_POINTS.get(difficulty, 100)
        if treasure_unlocked:
            points += TREASURE_BONUS
            new_streak = 0
        return AnswerOutcome(
            correct=True,
            points_awarded=points,
            torch_lost=False,
            treasure_unlocked=treasure_unlocked,
            new_streak=new_streak,
        )

    return AnswerOutcome(
        correct=False,
        points_awarded=0,
        torch_lost=torches_remaining > 0,
        treasure_unlocked=False,
        new_streak=0,
    )


def mastery_from_attempts(attempts: Iterable) -> dict[str, int]:
    stats: dict[str, list[int]] = {}
    for attempt in attempts:
        if attempt.topic not in stats:
            stats[attempt.topic] = [0, 0]
        stats[attempt.topic][1] += 1
        if attempt.correct:
            stats[attempt.topic][0] += 1

    return {
        topic: round((correct / total) * 100)
        for topic, (correct, total) in stats.items()
        if total
    }


def accuracy(correct: int, incorrect: int) -> int:
    total = correct + incorrect
    return round(correct / total * 100) if total else 0
