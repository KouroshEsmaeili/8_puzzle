"""Search-tree nodes used to reconstruct solution paths."""

from __future__ import annotations

from dataclasses import dataclass

from eight_puzzle.puzzle import Action, PuzzleState


@dataclass(slots=True)
class SearchNode:
    """A lightweight node with one parent link and no stored children."""

    state: PuzzleState
    parent: SearchNode | None = None
    action: Action | None = None
    path_cost: int = 0
    depth: int = 0
