"""Breadth-first graph search for unit-cost sliding puzzles."""

from collections import deque
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


def breadth_first_search(puzzle: SlidingPuzzle) -> SearchResult:
    """Find a shortest solution using a FIFO frontier.

    States are marked discovered when enqueued, preventing duplicate frontier
    entries and repeated expansion.
    """
    started_at = perf_counter()
    early_result = pre_search_result(puzzle, "bfs", started_at)
    if early_result is not None:
        return early_result

    root = SearchNode(puzzle.start_state)
    frontier = deque([root])
    discovered = {root.state}
    metrics = SearchMetrics(nodes_generated=1, max_frontier_size=1)

    while frontier:
        node = frontier.popleft()
        if node.state == puzzle.goal_state:
            return solved_result("bfs", node, metrics, started_at)

        metrics.nodes_expanded += 1
        for action, state in puzzle.neighbors(node.state):
            metrics.nodes_generated += 1
            if state in discovered:
                continue

            discovered.add(state)
            frontier.append(
                SearchNode(
                    state=state,
                    parent=node,
                    action=action,
                    path_cost=node.path_cost + 1,
                    depth=node.depth + 1,
                )
            )
            metrics.max_frontier_size = max(metrics.max_frontier_size, len(frontier))

    return terminal_result("bfs", SearchStatus.FAILURE, metrics, started_at)
