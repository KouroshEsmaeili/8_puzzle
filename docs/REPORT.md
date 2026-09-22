# Search Algorithms for the Sliding Puzzle — Technical Report

## 1. Purpose

This project studies classical state-space search through the sliding-puzzle problem. The implementation focuses on correctness, deterministic behavior, measurable search effort, and reproducibility rather than on a graphical interface.

The current codebase supports general square sliding puzzles, while the benchmark and exhaustive validation concentrate on the standard 3×3 8-puzzle. Six public search strategies are implemented: BFS, DFS, DLS, IDS, UCS, and A*. A* supports Misplaced Tiles and Manhattan Distance heuristics.

This repository is a refactored and extended fork of an earlier `8_puzzle` project. The original Git history remains intact; the refactor introduces a package structure, a formal puzzle model, corrected search implementations, tests, a CLI, and deterministic benchmarks.

## 2. Problem model

A puzzle state is represented as an immutable tuple of integers. Tile `0` denotes the blank. For an `n × n` board, a valid state must contain each integer from `0` through `n² - 1` exactly once.

The `SlidingPuzzle` model stores a start state and a goal state and validates that both describe boards of the same square dimension. Using immutable tuples makes states directly hashable, which is important for discovered sets and best-cost maps used by graph-search algorithms.

Legal blank moves are generated in a fixed order:

1. `UP`
2. `DOWN`
3. `LEFT`
4. `RIGHT`

This deterministic successor order makes repeated runs reproducible when algorithmic tie-breaking is otherwise equal.

### 2.1 Goal-relative solvability

The solvability test is defined relative to the configured goal rather than hard-coded to one conventional goal arrangement.

For odd-width boards, reachability is determined by the inversion parity of the numbered tiles after ranking them according to their order in the goal state.

For even-width boards, the invariant combines inversion parity with the parity of the blank row. The implementation compares this invariant to the configured goal's blank-row parity.

This formulation supports both 3×3 and 4×4 examples and remains valid when the goal arrangement is nonstandard.

## 3. Search result contract

Every public search function returns a `SearchResult` containing:

- algorithm name
- status: `solved`, `failure`, or `cutoff`
- complete solution path
- action sequence
- path cost
- solution depth
- generated-node count
- expanded-node count
- maximum frontier size
- elapsed search time

The result object validates its own internal consistency, for example rejecting negative metrics or a solved result without a cost and solution depth.

### 3.1 Metric definitions

The metrics use explicit conventions so results are comparable across algorithms.

**Nodes generated.** The root counts as generated when a real search iteration creates a frontier. Every successor candidate is counted before duplicate or cycle filtering.

**Nodes expanded.** A node counts as expanded only when its successors are generated. A goal recognized before successor generation is not counted as expanded.

**Maximum frontier size.** For BFS and DFS this is the largest queue or stack size. For UCS and A*, it is the number of logically active best-cost states, excluding lazy stale heap entries. For DLS and IDS it is the largest active depth-first path length.

**IDS aggregation.** Generated and expanded counts accumulate repeated work from all fresh depth-limited iterations. Its maximum frontier is the maximum over iterations, not a sum.

**Timing.** Search time uses `time.perf_counter`. It includes the solvability precheck and excludes result presentation. An unsolvable instance rejected by the precheck creates no frontier and therefore reports zero generated, expanded, and frontier metrics.

These conventions make `max_frontier_size` a search-space measurement; it should not be interpreted as process memory consumption.

## 4. Algorithms

### 4.1 Breadth-First Search

BFS uses a FIFO queue and marks a state discovered when it is enqueued. This prevents duplicate frontier entries and repeated expansion. With unit move cost, BFS is complete and returns a minimum-depth solution.

In the finite 8-puzzle graph, graph-search cost is bounded by the reachable state graph. In the conventional branching-factor/depth analysis, BFS requires exponential time and space in solution depth, commonly written `O(b^d)`.

### 4.2 Depth-First Search

DFS uses a LIFO stack with a global discovered set. Successors are pushed in reverse deterministic order so the intended `UP`, `DOWN`, `LEFT`, `RIGHT` ordering is preserved when nodes are popped.

Because the reachable sliding-puzzle graph is finite and duplicates are suppressed, this DFS implementation terminates and is complete for this state space. It is not optimal: the first discovered solution may be extremely deep even when a short solution exists.

