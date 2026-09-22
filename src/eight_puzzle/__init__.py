"""Immutable sliding puzzles and classical search algorithms."""

from eight_puzzle.node import SearchNode
from eight_puzzle.puzzle import Action, PuzzleState, SlidingPuzzle
from eight_puzzle.result import SearchResult, SearchStatus
from eight_puzzle.search import (
    breadth_first_search,
    depth_first_search,
    depth_limited_search,
    iterative_deepening_search,
    uniform_cost_search,
)

__all__ = [
    "Action",
    "PuzzleState",
    "SearchNode",
    "SearchResult",
    "SearchStatus",
    "SlidingPuzzle",
    "breadth_first_search",
    "depth_first_search",
    "depth_limited_search",
    "iterative_deepening_search",
    "uniform_cost_search",
]
