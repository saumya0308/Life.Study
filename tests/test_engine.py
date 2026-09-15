from app.game.engine import accuracy, mastery_from_attempts, resolve_answer


def test_correct_answer_awards_points_and_increases_streak():
    result = resolve_answer(
        is_correct=True,
        difficulty="medium",
        current_streak=1,
        torches_remaining=5,
    )
    assert result.correct is True
    assert result.points_awarded == 150
    assert result.new_streak == 2
    assert result.treasure_unlocked is False


def test_third_correct_answer_unlocks_treasure_and_resets_streak():
    result = resolve_answer(
        is_correct=True,
        difficulty="hard",
        current_streak=2,
        torches_remaining=5,
    )
    assert result.treasure_unlocked is True
    assert result.new_streak == 0
    assert result.points_awarded == 500


def test_wrong_answer_resets_streak_and_loses_torch():
    result = resolve_answer(
        is_correct=False,
        difficulty="easy",
        current_streak=2,
        torches_remaining=5,
    )
    assert result.correct is False
    assert result.new_streak == 0
    assert result.torch_lost is True
    assert result.points_awarded == 0


def test_accuracy():
    assert accuracy(8, 2) == 80
    assert accuracy(0, 0) == 0