DFS can use less frontier storage than BFS in many tree-search settings, but graph duplicate detection still requires storing discovered states.

### 4.3 Depth-Limited Search

DLS performs recursive depth-first search with a caller-provided depth limit. It uses path-based cycle detection rather than a global discovered set, allowing a state to be revisited through a different path when required by depth-limited semantics.

DLS distinguishes three outcomes:

- `solved` — a goal was found within the limit
- `cutoff` — search reached the depth boundary while deeper paths may exist
- `failure` — the searched component was exhausted without a goal or remaining cutoff

DLS is useful directly when a meaningful depth bound is known and serves as the inner search used by IDS.

### 4.4 Iterative Deepening Search

IDS repeatedly executes a fresh DLS iteration with limits `0, 1, 2, ...` until a solution is found or a genuine failure is established.

With unit costs, IDS combines the optimal-depth behavior of BFS with depth-first frontier growth. Its tradeoff is repeated work near the top of the search tree, which is intentionally reflected in the cumulative generated and expanded metrics.

### 4.5 Uniform-Cost Search

UCS prioritizes states by path cost `g(n)` using a heap. A `best_g` map stores the cheapest known cost to each state. When a lower-cost path is found, the state is reinserted; lazy stale heap entries are ignored when popped.

Tie-breaking uses insertion order to keep execution deterministic.

All moves in this project currently cost one, so UCS returns the same optimal path cost as BFS. The algorithms differ conceptually because UCS also generalizes to nonuniform nonnegative edge costs.

### 4.6 A* Search

A* prioritizes nodes by

`f(n) = g(n) + h(n)`

where `g(n)` is the path cost and `h(n)` is a heuristic estimate to the goal.

The implementation:

- tracks the best known `g` value per state
- reopens a state when a cheaper path is discovered
- ignores stale heap entries
- breaks priority ties by lower `h(n)`, then insertion order
- rejects negative or noninteger heuristic results

With an admissible heuristic, A* returns an optimal solution in this setting.

## 5. Heuristics

### 5.1 Misplaced Tiles

Misplaced Tiles counts numbered tiles that are not at their configured goal positions. The blank is excluded.

This heuristic is simple and admissible because each misplaced numbered tile must be moved at least once before reaching the goal.

### 5.2 Manhattan Distance

Manhattan Distance sums, for every numbered tile, the horizontal and vertical grid distance between its current position and its configured goal position. The blank is excluded.

For the standard sliding puzzle this is also admissible because one legal move changes the position of only one numbered tile by one grid step.

Manhattan Distance is generally more informative than Misplaced Tiles because it accounts for how far tiles are from their destinations rather than only whether they are misplaced.

Both built-in heuristics derive target positions from the configured goal, so they also support nonstandard goal arrangements.

## 6. Correctness and exhaustive validation

The automated suite contains 168 tests covering state validation, transitions, solvability, search behavior, metrics, heuristics, CLI parsing/output, and benchmark consistency.

In addition to the unit and regression suite, the complete 3×3 state space was exhaustively checked against the final implementation.

Starting from the canonical goal `(1, 2, 3, 4, 5, 6, 7, 8, 0)`:

- reachable states: **181,440**
- maximum optimal distance from the goal: **31**
- total permutations checked: **362,880**
- permutations classified solvable: **181,440**
- permutations classified unsolvable: **181,440**
- solvability/reachability mismatches: **0**

For every reachable state, the exact shortest-path distance was known from exhaustive BFS. The built-in heuristics were then checked against those distances and across all legal transitions:

- Misplaced Tiles admissibility violations: **0**
- Manhattan Distance admissibility violations: **0**
- Misplaced Tiles consistency violations: **0**
- Manhattan Distance consistency violations: **0**
- states where Manhattan Distance was smaller than Misplaced Tiles: **0**

These checks provide stronger evidence than a small collection of hand-selected examples, while still keeping the normal automated suite fast enough for routine development and CI.

## 7. Benchmark methodology

The benchmark module defines five deterministic 3×3 instances with independently verified optimal depths:

| Case | Optimal depth |
| --- | ---: |
| `easy` | 2 |
| `medium` | 8 |
| `medium-plus` | 12 |
| `hard` | 16 |
| `harder` | 20 |

The comparison includes:

- BFS
- DFS
- IDS
- UCS
- A* with Misplaced Tiles
- A* with Manhattan Distance

