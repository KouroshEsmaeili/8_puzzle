import csv
import json
from dataclasses import replace
from io import StringIO

import pytest

import eight_puzzle.benchmark as benchmark_module
from eight_puzzle import SlidingPuzzle, breadth_first_search
from eight_puzzle.benchmark import (
    BENCHMARK_CASES,
    BENCHMARK_VARIANTS,
    BenchmarkError,
    benchmark_csv,
    benchmark_json,
    benchmark_metadata,
    benchmark_table,
    run_benchmarks,
    select_benchmark_cases,
    select_benchmark_variants,
)
from eight_puzzle.cli import main


def test_benchmark_cases_are_unique_valid_solvable_and_ordered() -> None:
    assert [case.name for case in BENCHMARK_CASES] == [
        "easy",
        "medium",
        "medium-plus",
        "hard",
        "harder",
    ]
    assert len({case.name for case in BENCHMARK_CASES}) == len(BENCHMARK_CASES)

    for case in BENCHMARK_CASES:
        puzzle = SlidingPuzzle(case.start_state, case.goal_state)
        assert puzzle.is_solvable()


def test_benchmark_fixture_depths_are_independently_verified_by_bfs() -> None:
    for case in BENCHMARK_CASES:
        result = breadth_first_search(SlidingPuzzle(case.start_state, case.goal_state))

        assert result.solution_depth == case.optimal_depth
        assert result.cost == case.optimal_depth


def test_case_and_algorithm_filters_preserve_configured_order() -> None:
    cases = select_benchmark_cases(["harder", "easy"])
    astar_variants = select_benchmark_variants("astar")

    assert [case.name for case in cases] == ["easy", "harder"]
    assert [variant.key for variant in astar_variants] == [
        "astar-misplaced",
        "astar-manhattan",
    ]
    assert [variant.key for variant in BENCHMARK_VARIANTS] == [
        "bfs",
        "dfs",
        "ids",
        "ucs",
        "astar-misplaced",
        "astar-manhattan",
    ]


def test_repeated_benchmark_aggregates_actual_timing_samples() -> None:
    records = run_benchmarks(
        case_names=["easy"],
        algorithm="astar",
        heuristic="manhattan",
        repeat=3,
    )

    record = records[0]
    assert len(records) == 1
    assert len(record.timing_runs) == 3
    assert record.elapsed_min == min(record.timing_runs)
    assert record.elapsed_min <= record.elapsed_median <= max(record.timing_runs)
    assert record.elapsed_mean == pytest.approx(sum(record.timing_runs) / 3)
    assert record.solution_depth == record.optimal_depth == 2
    assert record.optimal is True


def test_repeated_benchmark_rejects_nondeterministic_metrics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = benchmark_module._run_variant
    call_count = 0

    def changing_run(puzzle: SlidingPuzzle, variant: object):
        nonlocal call_count
        result = original(puzzle, variant)  # type: ignore[arg-type]
        call_count += 1
        return replace(result, nodes_generated=result.nodes_generated + call_count)

    monkeypatch.setattr(benchmark_module, "_run_variant", changing_run)

    with pytest.raises(BenchmarkError, match="nondeterministic metrics"):
        run_benchmarks(
            case_names=["easy"],
            algorithm="astar",
            heuristic="manhattan",
            repeat=2,
        )


def test_benchmark_json_contains_metadata_and_plain_data() -> None:
    records = run_benchmarks(
        case_names=["easy"], algorithm="astar", heuristic="misplaced"
    )
    metadata = benchmark_metadata(1)

    payload = json.loads(benchmark_json(records, metadata))

    assert payload["metadata"]["repeat"] == 1
    assert payload["metadata"]["python_version"]
    assert payload["metadata"]["package_version"] == "0.1.0"
    assert payload["results"][0]["status"] == "solved"
    assert payload["results"][0]["heuristic"] == "misplaced"
    assert isinstance(payload["results"][0]["timing_runs"], list)


def test_benchmark_csv_has_header_metadata_and_one_row_per_record() -> None:
    records = run_benchmarks(case_names=["easy"], algorithm="bfs")
    metadata = benchmark_metadata(1)

    rows = list(csv.DictReader(StringIO(benchmark_csv(records, metadata))))

    assert len(rows) == len(records) == 1
    assert rows[0]["case"] == "easy"
    assert rows[0]["algorithm"] == "bfs"
    assert rows[0]["nodes_expanded"] == str(records[0].nodes_expanded)
    assert rows[0]["python_version"] == metadata["python_version"]
    assert rows[0]["timing_runs"]


def test_human_table_labels_frontier_as_proxy() -> None:
    records = run_benchmarks(
        case_names=["easy"], algorithm="astar", heuristic="manhattan"
    )

    output = benchmark_table(records, benchmark_metadata(1))

    assert "A* (Manhattan)" in output
    assert "Max Frontier" in output
    assert "not process RAM" in output
    assert "Median Time" in output


def test_metadata_avoids_sensitive_machine_identifiers() -> None:
    metadata = benchmark_metadata(2)

    assert set(metadata) == {
        "timestamp_utc",
        "python_version",
        "platform",
        "processor",
        "package_version",
        "repeat",
    }
    assert "hostname" not in metadata
    assert "username" not in metadata
    assert metadata["repeat"] == 2


def test_benchmark_cli_writes_json_to_explicit_path(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    destination = tmp_path / "results.json"

    exit_code = main(
        [
            "benchmark",
            "--case",
            "easy",
            "--algorithm",
            "astar",
            "--heuristic",
            "manhattan",
            "--json",
            "--output",
            str(destination),
        ]
    )

    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert len(payload["results"]) == 1
    assert payload["results"][0]["heuristic"] == "manhattan"
    assert "Wrote 1 benchmark records" in capsys.readouterr().out


@pytest.mark.parametrize(
    "arguments",
    [
        ["benchmark", "--repeat", "0"],
        ["benchmark", "--heuristic", "manhattan"],
        ["benchmark", "--output", "results.txt"],
    ],
)
def test_invalid_benchmark_options_exit_two(
    arguments: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as error:
        main(arguments)

    assert error.value.code == 2
    assert "error:" in capsys.readouterr().err
