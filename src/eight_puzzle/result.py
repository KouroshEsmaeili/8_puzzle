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

    @property
    def solved(self) -> bool:
        """Return whether this result contains a solution."""
        return self.status is SearchStatus.SOLVED
