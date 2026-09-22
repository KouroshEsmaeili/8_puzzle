"""Command-line interface for solving and benchmarking sliding puzzles."""

from __future__ import annotations

import argparse
import json
from math import isqrt
from pathlib import Path
from typing import Sequence

from eight_puzzle.benchmark import (
    BENCHMARK_ALGORITHMS,
    BENCHMARK_CASES,
    BENCHMARK_HEURISTICS,
    BenchmarkError,
    benchmark_csv,
    benchmark_json,
    benchmark_metadata,
    benchmark_table,
    run_benchmarks,
)
from eight_puzzle.heuristics import manhattan_distance, misplaced_tiles
from eight_puzzle.puzzle import PuzzleState, SlidingPuzzle
from eight_puzzle.result import SearchResult, SearchStatus
from eight_puzzle.search import (
    a_star_search,
    breadth_first_search,
    depth_first_search,
    depth_limited_search,
    iterative_deepening_search,
    uniform_cost_search,
)

SOLVE_ALGORITHMS: tuple[str, ...] = ("bfs", "dfs", "dls", "ids", "ucs", "astar")
SOLVE_HEURISTICS: tuple[str, ...] = ("misplaced", "manhattan")

_ALGORITHM_LABELS = {
    "bfs": "BFS",
    "dfs": "DFS",
    "dls": "DLS",
    "ids": "IDS",
    "ucs": "UCS",
    "astar": "A*",
}


def parse_state(text: str) -> PuzzleState:
    """Parse whitespace- or comma-separated integer tiles."""
    pieces = text.replace(",", " ").split()
    if not pieces:
        raise ValueError("puzzle state must contain integers")
    try:
        return tuple(int(piece) for piece in pieces)
    except ValueError as exc:
        raise ValueError("puzzle state must contain integers only") from exc


def _default_goal(start_state: PuzzleState) -> PuzzleState:
    tile_count = len(start_state)
    size = isqrt(tile_count)
    if size * size != tile_count:
        raise ValueError("start state length must be a perfect square")
    return tuple(range(1, tile_count)) + (0,)


def _validate_solve_options(args: argparse.Namespace) -> tuple[str | None, int | None]:
    heuristic = args.heuristic
    depth_limit = args.depth_limit
    if args.algorithm == "dls":
        if depth_limit is None:
            raise ValueError("--depth-limit is required for DLS")
        if depth_limit < 0:
            raise ValueError("--depth-limit must be non-negative")
    elif depth_limit is not None:
        raise ValueError("--depth-limit may only be used with DLS")

    if args.algorithm == "astar":
        heuristic = heuristic or "manhattan"
    elif heuristic is not None:
        raise ValueError("--heuristic may only be used with A*")
    return heuristic, depth_limit


def _run_solve(
    puzzle: SlidingPuzzle,
    algorithm: str,
    heuristic: str | None,
    depth_limit: int | None,
) -> SearchResult:
    if algorithm == "bfs":
        return breadth_first_search(puzzle)
    if algorithm == "dfs":
        return depth_first_search(puzzle)
    if algorithm == "dls":
        if depth_limit is None:
            raise ValueError("DLS requires a depth limit")
        return depth_limited_search(puzzle, depth_limit)
    if algorithm == "ids":
        return iterative_deepening_search(puzzle)
    if algorithm == "ucs":
        return uniform_cost_search(puzzle)
    selected = misplaced_tiles if heuristic == "misplaced" else manhattan_distance
    return a_star_search(puzzle, selected)


def _solve_payload(
    result: SearchResult,
    heuristic: str | None,
    *,
    include_path: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "algorithm": result.algorithm,
        "heuristic": heuristic,
        "status": result.status.value,
        "solution_depth": result.solution_depth,
        "cost": result.cost,
        "nodes_generated": result.nodes_generated,
        "nodes_expanded": result.nodes_expanded,
        "max_frontier_size": result.max_frontier_size,
        "elapsed_seconds": result.elapsed_seconds,
        "actions": [action.value for action in result.actions],
    }
    if include_path:
        payload["path"] = [list(state) for state in result.path]
    return payload


def _format_solve_result(
    puzzle: SlidingPuzzle,
    result: SearchResult,
    heuristic: str | None,
    *,
    show_path: bool,
) -> str:
    lines = [f"Algorithm: {_ALGORITHM_LABELS[result.algorithm]}"]
    if heuristic is not None:
        lines.append(f"Heuristic: {heuristic.title()}")
    lines.extend(
        (
            f"Status: {result.status.value}",
            f"Solution depth: {result.solution_depth if result.solution_depth is not None else 'n/a'}",
            f"Path cost: {result.cost if result.cost is not None else 'n/a'}",
            f"Nodes generated: {result.nodes_generated}",
            f"Nodes expanded: {result.nodes_expanded}",
            f"Max frontier size: {result.max_frontier_size}",
            f"Elapsed: {result.elapsed_seconds:.6f} s",
            "",
            "Actions:",
            " ".join(action.value for action in result.actions) or "(none)",
        )
    )
    if show_path and result.path:
        lines.extend(("", "Path:"))
        for index, state in enumerate(result.path):
            label = "start" if index == 0 else result.actions[index - 1].value
            lines.extend((f"Step {index} ({label}):", puzzle.format_state(state)))
            if index != len(result.path) - 1:
                lines.append("")
    return "\n".join(lines)


