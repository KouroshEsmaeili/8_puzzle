"""A* graph search using path cost plus a goal-aware heuristic."""

import heapq
from collections.abc import Callable
from itertools import count
from time import perf_counter

from eight_puzzle.heuristics import (
    Heuristic,
    _build_heuristic_evaluator,
    manhattan_distance,
)
from eight_puzzle.node import SearchNode
from eight_puzzle.puzzle import PuzzleState, SlidingPuzzle
from eight_puzzle.result import SearchResult, SearchStatus
from eight_puzzle.search._common import (
    SearchMetrics,
    pre_search_result,
    solved_result,
    terminal_result,
)


def _checked_heuristic_value(
    heuristic: Heuristic,
    state_heuristic: Callable[[PuzzleState], int],
    state: PuzzleState,
) -> int:
    value = state_heuristic(state)
    if type(value) is not int:
        raise ValueError(
            f"heuristic {heuristic!r} must return an integer, got {value!r}"
        )
    if value < 0:
        raise ValueError(f"heuristic {heuristic!r} returned negative value {value}")
    return value


def a_star_search(
    puzzle: SlidingPuzzle,
    heuristic: Heuristic = manhattan_distance,
) -> SearchResult:
    """Find a least-cost solution by prioritizing ``g(n) + h(n)``.

    Priority ties prefer lower heuristic values, then insertion order. The
    counter keeps ``SearchNode`` objects out of comparison operations. A*
    reopens a state whenever a cheaper path is found and ignores lazy stale
    heap entries. Optimality requires an appropriately admissible heuristic.
    """
    started_at = perf_counter()
    early_result = pre_search_result(puzzle, "astar", started_at)
    if early_result is not None:
        return early_result

    state_heuristic = _build_heuristic_evaluator(puzzle, heuristic)
    root = SearchNode(puzzle.start_state)
    root_h = _checked_heuristic_value(heuristic, state_heuristic, root.state)
    tie_breaker = count()
    frontier: list[tuple[int, int, int, SearchNode]] = [
        (root_h, root_h, next(tie_breaker), root)
    ]
    best_g: dict[PuzzleState, int] = {root.state: 0}
    active_states = {root.state}
    metrics = SearchMetrics(nodes_generated=1, max_frontier_size=1)

    while frontier:
        _, _, _, node = heapq.heappop(frontier)
        if node.path_cost != best_g.get(node.state) or node.state not in active_states:
            continue

        active_states.remove(node.state)
        if node.state == puzzle.goal_state:
            return solved_result("astar", node, metrics, started_at)

        metrics.nodes_expanded += 1
        for action, state in puzzle.neighbors(node.state):
            metrics.nodes_generated += 1
            candidate_g = node.path_cost + 1
            known_g = best_g.get(state)
            if known_g is not None and candidate_g >= known_g:
                continue

            best_g[state] = candidate_g
            child = SearchNode(
                state=state,
                parent=node,
                action=action,
                path_cost=candidate_g,
                depth=node.depth + 1,
            )
            child_h = _checked_heuristic_value(heuristic, state_heuristic, state)
            heapq.heappush(
                frontier,
                (candidate_g + child_h, child_h, next(tie_breaker), child),
            )
            active_states.add(state)
            metrics.max_frontier_size = max(
                metrics.max_frontier_size, len(active_states)
            )

    return terminal_result("astar", SearchStatus.FAILURE, metrics, started_at)
