import pytest

from eight_puzzle import SlidingPuzzle

GOAL_3X3 = (
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    0,
)
GOAL_4X4 = tuple(range(1, 16)) + (0,)


@pytest.mark.parametrize(
    "state",
    [
        GOAL_3X3,
        (1, 2, 3, 4, 5, 6, 7, 0, 8),
        (1, 2, 3, 4, 0, 6, 7, 5, 8),
        (1, 2, 3, 0, 7, 6, 5, 4, 8),
    ],
)
def test_known_solvable_3x3_states(state: tuple[int, ...]) -> None:
    puzzle = SlidingPuzzle(state, GOAL_3X3)

    assert puzzle.is_solvable()
    assert puzzle.is_solvable(state)


def test_numbered_tile_swap_is_unsolvable_for_canonical_3x3_goal() -> None:
    unsolvable = (1, 2, 3, 4, 5, 6, 8, 7, 0)
    puzzle = SlidingPuzzle(unsolvable, GOAL_3X3)

    assert not puzzle.is_solvable()


def test_solvability_is_relative_to_nonstandard_3x3_goal() -> None:
    nonstandard_goal = (1, 2, 3, 4, 5, 6, 8, 7, 0)
    one_move_away = (1, 2, 3, 4, 5, 6, 8, 0, 7)
    puzzle = SlidingPuzzle(one_move_away, nonstandard_goal)

    assert puzzle.is_solvable()
    assert puzzle.is_solvable(nonstandard_goal)
    assert not puzzle.is_solvable(GOAL_3X3)


@pytest.mark.parametrize(
    "state",
    [
        GOAL_4X4,
        tuple(range(1, 15)) + (0, 15),
        (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 13, 14, 15, 12),
    ],
)
def test_known_solvable_4x4_states(state: tuple[int, ...]) -> None:
    puzzle = SlidingPuzzle(state, GOAL_4X4)

    assert puzzle.is_solvable()


def test_numbered_tile_swap_is_unsolvable_for_canonical_4x4_goal() -> None:
    unsolvable = tuple(range(1, 14)) + (15, 14, 0)
    puzzle = SlidingPuzzle(unsolvable, GOAL_4X4)

    assert not puzzle.is_solvable()


def test_solvability_is_relative_to_nonstandard_4x4_goal() -> None:
    nonstandard_goal = tuple(range(1, 14)) + (15, 14, 0)
    one_move_away = tuple(range(1, 14)) + (15, 0, 14)
    puzzle = SlidingPuzzle(one_move_away, nonstandard_goal)

    assert puzzle.is_solvable()
    assert puzzle.is_solvable(nonstandard_goal)
    assert not puzzle.is_solvable(GOAL_4X4)
