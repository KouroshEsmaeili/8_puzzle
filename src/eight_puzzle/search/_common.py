"""Small shared helpers for the independent search implementations."""

from dataclasses import dataclass
from time import perf_counter

from eight_puzzle.node import SearchNode
from eight_puzzle.puzzle import Action, PuzzleState, SlidingPuzzle
from eight_puzzle.result import SearchResult, SearchStatus


@dataclass(slots=True)
class SearchMetrics:
    """Mutable counters used internally while a search is running."""

    nodes_generated: int = 0
    nodes_expanded: int = 0
    max_frontier_size: int = 0


def reconstruct_solution(
    goal_node: SearchNode,
) -> tuple[tuple[PuzzleState, ...], tuple[Action, ...]]:
    """Follow parent links and return start-to-goal states and actions."""
    reverse_path: list[PuzzleState] = []
    reverse_actions: list[Action] = []
    node: SearchNode | None = goal_node

    while node is not None:
        reverse_path.append(node.state)
        if node.action is not None:
            reverse_actions.append(node.action)
        node = node.parent

    return tuple(reversed(reverse_path)), tuple(reversed(reverse_actions))


def solved_result(
    algorithm: str,
    goal_node: SearchNode,
    metrics: SearchMetrics,
    started_at: float,
) -> SearchResult:
    """Build a successful result from a goal node and current metrics."""
    path, actions = reconstruct_solution(goal_node)
    return SearchResult(
        algorithm=algorithm,
        status=SearchStatus.SOLVED,
        path=path,
        actions=actions,
        cost=goal_node.path_cost,
        solution_depth=goal_node.depth,
        nodes_generated=metrics.nodes_generated,
        nodes_expanded=metrics.nodes_expanded,
        max_frontier_size=metrics.max_frontier_size,
        elapsed_seconds=perf_counter() - started_at,
    )


def terminal_result(
    algorithm: str,
    status: SearchStatus,
    metrics: SearchMetrics,
    started_at: float,
) -> SearchResult:
    """Build a failure or cutoff result without a solution path."""
    if status is SearchStatus.SOLVED:
        raise ValueError("a solved result requires a goal node")
    return SearchResult(
        algorithm=algorithm,
        status=status,
        path=(),
        actions=(),
        cost=None,
        solution_depth=None,
        nodes_generated=metrics.nodes_generated,
        nodes_expanded=metrics.nodes_expanded,
        max_frontier_size=metrics.max_frontier_size,
        elapsed_seconds=perf_counter() - started_at,
    )


def pre_search_result(
    puzzle: SlidingPuzzle,
    algorithm: str,
    started_at: float,
) -> SearchResult | None:
    """Handle the immediate-goal and mathematical-unsolvability cases."""
    if puzzle.start_state == puzzle.goal_state:
        root = SearchNode(puzzle.start_state)
        return solved_result(
            algorithm,
            root,
            SearchMetrics(nodes_generated=1, max_frontier_size=1),
            started_at,
        )

    if not puzzle.is_solvable():
        return terminal_result(
            algorithm,
            SearchStatus.FAILURE,
            SearchMetrics(),
            started_at,
        )

    return None
