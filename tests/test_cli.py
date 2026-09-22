import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from eight_puzzle.cli import main, parse_state

TWO_MOVE = "1 2 3 4 5 6 0 7 8"
GOAL_3X3 = "1 2 3 4 5 6 7 8 0"


@pytest.mark.parametrize(
    "text",
    [
        "1 2 3 4 5 6 7 8 0",
        "1,2,3,4,5,6,7,8,0",
        "1, 2, 3, 4, 5, 6, 7, 8, 0",
    ],
)
def test_parse_state_supports_whitespace_and_commas(text: str) -> None:
    assert parse_state(text) == (1, 2, 3, 4, 5, 6, 7, 8, 0)


def test_bfs_solve_human_output_is_concise(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["solve", "--algorithm", "bfs", "--start", TWO_MOVE])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Algorithm: BFS" in output
    assert "Status: solved" in output
    assert "Solution depth: 2" in output
    assert "RIGHT RIGHT" in output
    assert "Step 0" not in output


def test_astar_json_output_has_stable_machine_fields(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "solve",
            "--algorithm",
            "astar",
            "--heuristic",
            "misplaced",
            "--start",
            TWO_MOVE,
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["algorithm"] == "astar"
    assert payload["heuristic"] == "misplaced"
    assert payload["status"] == "solved"
    assert payload["solution_depth"] == payload["cost"] == 2
    assert payload["actions"] == ["RIGHT", "RIGHT"]
    assert "path" not in payload


def test_show_path_formats_boards(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "solve",
            "--algorithm",
            "astar",
            "--start",
            TWO_MOVE,
            "--show-path",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Heuristic: Manhattan" in output
    assert "Step 0 (start):" in output
    assert "Step 2 (RIGHT):" in output
    assert "7 8 ·" in output


def test_json_show_path_contains_plain_lists(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "solve",
            "--algorithm",
            "astar",
            "--start",
            TWO_MOVE,
            "--json",
            "--show-path",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["path"][0] == [1, 2, 3, 4, 5, 6, 0, 7, 8]
    assert payload["path"][-1] == [1, 2, 3, 4, 5, 6, 7, 8, 0]


def test_dls_cutoff_is_distinct_and_returns_exit_one(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "solve",
            "--algorithm",
            "dls",
            "--depth-limit",
            "1",
            "--start",
            TWO_MOVE,
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Status: cutoff" in output
    assert "Solution depth: n/a" in output


def test_unsolvable_request_returns_failure_exit_one(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "solve",
            "--algorithm",
            "astar",
            "--start",
            "1 2 3 4 5 6 8 7 0",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["status"] == "failure"
    assert payload["nodes_generated"] == 0


def test_default_goal_is_inferred_for_4x4(capsys: pytest.CaptureFixture[str]) -> None:
    start = "1 2 3 4 5 6 7 8 9 10 11 12 13 14 0 15"

    exit_code = main(["solve", "--algorithm", "astar", "--start", start, "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["solution_depth"] == 1
    assert payload["actions"] == ["RIGHT"]


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (
            ["solve", "--algorithm", "greedy", "--start", TWO_MOVE],
            "invalid choice",
        ),
        (
            [
                "solve",
                "--algorithm",
                "astar",
                "--heuristic",
                "euclidean",
                "--start",
                TWO_MOVE,
            ],
            "invalid choice",
        ),
        (["solve", "--algorithm", "dls", "--start", TWO_MOVE], "required for DLS"),
        (
            [
                "solve",
                "--algorithm",
                "dls",
                "--depth-limit",
                "-1",
                "--start",
                TWO_MOVE,
            ],
            "must be non-negative",
        ),
        (
            [
                "solve",
                "--algorithm",
                "bfs",
                "--heuristic",
                "manhattan",
                "--start",
                TWO_MOVE,
            ],
            "only be used with A",
        ),
        (
            [
                "solve",
                "--algorithm",
                "bfs",
                "--depth-limit",
                "2",
                "--start",
                TWO_MOVE,
            ],
            "only be used with DLS",
        ),
        (
            ["solve", "--algorithm", "bfs", "--start", "1 2 x 4"],
            "integers only",
        ),
        (
            ["solve", "--algorithm", "bfs", "--start", "1 2 3 4 5 6 7 7 0"],
            "duplicate",
        ),
        (
            [
                "solve",
                "--algorithm",
                "bfs",
                "--start",
                TWO_MOVE,
                "--goal",
                "1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 0",
            ],
            "matching dimensions",
        ),
    ],
)
def test_normal_user_errors_exit_two_without_tracebacks(
    arguments: list[str], message: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as error:
        main(arguments)

    stderr = capsys.readouterr().err
    assert error.value.code == 2
    assert message in stderr
    assert "Traceback" not in stderr


def test_module_entry_point_help_runs_successfully() -> None:
    repository = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(repository / "src")

    completed = subprocess.run(
        [sys.executable, "-m", "eight_puzzle", "--help"],
        cwd=repository,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "solve" in completed.stdout
    assert "benchmark" in completed.stdout
    assert "Exit codes:" in completed.stdout
    assert completed.stderr == ""
