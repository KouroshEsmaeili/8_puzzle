"""Deterministic benchmark cases and aggregation for the search algorithms."""

from __future__ import annotations

import csv
import json
import platform
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from io import StringIO
from statistics import fmean, median
from typing import Any, Sequence

from eight_puzzle.heuristics import manhattan_distance, misplaced_tiles
from eight_puzzle.puzzle import PuzzleState, SlidingPuzzle
from eight_puzzle.result import SearchResult, SearchStatus
from eight_puzzle.search import (
    a_star_search,
    breadth_first_search,
    depth_first_search,
    iterative_deepening_search,
    uniform_cost_search,
)

CANONICAL_GOAL: PuzzleState = (1, 2, 3, 4, 5, 6, 7, 8, 0)


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    """A fixed puzzle with an independently verified optimal depth."""

    name: str
    start_state: PuzzleState
    goal_state: PuzzleState
    optimal_depth: int


BENCHMARK_CASES: tuple[BenchmarkCase, ...] = (
    BenchmarkCase("easy", (1, 2, 3, 4, 5, 6, 0, 7, 8), CANONICAL_GOAL, 2),
    BenchmarkCase("medium", (1, 3, 6, 5, 0, 2, 4, 7, 8), CANONICAL_GOAL, 8),
    BenchmarkCase("medium-plus", (0, 1, 2, 3, 5, 6, 4, 7, 8), CANONICAL_GOAL, 12),
    BenchmarkCase("hard", (0, 1, 2, 3, 4, 5, 7, 8, 6), CANONICAL_GOAL, 16),
    BenchmarkCase("harder", (0, 1, 2, 3, 4, 7, 8, 5, 6), CANONICAL_GOAL, 20),
)


@dataclass(frozen=True, slots=True)
class BenchmarkVariant:
    """One algorithm configuration used in the comparison."""

    key: str
    algorithm: str
    display_name: str
    heuristic: str | None
    expected_optimal: bool


BENCHMARK_VARIANTS: tuple[BenchmarkVariant, ...] = (
    BenchmarkVariant("bfs", "bfs", "BFS", None, True),
    BenchmarkVariant("dfs", "dfs", "DFS", None, False),
    BenchmarkVariant("ids", "ids", "IDS", None, True),
    BenchmarkVariant("ucs", "ucs", "UCS", None, True),
    BenchmarkVariant("astar-misplaced", "astar", "A* (Misplaced)", "misplaced", True),
    BenchmarkVariant("astar-manhattan", "astar", "A* (Manhattan)", "manhattan", True),
)

BENCHMARK_ALGORITHMS: tuple[str, ...] = ("bfs", "dfs", "ids", "ucs", "astar")
BENCHMARK_HEURISTICS: tuple[str, ...] = ("misplaced", "manhattan")


class BenchmarkError(RuntimeError):
    """Raised when a benchmark result would be misleading or inconsistent."""


@dataclass(frozen=True, slots=True)
class BenchmarkRecord:
    """Aggregated deterministic metrics and repeated timing samples."""

    case: str
    algorithm: str
    display_name: str
    heuristic: str | None
    optimal_depth: int
    status: str
    solution_depth: int
    cost: int
    optimal: bool | None
    nodes_generated: int
    nodes_expanded: int
    max_frontier_size: int
    timing_runs: tuple[float, ...]
    elapsed_min: float
    elapsed_median: float
    elapsed_mean: float

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "case": self.case,
            "algorithm": self.algorithm,
            "display_name": self.display_name,
            "heuristic": self.heuristic,
            "optimal_depth": self.optimal_depth,
            "status": self.status,
            "solution_depth": self.solution_depth,
            "cost": self.cost,
            "optimal": self.optimal,
            "nodes_generated": self.nodes_generated,
            "nodes_expanded": self.nodes_expanded,
            "max_frontier_size": self.max_frontier_size,
            "timing_runs": list(self.timing_runs),
            "elapsed_min": self.elapsed_min,
            "elapsed_median": self.elapsed_median,
            "elapsed_mean": self.elapsed_mean,
        }


def _package_version() -> str:
    try:
        return version("eight-puzzle-search")
    except PackageNotFoundError:
        return "0.1.0"


def benchmark_metadata(repeat: int) -> dict[str, str | int]:
    """Capture reproducibility metadata without identifying the local user."""
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor() or "unknown",
        "package_version": _package_version(),
        "repeat": repeat,
    }


