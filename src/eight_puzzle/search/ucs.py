"""Uniform-cost graph search using a best-cost heap frontier."""

import heapq
from itertools import count
from time import perf_counter

from eight_puzzle.node import SearchNode
from eight_puzzle.puzzle import PuzzleState, SlidingPuzzle
from eight_puzzle.result import SearchResult, SearchStatus
from eight_puzzle.search._common import (
    SearchMetrics,
    pre_search_result,
    solved_result,
    terminal_result,
)


def uniform_cost_search(puzzle: SlidingPuzzle) -> SearchResult:
    """Find a least-cost solution using ``g(n)`` and deterministic tie breaks.

    With the current unit move costs, UCS returns the same optimal cost as BFS,
    although the algorithms are not generally equivalent on weighted graphs.
    Lazy stale heap entries are excluded from the logical frontier metric.
    """
    started_at = perf_counter()
    early_result = pre_search_result(puzzle, "ucs", started_at)
    if early_result is not None:
        return early_result

    root = SearchNode(puzzle.start_state)
    tie_breaker = count()
    frontier: list[tuple[int, int, SearchNode]] = [
        (root.path_cost, next(tie_breaker), root)
    ]
    best_g: dict[PuzzleState, int] = {root.state: 0}
    active_states = {root.state}
    metrics = SearchMetrics(nodes_generated=1, max_frontier_size=1)

    while frontier:
        path_cost, _, node = heapq.heappop(frontier)
        if path_cost != best_g.get(node.state) or node.state not in active_states:
            continue

        active_states.remove(node.state)
        if node.state == puzzle.goal_state:
            return solved_result("ucs", node, metrics, started_at)

        metrics.nodes_expanded += 1
        for action, state in puzzle.neighbors(node.state):
            metrics.nodes_generated += 1
            candidate_cost = node.path_cost + 1
            if candidate_cost >= best_g.get(state, float("inf")):
                continue

            best_g[state] = candidate_cost
            child = SearchNode(
                state=state,
                parent=node,
                action=action,
                path_cost=candidate_cost,
                depth=node.depth + 1,
            )
            heapq.heappush(
                frontier,
                (candidate_cost, next(tie_breaker), child),
            )
            active_states.add(state)
            metrics.max_frontier_size = max(
                metrics.max_frontier_size, len(active_states)
            )

    return terminal_result("ucs", SearchStatus.FAILURE, metrics, started_at)
