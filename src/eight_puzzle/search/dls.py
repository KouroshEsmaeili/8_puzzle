"""Depth-limited search with path-based cycle detection."""

from dataclasses import dataclass
from time import perf_counter

from eight_puzzle.node import SearchNode
from eight_puzzle.puzzle import SlidingPuzzle
from eight_puzzle.result import SearchResult, SearchStatus
from eight_puzzle.search._common import (
    SearchMetrics,
    pre_search_result,
    solved_result,
    terminal_result,
)


@dataclass(slots=True)
class _DepthLimitedOutcome:
    status: SearchStatus
    goal_node: SearchNode | None
    metrics: SearchMetrics


def _depth_limited_iteration(
    puzzle: SlidingPuzzle, depth_limit: int
) -> _DepthLimitedOutcome:
    """Run one fresh DLS iteration without timing or solvability checks."""
    root = SearchNode(puzzle.start_state)
    metrics = SearchMetrics(nodes_generated=1, max_frontier_size=1)
    path_states = {root.state}

    def visit(node: SearchNode) -> tuple[SearchStatus, SearchNode | None]:
        if node.state == puzzle.goal_state:
            return SearchStatus.SOLVED, node
        if node.depth == depth_limit:
            return SearchStatus.CUTOFF, None

        metrics.nodes_expanded += 1
        cutoff_occurred = False

        for action, state in puzzle.neighbors(node.state):
            metrics.nodes_generated += 1
            if state in path_states:
                continue

            child = SearchNode(
                state=state,
                parent=node,
                action=action,
                path_cost=node.path_cost + 1,
                depth=node.depth + 1,
            )
            path_states.add(state)
            metrics.max_frontier_size = max(metrics.max_frontier_size, len(path_states))
            status, goal_node = visit(child)
            path_states.remove(state)

            if status is SearchStatus.SOLVED:
                return status, goal_node
            if status is SearchStatus.CUTOFF:
                cutoff_occurred = True

        if cutoff_occurred:
            return SearchStatus.CUTOFF, None
        return SearchStatus.FAILURE, None

    status, goal_node = visit(root)
    return _DepthLimitedOutcome(status, goal_node, metrics)


def depth_limited_search(puzzle: SlidingPuzzle, depth_limit: int) -> SearchResult:
    """Search depth-first up to ``depth_limit`` with standard cutoff semantics."""
    if type(depth_limit) is not int or depth_limit < 0:
        raise ValueError("depth_limit must be a non-negative integer")

    started_at = perf_counter()
    early_result = pre_search_result(puzzle, "dls", started_at)
    if early_result is not None:
        return early_result

    outcome = _depth_limited_iteration(puzzle, depth_limit)
    if outcome.status is SearchStatus.SOLVED:
        if outcome.goal_node is None:
            raise RuntimeError("solved DLS outcome is missing its goal node")
        return solved_result("dls", outcome.goal_node, outcome.metrics, started_at)
    return terminal_result("dls", outcome.status, outcome.metrics, started_at)