def select_benchmark_cases(
    names: Sequence[str] | None = None,
) -> tuple[BenchmarkCase, ...]:
    """Select cases without changing their deterministic configured order."""
    if names is None:
        return BENCHMARK_CASES
    requested = set(names)
    known = {case.name for case in BENCHMARK_CASES}
    unknown = requested - known
    if unknown:
        raise ValueError(f"unknown benchmark case: {sorted(unknown)[0]}")
    return tuple(case for case in BENCHMARK_CASES if case.name in requested)


def select_benchmark_variants(
    algorithm: str | None = None,
    heuristic: str | None = None,
) -> tuple[BenchmarkVariant, ...]:
    """Select algorithm variants while preserving comparison-table order."""
    if algorithm is not None and algorithm not in BENCHMARK_ALGORITHMS:
        raise ValueError(f"unknown benchmark algorithm: {algorithm}")
    if heuristic is not None and heuristic not in BENCHMARK_HEURISTICS:
        raise ValueError(f"unknown A* heuristic: {heuristic}")
    if heuristic is not None and algorithm != "astar":
        raise ValueError("--heuristic requires --algorithm astar")

    variants = BENCHMARK_VARIANTS
    if algorithm is not None:
        variants = tuple(item for item in variants if item.algorithm == algorithm)
    if heuristic is not None:
        variants = tuple(item for item in variants if item.heuristic == heuristic)
    return variants


def _run_variant(puzzle: SlidingPuzzle, variant: BenchmarkVariant) -> SearchResult:
    if variant.algorithm == "bfs":
        return breadth_first_search(puzzle)
    if variant.algorithm == "dfs":
        return depth_first_search(puzzle)
    if variant.algorithm == "ids":
        return iterative_deepening_search(puzzle)
    if variant.algorithm == "ucs":
        return uniform_cost_search(puzzle)
    if variant.heuristic == "misplaced":
        return a_star_search(puzzle, misplaced_tiles)
    return a_star_search(puzzle, manhattan_distance)


def _validate_solution(
    case: BenchmarkCase,
    puzzle: SlidingPuzzle,
    variant: BenchmarkVariant,
    result: SearchResult,
) -> None:
    if result.status is not SearchStatus.SOLVED:
        raise BenchmarkError(
            f"{variant.display_name} did not solve benchmark case {case.name}"
        )
    if result.path[0] != case.start_state or result.path[-1] != case.goal_state:
        raise BenchmarkError(
            f"{variant.display_name} returned an invalid path endpoint"
        )
    if len(result.path) != len(result.actions) + 1:
        raise BenchmarkError(
            f"{variant.display_name} returned inconsistent path lengths"
        )
    for state, action, successor in zip(
        result.path[:-1], result.actions, result.path[1:], strict=True
    ):
        if puzzle.apply_action(state, action) != successor:
            raise BenchmarkError(
                f"{variant.display_name} returned an invalid action path"
            )
    if variant.expected_optimal and result.solution_depth != case.optimal_depth:
        raise BenchmarkError(
            f"{variant.display_name} returned depth {result.solution_depth} for "
            f"{case.name}; expected {case.optimal_depth}"
        )


def _deterministic_signature(result: SearchResult) -> tuple[object, ...]:
    return (
        result.status,
        result.path,
        result.actions,
        result.cost,
        result.solution_depth,
        result.nodes_generated,
        result.nodes_expanded,
        result.max_frontier_size,
    )


def _benchmark_one(
    case: BenchmarkCase,
    variant: BenchmarkVariant,
    repeat: int,
) -> BenchmarkRecord:
    puzzle = SlidingPuzzle(case.start_state, case.goal_state)
    baseline: SearchResult | None = None
    baseline_signature: tuple[object, ...] | None = None
    timings: list[float] = []

    for _ in range(repeat):
        result = _run_variant(puzzle, variant)
        _validate_solution(case, puzzle, variant, result)
        signature = _deterministic_signature(result)
        if baseline_signature is not None and signature != baseline_signature:
            raise BenchmarkError(
                f"{variant.display_name} produced nondeterministic metrics for {case.name}"
            )
        if baseline is None:
            baseline = result
            baseline_signature = signature
        timings.append(result.elapsed_seconds)

    if baseline is None or baseline.solution_depth is None or baseline.cost is None:
        raise BenchmarkError("benchmark did not produce a usable search result")

    timing_runs = tuple(timings)
    return BenchmarkRecord(
        case=case.name,
        algorithm=variant.algorithm,
        display_name=variant.display_name,
        heuristic=variant.heuristic,
        optimal_depth=case.optimal_depth,
        status=baseline.status.value,
        solution_depth=baseline.solution_depth,
        cost=baseline.cost,
        optimal=(baseline.solution_depth == case.optimal_depth)
        if variant.expected_optimal
        else None,
        nodes_generated=baseline.nodes_generated,
        nodes_expanded=baseline.nodes_expanded,
        max_frontier_size=baseline.max_frontier_size,
        timing_runs=timing_runs,
        elapsed_min=min(timing_runs),
        elapsed_median=median(timing_runs),
        elapsed_mean=fmean(timing_runs),
    )


