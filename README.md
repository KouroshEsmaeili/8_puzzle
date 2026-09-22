# 8-Puzzle Search Algorithms

[![CI](https://github.com/KouroshEsmaeili/8_puzzle/actions/workflows/ci.yml/badge.svg)](https://github.com/KouroshEsmaeili/8_puzzle/actions/workflows/ci.yml)

A compact classical-AI search project for solving square sliding puzzles and comparing uninformed and heuristic search strategies.

This repository is a refactored and extended fork of the original `8_puzzle` project by **Yazdan ZandiyeVakili (`yazdanzv`)**. The original Git history is preserved; the current implementation replaces the earlier scripts with a tested package, command-line interface, reproducible benchmarks, and explicit search metrics.

## What it includes

- Immutable, validated sliding-puzzle states for square boards
- Goal-relative solvability checks for odd and even board widths
- Breadth-First Search (BFS)
- Depth-First Search (DFS)
- Depth-Limited Search (DLS)
- Iterative Deepening Search (IDS)
- Uniform-Cost Search (UCS)
- A* with Misplaced Tiles and Manhattan Distance heuristics
- Structured search results and deterministic tie-breaking
- CLI output in human-readable or JSON form
- Fixed benchmark cases with JSON/CSV export
- 168 automated tests covering puzzle rules, heuristics, algorithms, CLI behavior, and benchmark validation

## Search methods

| Method | Complete here? | Optimal here? | Main frontier |
| --- | --- | --- | --- |
| BFS | Yes | Yes | FIFO queue |
| DFS | Yes on the finite state graph | No | LIFO stack |
| DLS | Up to the chosen limit | No | Active depth-first path |
| IDS | Yes | Yes | Repeated depth-limited search |
| UCS | Yes | Yes | Best-cost heap |
| A* | Yes | Yes with an admissible heuristic | `g(n) + h(n)` heap |

All puzzle moves currently have unit cost. BFS, IDS, UCS, and A* with either built-in heuristic therefore return optimal solution depth on the benchmark set.

## Installation

Python 3.11 or newer is required.

```bash
python -m venv .venv
```

Activate the environment, then install the project and development tools:

```bash
python -m pip install -e ".[dev]"
```

## Solve a puzzle

```bash
python -m eight_puzzle solve \
  --algorithm astar \
  --heuristic manhattan \
  --start "1 2 3 4 5 6 0 7 8"
```

Example result:

```text
Algorithm: A*
Heuristic: Manhattan
Status: solved
Solution depth: 2
Path cost: 2
Actions:
RIGHT RIGHT
```

The default goal is:

```text
1 2 3
4 5 6
7 8 ·
```

A custom goal may be supplied with `--goal`. DLS requires `--depth-limit`. Add `--show-path` to display every state in the solution path or `--json` for machine-readable output.

## Run benchmarks

```bash
python -m eight_puzzle benchmark --repeat 3
```

The benchmark uses fixed 3×3 cases with verified optimal depths 2, 8, 12, 16, and 20. It compares BFS, DFS, IDS, UCS, A* with Misplaced Tiles, and A* with Manhattan Distance. DLS is intentionally excluded because its result depends on an externally selected depth limit.

For the depth-20 case, deterministic search-work metrics show the effect of heuristic quality:

| Algorithm | Expanded | Generated | Max frontier |
| --- | ---: | ---: | ---: |
| BFS | 46,310 | 124,941 | 17,259 |
| IDS | 214,375 | 586,298 | 21 |
| UCS | 46,310 | 124,941 | 17,259 |
| A* — Misplaced | 3,318 | 8,988 | 1,946 |
| A* — Manhattan | 352 | 949 | 220 |

Timing is reported by the CLI, but it is environment-dependent. `max_frontier_size` is an algorithmic search-space metric, not process RAM usage.

JSON and CSV output are also supported:

```bash
python -m eight_puzzle benchmark --json --output benchmark.json
python -m eight_puzzle benchmark --csv --output benchmark.csv
```

## Validation

The implementation is covered by 168 automated tests. Additional exhaustive validation over the full 3×3 state space confirmed:

- 181,440 states are reachable from the canonical goal
- the maximum optimal distance is 31 moves
- all 362,880 permutations split exactly into 181,440 solvable and 181,440 unsolvable states
- the solvability predicate matches reachability for every permutation
- Misplaced Tiles and Manhattan Distance have no admissibility or consistency violations over the reachable state space
- Manhattan Distance is never smaller than Misplaced Tiles on those states

Run the local checks with:

```bash
python -m pytest
ruff check .
ruff format --check src tests
```

## Project structure

```text
src/eight_puzzle/
├── puzzle.py       # state model, transitions, solvability
├── node.py         # lightweight parent-linked search node
├── result.py       # structured outcomes and metric definitions
├── heuristics.py   # Misplaced Tiles and Manhattan Distance
├── benchmark.py    # fixed cases and benchmark aggregation
├── cli.py          # command-line interface
└── search/
    ├── bfs.py
    ├── dfs.py
    ├── dls.py
    ├── ids.py
    ├── ucs.py
    └── astar.py

tests/              # automated regression suite
docs/REPORT.md      # design, correctness, metrics, and benchmark discussion
```

## Design notes

States are immutable tuples, actions are deterministic (`UP`, `DOWN`, `LEFT`, `RIGHT`), and the blank is represented by `0`. Built-in heuristics ignore the blank and are evaluated relative to the configured goal rather than assuming a single conventional target arrangement.

UCS and A* use lazy heap deletion while tracking the logically active best-cost states, so stale heap entries do not inflate the reported frontier metric. IDS reports cumulative generated/expanded work across all depth-limited iterations.

See [`docs/REPORT.md`](docs/REPORT.md) for the full methodology and analysis.

## Attribution

The original repository history and authorship are intentionally preserved. The earlier project was described as an AI-course 8-puzzle solver and already contained implementations named A*, DFS, IDS, BFS, and UCS. This refactor reorganizes and reimplements the project without rewriting that upstream history.

No license file is added because the upstream repository does not declare an explicit license.