def _handle_solve(args: argparse.Namespace) -> int:
    heuristic, depth_limit = _validate_solve_options(args)
    start_state = parse_state(args.start)
    goal_state = parse_state(args.goal) if args.goal else _default_goal(start_state)
    puzzle = SlidingPuzzle(start_state, goal_state)
    result = _run_solve(puzzle, args.algorithm, heuristic, depth_limit)

    if args.json_output:
        print(
            json.dumps(_solve_payload(result, heuristic, include_path=args.show_path))
        )
    else:
        print(_format_solve_result(puzzle, result, heuristic, show_path=args.show_path))
    return 0 if result.status is SearchStatus.SOLVED else 1


def _handle_benchmark(args: argparse.Namespace) -> int:
    if args.heuristic is not None and args.algorithm != "astar":
        raise ValueError("--heuristic requires --algorithm astar")
    if args.repeat < 1:
        raise ValueError("--repeat must be a positive integer")
    if args.output and not (args.json_output or args.csv_output):
        raise ValueError("--output requires --json or --csv")

    case_names = (args.case,) if args.case else None
    records = run_benchmarks(
        case_names=case_names,
        algorithm=args.algorithm,
        heuristic=args.heuristic,
        repeat=args.repeat,
    )
    metadata = benchmark_metadata(args.repeat)
    if args.json_output:
        output = benchmark_json(records, metadata)
    elif args.csv_output:
        output = benchmark_csv(records, metadata)
    else:
        output = benchmark_table(records, metadata)

    if args.output:
        destination = Path(args.output)
        destination.write_text(output, encoding="utf-8")
        print(f"Wrote {len(records)} benchmark records to {destination}")
    else:
        print(output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the complete command-line parser."""
    parser = argparse.ArgumentParser(
        prog="eight_puzzle",
        description="Solve square sliding puzzles and compare search algorithms.",
        epilog=(
            "Exit codes: 0 = solved/successful command, 1 = search failure, cutoff, "
            "or benchmark validation failure, 2 = invalid command-line input."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    solve_parser = subparsers.add_parser(
        "solve", help="solve one puzzle with a selected search algorithm"
    )
    solve_parser.add_argument("--algorithm", required=True, choices=SOLVE_ALGORITHMS)
    solve_parser.add_argument(
        "--start",
        required=True,
        help='tiles separated by spaces or commas, for example "1 2 3 4 5 6 0 7 8"',
    )
    solve_parser.add_argument(
        "--goal",
        help="optional goal state; defaults to 1..N²-1 followed by 0",
    )
    solve_parser.add_argument(
        "--depth-limit", type=int, help="required for DLS and invalid otherwise"
    )
    solve_parser.add_argument(
        "--heuristic",
        choices=SOLVE_HEURISTICS,
        help="A* heuristic (default: manhattan); invalid for other algorithms",
    )
    solve_parser.add_argument(
        "--show-path",
        action="store_true",
        help="include every board in the solution path",
    )
    solve_parser.add_argument(
        "--json", dest="json_output", action="store_true", help="emit JSON only"
    )
    solve_parser.set_defaults(handler=_handle_solve)

    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="run deterministic fixed-case comparisons using real search implementations",
        description=(
            "Run reproducible fixed puzzle cases. DLS is excluded because its result "
            "depends on an externally chosen depth limit and it primarily supports IDS."
        ),
    )
    benchmark_parser.add_argument(
        "--case", choices=tuple(case.name for case in BENCHMARK_CASES)
    )
    benchmark_parser.add_argument("--algorithm", choices=BENCHMARK_ALGORITHMS)
    benchmark_parser.add_argument(
        "--heuristic",
        choices=BENCHMARK_HEURISTICS,
        help="select one A* heuristic; requires --algorithm astar",
    )
    benchmark_parser.add_argument(
        "--repeat", type=int, default=1, help="runs per case/algorithm (default: 1)"
    )
    output_group = benchmark_parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--json", dest="json_output", action="store_true", help="emit JSON"
    )
    output_group.add_argument(
        "--csv", dest="csv_output", action="store_true", help="emit CSV"
    )
    benchmark_parser.add_argument(
        "--output", help="write JSON or CSV to this path instead of stdout"
    )
    benchmark_parser.set_defaults(handler=_handle_benchmark)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments, handle normal user errors, and return a process code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except BenchmarkError as exc:
        parser.exit(1, f"error: {exc}\n")
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 2


__all__ = [
    "SOLVE_ALGORITHMS",
    "SOLVE_HEURISTICS",
    "build_parser",
    "main",
    "parse_state",
]