def run_benchmarks(
    *,
    case_names: Sequence[str] | None = None,
    algorithm: str | None = None,
    heuristic: str | None = None,
    repeat: int = 1,
) -> tuple[BenchmarkRecord, ...]:
    """Execute the selected real searches and aggregate repeated timings."""
    if type(repeat) is not int or repeat < 1:
        raise ValueError("repeat must be a positive integer")
    cases = select_benchmark_cases(case_names)
    variants = select_benchmark_variants(algorithm, heuristic)
    return tuple(
        _benchmark_one(case, variant, repeat) for case in cases for variant in variants
    )


def benchmark_json(
    records: Sequence[BenchmarkRecord], metadata: dict[str, str | int]
) -> str:
    """Serialize benchmark metadata and records as JSON."""
    payload = {
        "metadata": metadata,
        "results": [record.to_dict() for record in records],
    }
    return json.dumps(payload, indent=2)


def benchmark_csv(
    records: Sequence[BenchmarkRecord], metadata: dict[str, str | int]
) -> str:
    """Serialize records as CSV with reproducibility metadata on every row."""
    metadata_fields = tuple(metadata)
    record_fields = (
        "case",
        "algorithm",
        "display_name",
        "heuristic",
        "optimal_depth",
        "status",
        "solution_depth",
        "cost",
        "optimal",
        "nodes_generated",
        "nodes_expanded",
        "max_frontier_size",
        "timing_runs",
        "elapsed_min",
        "elapsed_median",
        "elapsed_mean",
    )
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=metadata_fields + record_fields)
    writer.writeheader()
    for record in records:
        row = dict(metadata)
        row.update(record.to_dict())
        row["timing_runs"] = ";".join(f"{sample:.9f}" for sample in record.timing_runs)
        writer.writerow(row)
    return output.getvalue()


def benchmark_table(
    records: Sequence[BenchmarkRecord], metadata: dict[str, str | int]
) -> str:
    """Render a dependency-free human-readable comparison table."""
    headers = (
        "Case",
        "Algorithm",
        "Expected",
        "Depth",
        "Optimal?",
        "Expanded",
        "Generated",
        "Max Frontier",
        "Median Time",
    )
    rows = [
        (
            record.case,
            record.display_name,
            str(record.optimal_depth),
            str(record.solution_depth),
            "yes" if record.optimal else ("no" if record.optimal is False else "n/a"),
            str(record.nodes_expanded),
            str(record.nodes_generated),
            str(record.max_frontier_size),
            f"{record.elapsed_median:.6f} s",
        )
        for record in records
    ]
    widths = [
        max([len(headers[index]), *(len(row[index]) for row in rows)])
        for index in range(len(headers))
    ]

    def render(row: tuple[str, ...]) -> str:
        return "  ".join(value.ljust(widths[index]) for index, value in enumerate(row))

    separator = "  ".join("-" * width for width in widths)
    lines = [
        f"Python: {metadata['python_version']}",
        f"Platform: {metadata['platform']}",
        f"Repeat count: {metadata['repeat']}",
        "Max frontier is an algorithmic search-space metric, not process RAM.",
        "",
        render(headers),
        separator,
        *(render(row) for row in rows),
    ]
    return "\n".join(lines)


__all__ = [
    "BENCHMARK_ALGORITHMS",
    "BENCHMARK_CASES",
    "BENCHMARK_HEURISTICS",
    "BENCHMARK_VARIANTS",
    "BenchmarkCase",
    "BenchmarkError",
    "BenchmarkRecord",
    "BenchmarkVariant",
    "benchmark_csv",
    "benchmark_json",
    "benchmark_metadata",
    "benchmark_table",
    "run_benchmarks",
    "select_benchmark_cases",
    "select_benchmark_variants",
]
