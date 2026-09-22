"""Iterative deepening implemented as repeated fresh DLS iterations."""

from time import perf_counter

from eight_puzzle.puzzle import SlidingPuzzle
from eight_puzzle.result import SearchResult, SearchStatus
from eight_puzzle.search._common import (
    SearchMetrics,
    pre_search_result,
    solved_result,
    terminal_result,
)
from eight_puzzle.search.dls import _depth_limited_iteration


def iterative_deepening_search(puzzle: SlidingPuzzle) -> SearchResult:
    """Increase the depth limit until fresh DLS finds a solution or fails.

    Generated and expanded counts accumulate repeated work from every limit;
    the maximum frontier is the largest active path in any one iteration.
    """
    started_at = perf_counter()
    early_result = pre_search_result(puzzle, "ids", started_at)
    if early_result is not None:
        return early_result

    cumulative = SearchMetrics()
    depth_limit = 0

    while True:
        outcome = _depth_limited_iteration(puzzle, depth_limit)
        cumulative.nodes_generated += outcome.metrics.nodes_generated
        cumulative.nodes_expanded += outcome.metrics.nodes_expanded
        cumulative.max_frontier_size = max(
            cumulative.max_frontier_size, outcome.metrics.max_frontier_size
        )

        if outcome.status is SearchStatus.SOLVED:
            if outcome.goal_node is None:
                raise RuntimeError("solved IDS outcome is missing its goal node")
            return solved_result("ids", outcome.goal_node, cumulative, started_at)
        if outcome.status is SearchStatus.FAILURE:
            return terminal_result("ids", SearchStatus.FAILURE, cumulative, started_at)

        depth_limit += 1
