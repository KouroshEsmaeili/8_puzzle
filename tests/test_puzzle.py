import pytest

from eight_puzzle import Action, SlidingPuzzle

GOAL_3X3 = (
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    0,
)
GOAL_4X4 = tuple(range(1, 16)) + (0,)


def test_valid_states_derive_board_size() -> None:
    puzzle_3x3 = SlidingPuzzle(GOAL_3X3, GOAL_3X3)
    puzzle_4x4 = SlidingPuzzle(GOAL_4X4, GOAL_4X4)

    assert puzzle_3x3.size == 3
    assert puzzle_4x4.size == 4


def test_constructor_normalizes_states_to_tuples() -> None:
    puzzle = SlidingPuzzle(list(GOAL_3X3), list(GOAL_3X3))

    assert isinstance(puzzle.start_state, tuple)
    assert isinstance(puzzle.goal_state, tuple)


@pytest.mark.parametrize(
    ("state", "message"),
    [
        ((1, 2, 3, 4, 5, 6, 7, 7, 0), "duplicate"),
        ((0, 1, 2, 3, 4, 5, 6, 7), "perfect square"),
        ((0, 1, 2, 3, 4, 5, 6, 7, -1), "missing"),
        ((0, 1, 2, 3, 4, 5, 6, 7, 9), "missing"),
        ((0, 1, 2, 3, 4, 5, 6, 7, "8"), "integers"),
        ((False, 1, 2, 3, 4, 5, 6, 7, 8), "integers"),
        ((0, True, 2, 3, 4, 5, 6, 7, 8), "integers"),
        ((0, 1.0, 2, 3, 4, 5, 6, 7, 8), "integers"),
    ],
)
def test_invalid_state_is_rejected(state: tuple[object, ...], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        SlidingPuzzle(state, GOAL_3X3)  # type: ignore[arg-type]


def test_missing_and_extra_tile_on_square_board_are_rejected() -> None:
    invalid = tuple(range(15)) + (16,)

    with pytest.raises(ValueError, match=r"missing=\[15\], extra=\[16\]"):
        SlidingPuzzle(invalid, GOAL_4X4)


def test_start_and_goal_dimensions_must_match() -> None:
    with pytest.raises(ValueError, match="matching dimensions"):
        SlidingPuzzle(GOAL_3X3, GOAL_4X4)


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ((0, 1, 2, 3, 4, 5, 6, 7, 8), (Action.DOWN, Action.RIGHT)),
        (
            (1, 0, 2, 3, 4, 5, 6, 7, 8),
            (Action.DOWN, Action.LEFT, Action.RIGHT),
        ),
        (
            (1, 2, 3, 4, 0, 5, 6, 7, 8),
            (Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT),
        ),
        ((1, 2, 3, 4, 5, 6, 7, 8, 0), (Action.UP, Action.LEFT)),
    ],
)
def test_legal_actions_are_ordered(
    state: tuple[int, ...], expected: tuple[Action, ...]
) -> None:
    puzzle = SlidingPuzzle(GOAL_3X3, GOAL_3X3)

    assert puzzle.legal_actions(state) == expected


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        (Action.UP, (1, 0, 3, 4, 2, 5, 6, 7, 8)),
        (Action.DOWN, (1, 2, 3, 4, 7, 5, 6, 0, 8)),
        (Action.LEFT, (1, 2, 3, 0, 4, 5, 6, 7, 8)),
        (Action.RIGHT, (1, 2, 3, 4, 5, 0, 6, 7, 8)),
    ],
)
def test_apply_action_returns_expected_new_state(
    action: Action, expected: tuple[int, ...]
) -> None:
    puzzle = SlidingPuzzle(GOAL_3X3, GOAL_3X3)
    source = (1, 2, 3, 4, 0, 5, 6, 7, 8)

    result = puzzle.apply_action(source, action)

    assert result == expected
    assert source == (1, 2, 3, 4, 0, 5, 6, 7, 8)
    assert result is not source


def test_illegal_and_unknown_actions_are_rejected() -> None:
    puzzle = SlidingPuzzle(GOAL_3X3, GOAL_3X3)
    upper_left = (0, 1, 2, 3, 4, 5, 6, 7, 8)

    with pytest.raises(ValueError, match="illegal"):
        puzzle.apply_action(upper_left, Action.UP)
    with pytest.raises(ValueError, match="unknown"):
        puzzle.apply_action(upper_left, "JUMP")  # type: ignore[arg-type]


def test_neighbors_have_expected_order_and_states() -> None:
    puzzle = SlidingPuzzle(GOAL_3X3, GOAL_3X3)
    upper_left = (0, 1, 2, 3, 4, 5, 6, 7, 8)

    assert puzzle.neighbors(upper_left) == (
        (Action.DOWN, (3, 1, 2, 0, 4, 5, 6, 7, 8)),
        (Action.RIGHT, (1, 0, 2, 3, 4, 5, 6, 7, 8)),
    )


def test_goal_detection() -> None:
    puzzle = SlidingPuzzle(GOAL_3X3, GOAL_3X3)

    assert puzzle.is_goal(GOAL_3X3)
    assert not puzzle.is_goal((1, 2, 3, 4, 5, 6, 7, 0, 8))


def test_states_are_immutable_hashable_values() -> None:
    state = tuple(GOAL_3X3)
    equivalent = tuple(list(GOAL_3X3))

    assert state == equivalent
    assert {state, equivalent} == {GOAL_3X3}
    assert {state: "goal"}[equivalent] == "goal"
    with pytest.raises(TypeError):
        state[0] = 0  # type: ignore[index]


def test_format_state_handles_blank_and_multi_digit_tiles() -> None:
    puzzle_3x3 = SlidingPuzzle(GOAL_3X3, GOAL_3X3)
    puzzle_4x4 = SlidingPuzzle(GOAL_4X4, GOAL_4X4)

    assert puzzle_3x3.format_state(GOAL_3X3) == "1 2 3\n4 5 6\n7 8 ·"
    assert puzzle_4x4.format_state(GOAL_4X4) == (
        " 1  2  3  4\n 5  6  7  8\n 9 10 11 12\n13 14 15  ·"
    )


def test_methods_reject_state_from_another_board_size() -> None:
    puzzle = SlidingPuzzle(GOAL_3X3, GOAL_3X3)

    with pytest.raises(ValueError, match="3x3"):
        puzzle.neighbors(GOAL_4X4)
