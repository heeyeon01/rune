"""Rebuild the recall sweep .md report from its raw CSV.

Why this exists: the recall run (2026-05-26) generated its .md at run time
(stdout: "Report saved → …recall_2026-05-26.md") but that file was lost before
being committed — only the raw csv/log were committed. The raw CSV holds every
per-run sample, so we can regenerate the exact same report by feeding those
samples back through the *original* generator (`LatencyBenchReport.to_markdown_sweep`).

Reusing the real generator (instead of hand-rolling a percentile table) keeps the
percentile math (np.percentile, linear interpolation) and formatting byte-identical
to the sibling capture/searchable reports.

env block: most fields are recovered directly from the recall stdout/stderr logs.
Four fields come from the shared benchmark config (vault_endpoint, embedding_model,
embedding_mode, network_rtt) and are not echoed in the recall logs — they are taken
from the sibling reports, which ran against the same config. These are marked
INFERRED below.
"""
from __future__ import annotations

import csv
from collections import OrderedDict
from pathlib import Path

from common import LatencyBenchReport, LatencyScenarioResult, PhaseLatency

RAW = Path(__file__).resolve().parent.parent / "reports" / "raw" / \
    "latency_sweep_v143_mm32ivf_recall_2026-05-26.csv"
OUT = Path(__file__).resolve().parent.parent / "reports" / \
    "latency_sweep_v143_mm32ivf_recall_2026-05-26.md"

PRIMER_ROWS = [100, 1000, 10000, 20000, 25000, 32000, 50000, 100000]
# Phase column order, matching the order phases are emitted within a run.
PHASE_ORDER = ["embed", "score", "vault_topk", "remind", "total"]
# N=100000 errored at prime time for every scenario in the group (stdout:
# "prime ABORTED … skipping all 2 scenario(s)"). Record those as error results
# so the row renders ERROR, exactly like the sibling reports' top N.
ERRORED_N = {100000}
PRIME_ABORT = (
    "prime_insert failed: ValueError('Index is not insertable for 4096 "
    "vectors, 0 available')"
)


def main() -> None:
    # (N, scenario) -> {phase -> [samples]}, preserving first-seen order.
    samples: "OrderedDict[tuple[int, str], OrderedDict[str, list[float]]]" = OrderedDict()
    with RAW.open() as f:
        for row in csv.DictReader(f):
            N = int(row["N"])
            sid = row["scenario"]
            phase = row["phase"]
            key = (N, sid)
            samples.setdefault(key, OrderedDict())
            samples[key].setdefault(phase, []).append(float(row["latency_ms"]))

    # Scenario order as first seen in the CSV (T5_exact_match, T6_cross_lang).
    scenario_ids: list[str] = []
    for (_, sid) in samples:
        if sid not in scenario_ids:
            scenario_ids.append(sid)

    report = LatencyBenchReport()
    report.env = {
        "sdk_version": "1.4.3",
        "date": "2026-05-26",
        "envector_endpoint": "runebench-0520-2-scfomauvy6cn.clusters.envector.ai",
        "vault_endpoint": "tcp://161.118.149.143:50051",   # INFERRED (shared config)
        "embedding_model": "Qwen/Qwen3-Embedding-0.6B",     # INFERRED (shared config)
        "embedding_mode": "sbert",                          # INFERRED (shared config)
        "key_id": "vault-key",
        "eval_mode": "mm32",
        "index_type": "ivf_vct",
        "insert_mode": "single",
        "network_rtt": "unknown",                           # INFERRED (shared config)
        "runs_per_scenario": 12,
        "warmup_runs": 3,
        "direct_envector": True,
        "sweep_mode": True,
        "sweep_grid_N": ",".join(str(n) for n in PRIMER_ROWS),
        "sweep_scenarios": "recall",
        "bench_index_prefix": "runebench",
        "reset_policy": (
            "mutating groups: per-scenario drop+create+prime; "
            "read-only recall: one drop+create+prime per (N, group), "
            "all T5/T6/T7 scenarios share that primed index"
        ),
    }

    # Emit in (scenario outer is not required; to_markdown_sweep groups by sid,
    # iterating results in add() order). Match run order: for each N, each sid.
    for N in PRIMER_ROWS:
        for sid in scenario_ids:
            if N in ERRORED_N:
                res = LatencyScenarioResult(
                    scenario_id=sid, feature="recall",
                    metadata={"sweep_n": N}, error=PRIME_ABORT,
                )
                report.add(res)
                continue
            key = (N, sid)
            if key not in samples:
                continue
            phases = []
            for name in PHASE_ORDER:
                if name in samples[key]:
                    phases.append(PhaseLatency(name=name, samples_ms=samples[key][name]))
            report.add(LatencyScenarioResult(
                scenario_id=sid, feature="recall",
                phases=phases, metadata={"sweep_n": N},
            ))

    OUT.write_text(report.to_markdown_sweep(PRIMER_ROWS), encoding="utf-8")
    print(f"Report saved → {OUT}")


if __name__ == "__main__":
    main()