DLS is omitted from the default comparison because its behavior depends on an externally chosen depth limit. It remains available through the solver CLI and as the primitive used by IDS.

Each benchmark validates returned paths and checks that algorithms expected to be optimal match the known optimal depth. Repeated timing runs report minimum, median, and mean elapsed time. JSON and CSV exports include reproducibility metadata such as Python version, platform, package version, UTC timestamp, and repeat count without recording the local username or project path.

## 8. Benchmark results

Search-work metrics are deterministic for the fixed cases and successor/tie-breaking rules. The following table reports nodes expanded for one complete comparison run:

| Case | BFS | DFS | IDS | UCS | A* Misplaced | A* Manhattan |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| depth 2 | 6 | 84,896 | 4 | 6 | 2 | 2 |
| depth 8 | 310 | 131,501 | 453 | 310 | 18 | 12 |
| depth 12 | 1,631 | 83,853 | 3,037 | 1,631 | 63 | 21 |
| depth 16 | 11,639 | 76,915 | 30,944 | 11,639 | 499 | 152 |
| depth 20 | 46,310 | 164,613 | 214,375 | 46,310 | 3,318 | 352 |

The depth-20 instance illustrates the difference between the two A* heuristics especially clearly:

| Algorithm | Expanded | Generated | Max frontier |
| --- | ---: | ---: | ---: |
| BFS | 46,310 | 124,941 | 17,259 |
| IDS | 214,375 | 586,298 | 21 |
| UCS | 46,310 | 124,941 | 17,259 |
| A* — Misplaced | 3,318 | 8,988 | 1,946 |
| A* — Manhattan | 352 | 949 | 220 |

Manhattan Distance expanded roughly one ninth as many nodes as Misplaced Tiles on this case, while both preserved optimality. Relative to uninformed BFS/UCS, Manhattan-guided A* reduced expansions by more than two orders of magnitude.

DFS demonstrates a different tradeoff. It does find a solution in the finite graph, but the returned solution can be extremely nonoptimal. On the nominal depth-2 case, deterministic DFS reaches a solution at depth 64,328. This is expected behavior for DFS and is why the benchmark marks its optimality field as not applicable rather than treating it as a shortest-path method.

IDS keeps its active depth-first path small but pays for repeated iterations. On the depth-20 case its maximum frontier is only 21 states, while its cumulative generated and expanded counts are much larger than BFS or A*.

### 8.1 Timing interpretation

Timing values are intentionally not treated as universal performance claims. They depend on Python version, operating system, processor, system load, and measurement noise. The benchmark records timing metadata and can repeat runs, but deterministic node counts are the more portable comparison for algorithmic behavior.

## 9. Reproducibility

Install the project with development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run the complete validation suite:

```bash
python -m pytest
ruff check .
ruff format --check src tests
```

Run all fixed benchmark cases:

```bash
python -m eight_puzzle benchmark --repeat 3
```

Export benchmark data:

```bash
python -m eight_puzzle benchmark --json --output benchmark.json
python -m eight_puzzle benchmark --csv --output benchmark.csv
```

Solve an individual puzzle:

```bash
python -m eight_puzzle solve \
  --algorithm astar \
  --heuristic manhattan \
  --start "1 2 3 4 5 6 0 7 8"
```

## 10. Limitations and extensions

The state model supports square puzzles larger than 3×3, and the tests include simple 4×4 behavior. The included benchmark, however, is deliberately limited to 3×3 instances because uninformed search becomes expensive very quickly as the state space grows.

All moves currently have unit cost. The UCS implementation already has the appropriate best-cost structure for weighted search, but the puzzle model would need an explicit move-cost policy before weighted experiments would be meaningful.

The heuristic set is intentionally small. Natural extensions include linear conflict, pattern databases, weighted A*, bidirectional search, and memory-bounded heuristic methods. Such additions should preserve the existing metric contract and deterministic benchmark methodology so comparisons remain interpretable.

## 11. Attribution and repository history

The original Git history belongs to the upstream course-project authors and has not been rewritten. This refactor starts from upstream commit `fe9d310`, authored by GitHub user [`yazdanzv`](https://github.com/yazdanzv). The refactor is layered on top of that history as new commits rather than replacing or reauthoring the original work.

The upstream repository does not declare an explicit license, so this refactor does not add one independently.
