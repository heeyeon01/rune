# Latency Sweep Benchmark — v1.2.2 (rmp/flat) vs v1.4.3 (mm32/ivf_vct)

> **Supersedes** `latency_bench_plan_envector_v1.2.2.md`,
> `latency_bench_plan_envector_v1.2.2_extended.md`, and
> `latency_bench_plan_envector_v1.4.3.md`. Those describe the older
> per-version runners (`latency_bench_v1.4.3.py`, since removed). The current
> work uses one adapter-driven runner — `benchmark/runners/latency_bench.py`
> — with an index-size sweep mode.

## Goal

Does v1.4.3's `mm32 + ivf_vct` have a real latency advantage over v1.2.2's
`rmp + flat`, in the regime where ivf_vct's centroid pruning is active?

envector `ivf_vct` adds a virtual centroid every ~4096 rows, and a query
probes `default_nprobe` of them — so query cost ≈ `nprobe × 4096` vectors,
roughly constant once the index holds more than `nprobe` centroids. Below
that the query still scans every centroid, i.e. behaves like a flat scan.
With `default_nprobe = 6` (see Index config), the ivf advantage appears only
above the **crossover N ≈ nprobe × 4096 ≈ 24,576**.

> ivf_vct is **not yet in production** — the live `runecontext` index runs
> v1.2.2 `rmp/flat`. This benchmark is a pre-adoption evaluation; the v1.4.3
> index parameters below are evaluation choices, not a mirror of a live index.

## Index config — v1.4.3 bench index

The `--direct-envector` bench index is created (`SdkAdapter.create_index` →
`V143Adapter.index_params`, in `benchmark/runners/sdk/v143.py`) with:

| param | value | note |
|---|---|---|
| index_type | `IVF_VCT` | |
| dim | 1024 | `BENCH_DIM` |
| nlist | **8192** | centroid-capacity headroom. **UNVERIFIED** — only `nlist=256` is known-good (the v1.4.3-native runner). The Step 2 probe must confirm it before any long run; fall back to 256 if it fails. |
| default_nprobe | **6** | centroids probed per query → crossover N ≈ 6 × 4096 ≈ 24,576 |
| eval_mode | `mm32` | |
| query encryption | `plain` | metadata encryption off |

`nlist` / `default_nprobe` are **fixed for the whole sweep** — only N varies.

## Unified runner

`benchmark/runners/latency_bench.py` is SDK-agnostic. `get_sdk_adapter()`
detects the installed `pyenvector.__version__` → V122Adapter (1.2.x) or
V143Adapter (1.4.x). Sweep mode (`--primer-rows N1,N2,...`) measures the
selected scenarios across a grid of index sizes N; see the runner's
`run_sweep` docstring. Raw samples stream to a long-format CSV
(`N,scenario,run_idx,phase,latency_ms`).

## Methodology — shared grid

| | v1.2.2 / flat | v1.4.3 / ivf_vct |
|---|---|---|
| Scaling | O(N), no regime change | ≈ flat scan below the crossover, then ≈ constant |
| Grid strategy | measure the full grid (no extrapolation) | measure the full grid, dense around the crossover |

flat is provably linear — a brute scan. ivf changes regime at the crossover
(~24,576), so it must be measured with points bracketing it. Both versions
sweep the **same grid** so the comparison can overlay them at identical N
points without trusting any extrapolation. The grid is dense around the
crossover (20,000 / 25,000 / 32,000) where the ivf advantage emerges; the
high-N tail (50k, 100k) confirms the ivf-cost cap on one side and v1.2.2
flat linearity at scale on the other. ivf cost ≈ `nprobe × 4096` vectors
(≈ constant once the index has more than `nprobe` centroids), so the
crossover N — where ivf meets the flat line — sits near `nprobe × 4096` ≈
24,576, bracketed by the N=20,000 / 25,000 / 32,000 measurement points.

> The two SDKs run on different machines (the SDK versions cannot coexist).
> The dominant N-dependent phase (`score`) is cluster-side, so client-machine
> differences mostly affect the smaller phases — note this in the report.

## Phase 3 — v1.2.2 sweep   `[machine: pyenvector 1.2.2]`

