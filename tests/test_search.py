from collections.abc import Callable

import pytest

from eight_puzzle import (
    Action,
    Heuristic,
    PuzzleState,
    SearchNode,
    SearchResult,
    SearchStatus,
    SlidingPuzzle,
    a_star_search,
    breadth_first_search,
    depth_first_search,
    depth_limited_search,
    iterative_deepening_search,
    manhattan_distance,
    misplaced_tiles,
    uniform_cost_search,
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
ONE_MOVE_START = (
    1,
    2,
    3,
    4,
    0,
    5,
    6,
    7,
    8,
)
ONE_MOVE_GOAL = (
    1,
    0,
    3,
    4,
    2,
    5,
    6,
    7,
    8,
)
TWO_MOVE_START = (
    1,
    2,
    3,
    4,
    5,
    6,
    0,
    7,
    8,
)
DFS_TWO_MOVE_GOAL = (
    0,
    1,
    3,
    4,
    2,
    5,
    6,
    7,
    8,
)
UNSOLVABLE_3X3 = (
    1,
    2,
    3,
    4,
    5,
    6,
    8,
    7,
    0,
)

SearchCall = Callable[[SlidingPuzzle], SearchResult]


def dls_with_safe_limit(puzzle: SlidingPuzzle) -> SearchResult:
    return depth_limited_search(puzzle, 8)


ALL_SEARCHES: tuple[tuple[str, SearchCall], ...] = (
    ("astar", a_star_search),
    ("bfs", breadth_first_search),
    ("dfs", depth_first_search),
    ("dls", dls_with_safe_limit),
    ("ids", iterative_deepening_search),
    ("ucs", uniform_cost_search),
)


def assert_valid_solution(puzzle: SlidingPuzzle, result: SearchResult) -> None:
    assert result.status is SearchStatus.SOLVED
    assert result.solved
    assert result.path[0] == puzzle.start_state
    assert result.path[-1] == puzzle.goal_state
    assert len(result.actions) == len(result.path) - 1
    assert result.solution_depth == len(result.actions)
    assert result.cost == len(result.actions)

    for state, action, next_state in zip(
        result.path[:-1], result.actions, result.path[1:], strict=True
    ):
        assert puzzle.apply_action(state, action) == next_state


@pytest.mark.parametrize(("algorithm", "search"), ALL_SEARCHES)
def test_immediate_goal_has_exact_standard_result(
    algorithm: str, search: SearchCall
) -> None:
    puzzle = SlidingPuzzle(GOAL_3X3, GOAL_3X3)

    result = search(puzzle)

    assert result.algorithm == algorithm
    assert result.status is SearchStatus.SOLVED
    assert result.path == (GOAL_3X3,)
    assert result.actions == ()
    assert result.cost == 0
    assert result.solution_depth == 0
    assert result.nodes_generated == 1
    assert result.nodes_expanded == 0
    assert result.max_frontier_size == 1
    assert result.elapsed_seconds >= 0


@pytest.mark.parametrize(("algorithm", "search"), ALL_SEARCHES)
def test_unsolvable_puzzle_is_rejected_without_constructing_a_frontier(
    algorithm: str, search: SearchCall
) -> None:
    puzzle = SlidingPuzzle(UNSOLVABLE_3X3, GOAL_3X3)

    result = search(puzzle)

    assert result.algorithm == algorithm
    assert result.status is SearchStatus.FAILURE
    assert not result.solved
    assert result.path == ()
    assert result.actions == ()
    assert result.cost is None
    assert result.solution_depth is None
    assert result.nodes_generated == 0
    assert result.nodes_expanded == 0
    assert result.max_frontier_size == 0
    assert result.elapsed_seconds >= 0


@pytest.mark.parametrize(("algorithm", "search"), ALL_SEARCHES)
def test_every_algorithm_solves_a_one_move_problem(
    algorithm: str, search: SearchCall
) -> None:
    puzzle = SlidingPuzzle(ONE_MOVE_START, ONE_MOVE_GOAL)

    result = search(puzzle)

    assert result.algorithm == algorithm
    assert_valid_solution(puzzle, result)
    assert result.actions == (Action.UP,)
    assert result.solution_depth == 1
    assert result.cost == 1
    assert result.nodes_generated >= 1
    assert result.nodes_expanded >= 0
    assert result.max_frontier_size >= 1
    assert result.elapsed_seconds >= 0


def test_optimal_searches_find_canonical_two_move_solution() -> None:
    puzzle = SlidingPuzzle(TWO_MOVE_START, GOAL_3X3)

    results = (
        breadth_first_search(puzzle),
        iterative_deepening_search(puzzle),
        uniform_cost_search(puzzle),
    )

    for result in results:
        assert_valid_solution(puzzle, result)
        assert result.actions == (Action.RIGHT, Action.RIGHT)
        assert result.solution_depth == 2
        assert result.cost == 2


def test_dfs_uses_lifo_order_and_returns_a_valid_nonoptimality_agnostic_path() -> None:
    puzzle = SlidingPuzzle(ONE_MOVE_START, DFS_TWO_MOVE_GOAL)

    result = depth_first_search(puzzle)

    assert_valid_solution(puzzle, result)
    assert result.actions == (Action.UP, Action.LEFT)


@pytest.mark.parametrize(
    "start",
    [
        GOAL_3X3,
        (1, 2, 3, 4, 5, 6, 7, 0, 8),
        TWO_MOVE_START,
        (1, 2, 3, 4, 0, 6, 7, 5, 8),
    ],
)
def test_bfs_ucs_and_ids_agree_on_optimal_cost_and_depth(
    start: tuple[int, ...],
) -> None:
    puzzle = SlidingPuzzle(start, GOAL_3X3)

    bfs_result = breadth_first_search(puzzle)
    ucs_result = uniform_cost_search(puzzle)
    ids_result = iterative_deepening_search(puzzle)

    assert_valid_solution(puzzle, bfs_result)
    assert_valid_solution(puzzle, ucs_result)
    assert_valid_solution(puzzle, ids_result)
    assert bfs_result.cost == ucs_result.cost == ids_result.cost
    assert (
        bfs_result.solution_depth
        == ucs_result.solution_depth
        == ids_result.solution_depth
    )


@pytest.mark.parametrize(
    "depth_limit",
    [-1, True],
)
def test_dls_rejects_invalid_depth_limits(depth_limit: int) -> None:
    puzzle = SlidingPuzzle(TWO_MOVE_START, GOAL_3X3)

    with pytest.raises(ValueError, match="non-negative integer"):
        depth_limited_search(puzzle, depth_limit)


def test_dls_distinguishes_cutoff_from_solution() -> None:
    puzzle = SlidingPuzzle(TWO_MOVE_START, GOAL_3X3)

    limit_zero = depth_limited_search(puzzle, 0)
    limit_one = depth_limited_search(puzzle, 1)
    limit_two = depth_limited_search(puzzle, 2)

    assert limit_zero.status is SearchStatus.CUTOFF
    assert limit_zero.nodes_generated == 1
    assert limit_zero.nodes_expanded == 0
    assert limit_zero.max_frontier_size == 1
    assert limit_one.status is SearchStatus.CUTOFF
    assert limit_two.status is SearchStatus.SOLVED
    assert_valid_solution(puzzle, limit_two)
    assert limit_two.solution_depth == 2


def test_ids_restarts_dls_and_accumulates_repeated_work() -> None:
    puzzle = SlidingPuzzle(TWO_MOVE_START, GOAL_3X3)

    final_iteration = depth_limited_search(puzzle, 2)
    ids_result = iterative_deepening_search(puzzle)

    assert_valid_solution(puzzle, ids_result)
    assert ids_result.solution_depth == 2
    assert ids_result.nodes_generated > final_iteration.nodes_generated
    assert ids_result.nodes_expanded > final_iteration.nodes_expanded
    assert ids_result.max_frontier_size == final_iteration.max_frontier_size


@pytest.mark.parametrize(
    "search",
    [breadth_first_search, depth_first_search, uniform_cost_search],
)
def test_graph_searches_terminate_without_cycles_in_returned_path(
    search: SearchCall,
) -> None:
    puzzle = SlidingPuzzle(ONE_MOVE_START, DFS_TWO_MOVE_GOAL)

    result = search(puzzle)

    assert_valid_solution(puzzle, result)
    assert len(set(result.path)) == len(result.path)


def test_search_node_is_lightweight_and_does_not_store_children() -> None:
    root = SearchNode(GOAL_3X3)

    assert root.parent is None
    assert root.action is None
    assert root.path_cost == 0
    assert root.depth == 0
    assert not hasattr(root, "children")
    assert not hasattr(root, "__dict__")


@pytest.mark.parametrize("heuristic", [misplaced_tiles, manhattan_distance])
def test_a_star_with_each_builtin_heuristic_solves_one_move_problem(
    heuristic: Heuristic,
) -> None:
    puzzle = SlidingPuzzle(ONE_MOVE_START, ONE_MOVE_GOAL)

    result = a_star_search(puzzle, heuristic)

    assert_valid_solution(puzzle, result)
    assert result.actions == (Action.UP,)
    assert result.solution_depth == 1
    assert result.cost == 1


@pytest.mark.parametrize("heuristic", [misplaced_tiles, manhattan_distance])
def test_a_star_with_each_builtin_heuristic_solves_two_move_problem(
    heuristic: Heuristic,
) -> None:
    puzzle = SlidingPuzzle(TWO_MOVE_START, GOAL_3X3)

    result = a_star_search(puzzle, heuristic)

    assert_valid_solution(puzzle, result)
    assert result.actions == (Action.RIGHT, Action.RIGHT)
    assert result.solution_depth == 2
    assert result.cost == 2


@pytest.mark.parametrize(
    "start",
    [
        GOAL_3X3,
        (1, 2, 3, 4, 5, 6, 7, 0, 8),
        TWO_MOVE_START,
        (1, 2, 3, 4, 0, 6, 7, 5, 8),
        (1, 2, 3, 5, 0, 6, 4, 7, 8),
    ],
)
def test_a_star_builtin_heuristics_match_bfs_optimal_solution_depth(
    start: tuple[int, ...],
) -> None:
    puzzle = SlidingPuzzle(start, GOAL_3X3)
    bfs_result = breadth_first_search(puzzle)

    for heuristic in (misplaced_tiles, manhattan_distance):
        result = a_star_search(puzzle, heuristic)
        assert_valid_solution(puzzle, result)
        assert result.cost == bfs_result.cost
        assert result.solution_depth == bfs_result.solution_depth


@pytest.mark.parametrize("heuristic", [misplaced_tiles, manhattan_distance])
def test_a_star_supports_nonstandard_goals(heuristic: Heuristic) -> None:
    start = (1, 2, 3, 4, 5, 6, 0, 7, 8)
    nonstandard_goal = (1, 2, 3, 4, 5, 6, 7, 0, 8)
    puzzle = SlidingPuzzle(start, nonstandard_goal)

    result = a_star_search(puzzle, heuristic)

    assert_valid_solution(puzzle, result)
    assert result.actions == (Action.RIGHT,)


def test_a_star_rejects_negative_heuristic_values() -> None:
    puzzle = SlidingPuzzle(TWO_MOVE_START, GOAL_3X3)

    def negative_heuristic(_: SlidingPuzzle, __: PuzzleState) -> int:
        return -1

    with pytest.raises(ValueError, match="negative value"):
        a_star_search(puzzle, negative_heuristic)


def test_a_star_rejects_noninteger_heuristic_values() -> None:
    puzzle = SlidingPuzzle(TWO_MOVE_START, GOAL_3X3)

    def floating_heuristic(_: SlidingPuzzle, __: PuzzleState) -> int:
        return 0.5  # type: ignore[return-value]

    with pytest.raises(ValueError, match="must return an integer"):
        a_star_search(puzzle, floating_heuristic)


@pytest.mark.parametrize("invalid_value", [True, False, "0", None])
def test_a_star_rejects_bool_and_unrelated_heuristic_values(
    invalid_value: object,
) -> None:
    puzzle = SlidingPuzzle(TWO_MOVE_START, GOAL_3X3)

    def invalid_heuristic(_: SlidingPuzzle, __: PuzzleState) -> int:
        return invalid_value  # type: ignore[return-value]

    with pytest.raises(ValueError, match="must return an integer"):
        a_star_search(puzzle, invalid_heuristic)


@pytest.mark.parametrize(
    "puzzle",
    [
        SlidingPuzzle(GOAL_3X3, GOAL_3X3),
        SlidingPuzzle(UNSOLVABLE_3X3, GOAL_3X3),
    ],
)
def test_a_star_fast_paths_do_not_evaluate_the_heuristic(
    puzzle: SlidingPuzzle,
) -> None:
    def unexpected_heuristic(_: SlidingPuzzle, __: PuzzleState) -> int:
        raise AssertionError("heuristic should not be evaluated")

    result = a_star_search(puzzle, unexpected_heuristic)

    assert result.nodes_expanded == 0
    if puzzle.start_state == puzzle.goal_state:
        assert result.status is SearchStatus.SOLVED
        assert result.nodes_generated == 1
        assert result.max_frontier_size == 1
    else:
        assert result.status is SearchStatus.FAILURE
        assert result.nodes_generated == 0
        assert result.max_frontier_size == 0
