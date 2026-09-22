"""Classical uninformed search algorithms for sliding puzzles."""

from eight_puzzle.search.bfs import breadth_first_search
from eight_puzzle.search.dfs import depth_first_search
from eight_puzzle.search.dls import depth_limited_search
from eight_puzzle.search.ids import iterative_deepening_search
from eight_puzzle.search.ucs import uniform_cost_search

__all__ = [
    "breadth_first_search",
    "depth_first_search",
    "depth_limited_search",
    "iterative_deepening_search",
    "uniform_cost_search",
]
