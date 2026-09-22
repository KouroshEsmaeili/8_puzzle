"""Depth-first graph search with deterministic stack ordering."""

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


def depth_first_search(puzzle: SlidingPuzzle) -> SearchResult:
    """Find a solution using a LIFO stack and graph duplicate detection.

    Successors arrive as UP, DOWN, LEFT, RIGHT and are pushed in reverse so the
    intended order is also the order in which the stack explores them. DFS is
    complete on this finite graph but does not guarantee a shortest solution.
    """
    started_at = perf_counter()
    early_result = pre_search_result(puzzle, "dfs", started_at)
    if early_result is not None:
        return early_result

    root = SearchNode(puzzle.start_state)
    frontier = [root]
    discovered = {root.state}
    metrics = SearchMetrics(nodes_generated=1, max_frontier_size=1)

    while frontier:
        node = frontier.pop()
        if node.state == puzzle.goal_state:
            return solved_result("dfs", node, metrics, started_at)

        metrics.nodes_expanded += 1
        for action, state in reversed(puzzle.neighbors(node.state)):
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

    return terminal_result("dfs", SearchStatus.FAILURE, metrics, started_at)
