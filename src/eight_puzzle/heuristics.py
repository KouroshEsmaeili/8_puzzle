"""Goal-aware admissible heuristics for sliding puzzles."""

from collections.abc import Callable

from eight_puzzle.puzzle import PuzzleState, SlidingPuzzle

Heuristic = Callable[[SlidingPuzzle, PuzzleState], int]

def _misplaced_tiles(goal_state: PuzzleState, state: PuzzleState) -> int:
    return sum(
        tile != 0 and tile != goal_state[index] for index, tile in enumerate(state)
    )


def misplaced_tiles(puzzle: SlidingPuzzle, state: PuzzleState) -> int:
    """Count numbered tiles that are not in their configured goal positions."""
    normalized = puzzle.validate_state(state)
    return _misplaced_tiles(puzzle.goal_state, normalized)


def _goal_positions(puzzle: SlidingPuzzle) -> dict[int, tuple[int, int]]:
    return {
        tile: divmod(index, puzzle.size)
        for index, tile in enumerate(puzzle.goal_state)
        if tile != 0
    }


def _manhattan_distance(
    state: PuzzleState,
    size: int,
    goal_positions: dict[int, tuple[int, int]],
) -> int:
    distance = 0
    for index, tile in enumerate(state):
        if tile == 0:
            continue
        current_row, current_column = divmod(index, size)
        goal_row, goal_column = goal_positions[tile]
        distance += abs(current_row - goal_row) + abs(current_column - goal_column)
    return distance


def manhattan_distance(puzzle: SlidingPuzzle, state: PuzzleState) -> int:
    """Sum each numbered tile's grid distance from its configured goal."""
    normalized = puzzle.validate_state(state)
    return _manhattan_distance(normalized, puzzle.size, _goal_positions(puzzle))


def _build_heuristic_evaluator(
    puzzle: SlidingPuzzle, heuristic: Heuristic
) -> Callable[[PuzzleState], int]:
    """Prepare an evaluator for valid states generated during one search."""
    if heuristic is misplaced_tiles:
        goal_state = puzzle.goal_state
        return lambda state: _misplaced_tiles(goal_state, state)

    if heuristic is manhattan_distance:
        size = puzzle.size
        goal_positions = _goal_positions(puzzle)
        return lambda state: _manhattan_distance(state, size, goal_positions)

    return lambda state: heuristic(puzzle, state)