**Status: planned** — re-launching from
`benchmark/envector-latency-comparison-1.2.2`. The earlier 2026-05-16 launch
aborted at N=4096 (ES2 keyserver `connection refused`); the [0..8192]-only
grid and combined-scenario methodology have since been superseded by the
Phase 4 update. This re-launch matches Phase 4 — same grid, same per-group
split, same per-scenario isolation, same `--runs 15 --warmup 3`, same
multi_capture / duplicate exclusions — so v1.2.2 and v1.4.3 measure at
identical N points under identical conditions.

Same per-group split as Phase 4 — three separate invocations, all on the
same grid:

```
GRID=100,1000,10000,20000,25000,32000,50000,100000
for grp in recall capture searchable; do
  .venv/bin/python benchmark/runners/latency_bench.py --direct-envector \
      --primer-rows $GRID --sweep-scenarios $grp --runs 15 --warmup 3 \
      --report  benchmark/reports/latency_sweep_v122_rmpflat_${grp}_<date>.md \
      --raw-csv benchmark/reports/raw/latency_sweep_v122_rmpflat_${grp}_<date>.csv
done
```

Strictly sequential. Same `remaining_insertable_vectors` ceiling +
per-scenario isolation reasoning as Phase 4 Step 3 — mutating groups
(`capture`, `searchable`) reset+prime *before each scenario* so T1/T2/T3
(and T10/T11/T12) start from a matching fresh N-row index; recall (T5/T6)
reuses one primed index (non-mutating, no isolation gain from reset).

**Cost — v1.2.2 is much slower per-N than v1.4.3, so this is a multi-day
run, not overnight.**

  * **score is O(N), ~11 ms/record.** At N=100,000 one recall call ≈ 18 min;
    12 runs/N ≈ 3.7 h. Total recall sweep across the grid ≈ 9 h. `capture`
    carries the same score cost per scenario, × 3 scenarios → ~27 h.
    `searchable` likewise ~27 h.
  * **insert is single-row (~125 ms/row).** One prime cycle through the
    grid ≈ 9 h. Recall keeps the single-prime model (~9 h); mutating groups
    reset+prime per scenario — `capture` and `searchable` each pay 3 prime
    cycles → ~27 h priming per group.
  * **Total Phase 3 ≈ 6–7 days** end-to-end for the three groups (score +
    priming). Stage them across days; do not run concurrently against the
    same cluster.
  * The 2026-05-16 ES2 `connection refused` was transient; if it recurs,
    abort and retry — do not silently skip N points.

## Phase 4 — v1.4.3 sweep + comparison   `[machine: pyenvector 1.4.3]`

Prerequisites: pyenvector 1.4.3 installed; the v1.4.3 cluster endpoint set in
`~/.rune/config.json`; the `rune/.venv` (Python 3.12).

### Step 1 — V143Adapter   (implemented)

`benchmark/runners/sdk/v143.py` implements `connect` / `insert` /
`measure_insert_to_searchable`. `SdkAdapter.create_index` passes the full
`index_params` dict per adapter — an earlier refactor had dropped `nlist` /
`default_nprobe`, which created a malformed IVF index that crashed the
cluster on the first insert (`get index info ... INTERNAL`); that is fixed.

Verify the adapter loads:

```
.venv/bin/python -c "import sys; sys.path.insert(0,'benchmark'); from runners.sdk import get_sdk_adapter; print(get_sdk_adapter().sdk_version)"
```

### Step 2 — create_index probe + smoke test

`nlist=8192` is unverified (only `nlist=256` is known-good). Before any long
run, confirm the configured `index_params` create cleanly and survive inserts:

```
.venv/bin/python benchmark/runners/create_index_probe.py \
    > benchmark/reports/raw/create_probe_verify.log 2>&1
```

Exit 0 = create + load + inserts survived the configured `index_params`. If
it fails, fall back to `nlist=256` in `v143.py` before continuing. Then run
the sweep-loop smoke test:

```
.venv/bin/python benchmark/runners/latency_bench.py --direct-envector \
    --primer-rows 100,1000,10000 --runs 5 --warmup 1 --raw-csv /tmp/smoke_v143.csv
```

Confirms the sweep loop completes with no errors before the long run.

### Step 3 — full sweep — one invocation per scenario group

**Run each scenario group as its own sweep** — three separate invocations
(`recall`, `capture`, `searchable`), all on the same N grid. Do NOT combine
them into one `--sweep-scenarios` list.

