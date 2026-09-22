import pytest

from eight_puzzle import (
    Heuristic,
    SlidingPuzzle,
    breadth_first_search,
    manhattan_distance,
    misplaced_tiles,
)

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
    ("state", "expected_misplaced", "expected_manhattan"),
    [
        (GOAL_3X3, 0, 0),
        ((1, 2, 3, 4, 5, 6, 7, 0, 8), 1, 1),
        ((1, 2, 3, 4, 5, 6, 0, 7, 8), 2, 2),
        ((1, 2, 3, 4, 5, 6, 8, 0, 7), 2, 3),
    ],
)
def test_exact_canonical_heuristic_values(
    state: tuple[int, ...],
    expected_misplaced: int,
    expected_manhattan: int,
) -> None:
    puzzle = SlidingPuzzle(GOAL_3X3, GOAL_3X3)

    assert misplaced_tiles(puzzle, state) == expected_misplaced
    assert manhattan_distance(puzzle, state) == expected_manhattan


def test_blank_is_excluded_even_when_far_from_its_goal() -> None:
    puzzle = SlidingPuzzle(GOAL_3X3, GOAL_3X3)
    state = (0, 2, 3, 4, 5, 6, 7, 8, 1)

    assert misplaced_tiles(puzzle, state) == 1
    assert manhattan_distance(puzzle, state) == 4


def test_heuristics_use_the_configured_nonstandard_goal() -> None:
    nonstandard_goal = (1, 2, 3, 4, 5, 6, 0, 7, 8)
    state = GOAL_3X3
    puzzle = SlidingPuzzle(state, nonstandard_goal)

    assert misplaced_tiles(puzzle, nonstandard_goal) == 0
    assert manhattan_distance(puzzle, nonstandard_goal) == 0
    assert misplaced_tiles(puzzle, state) == 2
    assert manhattan_distance(puzzle, state) == 2


@pytest.mark.parametrize(
    ("state", "expected_misplaced", "expected_manhattan"),
    [
        (GOAL_4X4, 0, 0),
        (tuple(range(1, 15)) + (0, 15), 1, 1),
        (tuple(range(1, 14)) + (15, 0, 14), 2, 3),
    ],
)
def test_exact_4x4_heuristic_values(
    state: tuple[int, ...],
    expected_misplaced: int,
    expected_manhattan: int,
) -> None:
    puzzle = SlidingPuzzle(GOAL_4X4, GOAL_4X4)

    assert misplaced_tiles(puzzle, state) == expected_misplaced
    assert manhattan_distance(puzzle, state) == expected_manhattan


@pytest.mark.parametrize("heuristic", [misplaced_tiles, manhattan_distance])
def test_heuristics_reuse_puzzle_state_validation(heuristic: Heuristic) -> None:
    puzzle = SlidingPuzzle(GOAL_3X3, GOAL_3X3)

    with pytest.raises(ValueError, match="perfect square"):
        heuristic(puzzle, tuple(range(8)))


@pytest.mark.parametrize(
    "state",
    [
        GOAL_3X3,
        (1, 2, 3, 4, 5, 6, 7, 0, 8),
        (1, 2, 3, 4, 5, 6, 0, 7, 8),
        (1, 2, 3, 4, 5, 6, 8, 0, 7),
        (0, 2, 3, 4, 5, 6, 7, 8, 1),
    ],
)
def test_manhattan_is_at_least_as_informative_as_misplaced(
    state: tuple[int, ...],
) -> None:
    puzzle = SlidingPuzzle(GOAL_3X3, GOAL_3X3)

    assert manhattan_distance(puzzle, state) >= misplaced_tiles(puzzle, state)


@pytest.mark.parametrize("heuristic", [misplaced_tiles, manhattan_distance])
@pytest.mark.parametrize(
    "state",
    [
        GOAL_3X3,
        (1, 2, 3, 4, 5, 6, 7, 0, 8),
        (1, 2, 3, 4, 5, 6, 0, 7, 8),
        (1, 2, 3, 5, 0, 6, 4, 7, 8),
        (0, 2, 3, 4, 5, 6, 7, 8, 1),
    ],
)
def test_builtin_heuristics_are_consistent_on_representative_transitions(
    heuristic: Heuristic, state: tuple[int, ...]
) -> None:
    puzzle = SlidingPuzzle(state, GOAL_3X3)
    state_value = heuristic(puzzle, state)

    for _, successor in puzzle.neighbors(state):
        assert state_value <= 1 + heuristic(puzzle, successor)


@pytest.mark.parametrize("heuristic", [misplaced_tiles, manhattan_distance])
@pytest.mark.parametrize(
    "state",
    [
        GOAL_3X3,
        (1, 2, 3, 4, 5, 6, 7, 0, 8),
        (1, 2, 3, 4, 5, 6, 0, 7, 8),
        (1, 2, 3, 4, 0, 6, 7, 5, 8),
    ],
)
def test_builtin_heuristic_does_not_exceed_known_optimal_cost(
    heuristic: Heuristic, state: tuple[int, ...]
) -> None:
    puzzle = SlidingPuzzle(state, GOAL_3X3)
    optimal_result = breadth_first_search(puzzle)

    assert optimal_result.cost is not None
    assert heuristic(puzzle, state) <= optimal_result.cost
