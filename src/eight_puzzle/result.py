"""Structured search outcomes and shared metric definitions."""

from dataclasses import dataclass
from enum import Enum

from eight_puzzle.puzzle import Action, PuzzleState


class SearchStatus(str, Enum):
    """The three possible outcomes needed by the search algorithms."""

    SOLVED = "solved"
    FAILURE = "failure"
    CUTOFF = "cutoff"


@dataclass(frozen=True, slots=True)
class SearchResult:
    """The solution, outcome, and measurements from one public search call.

    ``nodes_generated`` counts the root when a frontier or DLS iteration is
    created, plus every successor candidate before duplicate or cycle checks.
    ``nodes_expanded`` counts only nodes whose successors are generated; a goal
    recognized before expansion is therefore not included. For BFS and DFS,
    ``max_frontier_size`` is the greatest queue or stack size. For UCS and A*
    it is the number of logically active best-cost states, excluding stale
    heap entries. For DLS and IDS it is the greatest active recursive path
    length.

    Timing uses ``time.perf_counter`` and includes the solvability precheck but
    excludes any presentation of the returned result. A puzzle rejected by
    that precheck constructs no frontier and reports zero search-work metrics.
    IDS metrics include every fresh depth-limited iteration; its maximum
    frontier is the maximum across iterations rather than their sum.
    """

    algorithm: str
    status: SearchStatus
    path: tuple[PuzzleState, ...]
    actions: tuple[Action, ...]
    cost: int | None
    solution_depth: int | None
    nodes_generated: int
    nodes_expanded: int
    max_frontier_size: int
    elapsed_seconds: float

    def __post_init__(self) -> None:
        """Reject internally inconsistent result combinations."""
        metrics = (
            self.nodes_generated,
            self.nodes_expanded,
            self.max_frontier_size,
        )
        if any(type(value) is not int or value < 0 for value in metrics):
            raise ValueError("search metrics must be non-negative integers")
        if self.nodes_expanded > self.nodes_generated:
            raise ValueError("expanded nodes cannot exceed generated nodes")
        if self.elapsed_seconds < 0:
            raise ValueError("elapsed time must be non-negative")

        if self.status is SearchStatus.SOLVED:
            if self.cost is None or self.solution_depth is None:
                raise ValueError("a solved result requires cost and solution depth")
            if self.cost < 0 or self.solution_depth < 0:
                raise ValueError("solution cost and depth must be non-negative")
            if not self.path or len(self.path) != len(self.actions) + 1:
                raise ValueError("a solved result requires a complete path")
            if self.solution_depth != len(self.actions):
                raise ValueError("solution depth must equal the action count")
            return

        if (
            self.path
            or self.actions
            or self.cost is not None
            or self.solution_depth is not None
        ):
            raise ValueError("failure and cutoff results cannot contain a solution")

    @property
    def solved(self) -> bool:
        """Return whether this result contains a solution."""
        return self.status is SearchStatus.SOLVED