Why separate (decided 2026-05-22, after the Step 2 smoke):

  * **`remaining_insertable_vectors` ceiling.** `capture` / `searchable`
    insert rows while measuring. pyenvector's `Index.insert`
    (`index/index.py:1152`) refuses an insert once the index's
    `remaining_insertable_vectors` reaches 0 — `ValueError: Index is not
    insertable for 1 vectors, 0 available`. In the Step 2 smoke this fired at
    N=10000 after ~33 cumulative inserts. Running the mutating groups together
    makes them share that headroom and starves the later ones; one group per
    sweep gives each the full per-N headroom.
  * **Within-N drift.** A combined sweep primes once per N then runs the
    groups in sequence, so later groups measure a grown index. Separate sweeps
    remove cross-group drift — each group sees exactly the primed N plus only
    its own measured inserts.

Two scenario groups are excluded outright:

  * `multi_capture` — see `latency_bench_plan_envector_v1.4.3.md` (the v1.4.3
    cluster crashes on its batch-insert path).
  * `duplicate` — near-redundant with `capture`: both repeatedly capture the
    same text, and `capture`'s warmup runs already seed copies, so `capture`'s
    measured runs already exercise the near-duplicate `score` path. `duplicate`
    also drifts (each run inserts another copy of the text), so its repeats are
    not a clean fixed-condition sample. Dropped 2026-05-22.

All three use the identical grid and run settings (`--runs 15 --warmup 3`,
i.e. 12 effective runs/N — same for every group):

```
GRID=100,1000,10000,20000,25000,32000,50000,100000
for grp in recall capture searchable; do
  .venv/bin/python benchmark/runners/latency_bench.py --direct-envector \
      --primer-rows $GRID --sweep-scenarios $grp --runs 15 --warmup 3 \
      --report  benchmark/reports/latency_sweep_v143_mm32ivf_${grp}_<date>.md \
      --raw-csv benchmark/reports/raw/latency_sweep_v143_mm32ivf_${grp}_<date>.csv
done
```

Strictly sequential — all three hit the same cluster, never concurrently.
`recall` is the primary deliverable (the `score`-vs-N crossover curve) and the
only group with no measured inserts, so it alone yields clean data across the
whole grid. `capture` / `searchable` insert 15 rows/scenario at `--runs 15`
(45 inserts/N for the 3-scenario `capture` group), so they ERROR with
`0 available` at the higher N (≥ ~10k); those ERROR rows are recorded and mark
where the ceiling sits.

Grid = realistic org-memory corpus sizes, dense around the crossover.
Centroids ≈ ⌈N/4096⌉; with nprobe=6 the crossover (~24,576) is bracketed by
N=20,000 and N=25,000:

| N | centroids | nprobe=6 probes | regime |
|---|---|---|---|
| 100 | 1 | 1 | flat |
| 1,000 | 1 | 1 | flat |
| 10,000 | 3 | 3 (all) | ≈ flat (pre-crossover) |
| 20,000 | 5 | 5 (all) | ≈ flat (just below crossover) |
| 25,000 | 7 | 6 / 7 | pruning begins (just past crossover) |
| 32,000 | 8 | 6 / 8 | ivf pruning active |
| 50,000 | 13 | 6 / 13 | ivf pruning active |
| 100,000 | 25 | 6 / 25 | ivf pruning active |

12 effective runs/N. Priming inserts N records in batches of 4096
(`PRIMER_BATCH_ROWS`, `await_completion=True, load=True`), so N=100,000 is
~25 sequential batches and each sweep's priming phase alone is ~2–3 h — with
four separate sweeps, expect a long, ideally overnight, run.

> **Caveat** — verify the ivf centroid merge has completed after priming each
> N, before measuring. `_prime_bench_index` waits only for `score` readiness,
> which may not imply merge-complete; measuring an un-merged ivf index would
> understate its optimization. Record the pyenvector build and SDK bug state
> in the report env (see the v143.py `measure_insert_to_searchable`
> docstring).

### Step 4 — comparison report

Merge the two raw CSVs. Per scenario, overlay v1.2.2-flat (measured) and
v1.4.3-ivf (measured) latency-vs-N curves on the shared grid. Report the
crossover N (bracketed by the 20k / 25k / 32k points), the winner in each
region, and the speed-up factor. State which config each SDK measured and
the two-machine caveat in the environment section. (`searchable` is
measured by different mechanisms per SDK — see v143.py — so compare only
total insert→searchable time there.)

## Parallel execution

Phase 3 (this machine, v1.2.2) and Phase 4 (other machine, v1.4.3) are
independent — they run concurrently, and the comparison (Step 4) merges their
CSVs afterward.
