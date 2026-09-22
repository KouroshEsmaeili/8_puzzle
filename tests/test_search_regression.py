from collections.abc import Callable

import pytest

from eight_puzzle import (
    Action,
    Heuristic,
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
from eight_puzzle.search.dls import _depth_limited_iteration

GOAL_3X3 = (1, 2, 3, 4, 5, 6, 7, 8, 0)
EASY_START = (1, 2, 3, 4, 0, 5, 6, 7, 8)
EASY_GOAL = (1, 0, 3, 4, 2, 5, 6, 7, 8)
DEPTH_FOUR_START = (1, 2, 3, 5, 0, 6, 4, 7, 8)
GOAL_4X4 = tuple(range(1, 16)) + (0,)

SearchCall = Callable[[SlidingPuzzle], SearchResult]


def _dls_one(puzzle: SlidingPuzzle) -> SearchResult:
    return depth_limited_search(puzzle, 1)


STARTED_SEARCHES: tuple[SearchCall, ...] = (
    breadth_first_search,
    depth_first_search,
    _dls_one,
    iterative_deepening_search,
    uniform_cost_search,
    a_star_search,
)


def _assert_valid_path(puzzle: SlidingPuzzle, result: SearchResult) -> None:
    assert result.solved
    assert result.path[0] == puzzle.start_state
    assert result.path[-1] == puzzle.goal_state
    assert result.solution_depth == len(result.actions)
    assert result.cost == len(result.actions)
    assert len(result.path) == len(result.actions) + 1
    assert all(left != right for left, right in zip(result.path, result.path[1:]))

    for state, action, successor in zip(
        result.path[:-1], result.actions, result.path[1:], strict=True
    ):
        assert puzzle.apply_action(state, action) == successor


@pytest.mark.parametrize("search", STARTED_SEARCHES)
def test_all_algorithms_share_metric_and_path_invariants(search: SearchCall) -> None:
    puzzle = SlidingPuzzle(EASY_START, EASY_GOAL)

    result = search(puzzle)

    _assert_valid_path(puzzle, result)
    assert result.nodes_generated >= 1
    assert 0 <= result.nodes_expanded <= result.nodes_generated
    assert result.max_frontier_size >= 1
    assert result.elapsed_seconds >= 0


def test_internal_dls_reports_genuine_failure_after_exhausting_a_component() -> None:
    puzzle = SlidingPuzzle((2, 1, 3, 0), (1, 2, 3, 0))

    outcome = _depth_limited_iteration(puzzle, 12)

    assert not puzzle.is_solvable()
    assert outcome.status is SearchStatus.FAILURE
    assert outcome.goal_node is None
    assert outcome.metrics.nodes_generated > 0
    assert outcome.metrics.nodes_expanded > 0


def test_ids_metrics_equal_fresh_depth_limited_iterations() -> None:
    puzzle = SlidingPuzzle(DEPTH_FOUR_START, GOAL_3X3)
    iterations = [_depth_limited_iteration(puzzle, limit) for limit in range(5)]

    result = iterative_deepening_search(puzzle)

    assert [outcome.status for outcome in iterations] == [
        SearchStatus.CUTOFF,
        SearchStatus.CUTOFF,
        SearchStatus.CUTOFF,
        SearchStatus.CUTOFF,
        SearchStatus.SOLVED,
    ]
    assert result.solution_depth == 4
    assert result.nodes_generated == sum(
        outcome.metrics.nodes_generated for outcome in iterations
    )
    assert result.nodes_expanded == sum(
        outcome.metrics.nodes_expanded for outcome in iterations
    )
    assert result.max_frontier_size == max(
        outcome.metrics.max_frontier_size for outcome in iterations
    )


@pytest.mark.parametrize("heuristic", [misplaced_tiles, manhattan_distance])
def test_a_star_solves_a_trivial_4x4_case(heuristic: Heuristic) -> None:
    start = tuple(range(1, 15)) + (0, 15)
    puzzle = SlidingPuzzle(start, GOAL_4X4)

    result = a_star_search(puzzle, heuristic)

    _assert_valid_path(puzzle, result)
    assert result.actions == (Action.RIGHT,)


@pytest.mark.parametrize("search", [uniform_cost_search, a_star_search])
def test_heap_search_tie_breaking_is_deterministic(search: SearchCall) -> None:
    puzzle = SlidingPuzzle(DEPTH_FOUR_START, GOAL_3X3)

    first = search(puzzle)
    second = search(puzzle)

    assert first.actions == second.actions
    assert first.nodes_generated == second.nodes_generated
    assert first.nodes_expanded == second.nodes_expanded
    assert first.max_frontier_size == second.max_frontier_size


def test_search_result_rejects_inconsistent_solved_and_terminal_states() -> None:
    common = {
        "algorithm": "test",
        "actions": (),
        "nodes_generated": 1,
        "nodes_expanded": 0,
        "max_frontier_size": 1,
        "elapsed_seconds": 0.0,
    }

    with pytest.raises(ValueError, match="requires cost"):
        SearchResult(
            status=SearchStatus.SOLVED,
            path=(GOAL_3X3,),
            cost=None,
            solution_depth=0,
            **common,
        )
    with pytest.raises(ValueError, match="cannot contain a solution"):
        SearchResult(
            status=SearchStatus.FAILURE,
            path=(GOAL_3X3,),
            cost=None,
            solution_depth=None,
            **common,
        )
    with pytest.raises(ValueError, match="non-negative integers"):
        SearchResult(
            status=SearchStatus.FAILURE,
            path=(),
            cost=None,
            solution_depth=None,
            **(common | {"nodes_generated": -1}),
        )
