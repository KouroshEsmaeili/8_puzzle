"""Immutable state representation and transition rules for sliding puzzles."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isqrt
from typing import Iterable

PuzzleState = tuple[int, ...]


class Action(str, Enum):
    """A move of the blank tile."""

    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


ACTION_ORDER: tuple[Action, ...] = (
    Action.UP,
    Action.DOWN,
    Action.LEFT,
    Action.RIGHT,
)

_ACTION_DELTAS: dict[Action, tuple[int, int]] = {
    Action.UP: (-1, 0),
    Action.DOWN: (1, 0),
    Action.LEFT: (0, -1),
    Action.RIGHT: (0, 1),
}


def _normalize_state(state: Iterable[int], *, label: str) -> tuple[PuzzleState, int]:
    try:
        normalized = tuple(state)
    except TypeError as exc:
        raise ValueError(f"{label} must be an iterable of integers") from exc

    if not normalized:
        raise ValueError(f"{label} must not be empty")
    if any(type(tile) is not int for tile in normalized):
        raise ValueError(f"{label} must contain integers only")

    size = isqrt(len(normalized))
    if size * size != len(normalized):
        raise ValueError(f"{label} length must be a perfect square")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{label} must not contain duplicate tiles")

    expected = set(range(len(normalized)))
    actual = set(normalized)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(
            f"{label} must contain every tile from 0 to {len(normalized) - 1}; "
            f"missing={missing}, extra={extra}"
        )

    return normalized, size


def _inversion_parity(values: tuple[int, ...]) -> int:
    inversions = sum(
        left > right
        for index, left in enumerate(values)
        for right in values[index + 1 :]
    )
    return inversions % 2


@dataclass(frozen=True, slots=True)
class SlidingPuzzle:
    """A square sliding-puzzle problem with a configured start and goal."""

    start_state: PuzzleState
    goal_state: PuzzleState
    size: int = field(init=False)

    def __post_init__(self) -> None:
        start_state, start_size = _normalize_state(
            self.start_state, label="start state"
        )
        goal_state, goal_size = _normalize_state(self.goal_state, label="goal state")
        if start_size != goal_size:
            raise ValueError("start and goal states must have matching dimensions")

        object.__setattr__(self, "start_state", start_state)
        object.__setattr__(self, "goal_state", goal_state)
        object.__setattr__(self, "size", start_size)

    def validate_state(self, state: Iterable[int]) -> PuzzleState:
        """Validate and return a state normalized to an immutable tuple."""
        normalized, size = _normalize_state(state, label="state")
        if size != self.size:
            raise ValueError(f"state must describe a {self.size}x{self.size} board")
        return normalized

    def is_goal(self, state: Iterable[int]) -> bool:
        """Return whether a valid state equals this problem's goal."""
        return self.validate_state(state) == self.goal_state

    def legal_actions(self, state: Iterable[int]) -> tuple[Action, ...]:
        """Return legal blank moves in UP, DOWN, LEFT, RIGHT order."""
        normalized = self.validate_state(state)
        return self._legal_actions(normalized)

    def _legal_actions(self, state: PuzzleState) -> tuple[Action, ...]:
        blank_row, blank_column = divmod(state.index(0), self.size)
        legal: list[Action] = []
        for action in ACTION_ORDER:
            row_delta, column_delta = _ACTION_DELTAS[action]
            new_row = blank_row + row_delta
            new_column = blank_column + column_delta
            if 0 <= new_row < self.size and 0 <= new_column < self.size:
                legal.append(action)
        return tuple(legal)

    def apply_action(self, state: Iterable[int], action: Action) -> PuzzleState:
        """Apply one legal blank move and return a new immutable state."""
        normalized = self.validate_state(state)
        if not isinstance(action, Action):
            raise ValueError(f"unknown action: {action!r}")
        if action not in self._legal_actions(normalized):
            raise ValueError(f"action {action.value} is illegal for this state")
        return self._apply_legal_action(normalized, action)

    def _apply_legal_action(self, state: PuzzleState, action: Action) -> PuzzleState:
        blank_index = state.index(0)
        blank_row, blank_column = divmod(blank_index, self.size)
        row_delta, column_delta = _ACTION_DELTAS[action]
        target_row = blank_row + row_delta
        target_column = blank_column + column_delta
        target_index = target_row * self.size + target_column

        result = list(state)
        result[blank_index], result[target_index] = (
            result[target_index],
            result[blank_index],
        )
        return tuple(result)

    def neighbors(self, state: Iterable[int]) -> tuple[tuple[Action, PuzzleState], ...]:
        """Return all valid action/state successors in deterministic order."""
        normalized = self.validate_state(state)
        return tuple(
            (action, self._apply_legal_action(normalized, action))
            for action in self._legal_actions(normalized)
        )

    def is_solvable(self, state: Iterable[int] | None = None) -> bool:
        """Return whether a state is reachable from the configured goal.

        Numbered tiles are ranked by their flattened order in the configured
        goal. For odd widths, the inversion parity of those ranks is invariant.
        For even widths, a vertical blank move toggles both inversion parity and
        the parity of the blank's zero-based row from the top, so their sum is
        invariant. Comparing that invariant with the goal handles arbitrary
        goal arrangements without assuming the conventional goal.
        """
        normalized = self.start_state if state is None else self.validate_state(state)
        goal_rank = {
            tile: rank
            for rank, tile in enumerate(tile for tile in self.goal_state if tile != 0)
        }
        relative_order = tuple(goal_rank[tile] for tile in normalized if tile != 0)
        inversion_parity = _inversion_parity(relative_order)

        if self.size % 2 == 1:
            return inversion_parity == 0

        blank_row = normalized.index(0) // self.size
        goal_blank_row = self.goal_state.index(0) // self.size
        return (inversion_parity + blank_row) % 2 == goal_blank_row % 2

    def format_state(self, state: Iterable[int]) -> str:
        """Return a readable board string, using a middle dot for the blank."""
        normalized = self.validate_state(state)
        cell_width = max(
            (len(str(tile)) for tile in normalized if tile != 0), default=1
        )
        cells = ["·" if tile == 0 else str(tile) for tile in normalized]
        rows = (
            cells[index : index + self.size]
            for index in range(0, len(cells), self.size)
        )
        return "\n".join(
            " ".join(f"{cell:>{cell_width}}" for cell in row) for row in rows
        )
