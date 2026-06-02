"""Assemble the consolidated v1.4.3 latency report.

Takes a hand-written body (title / environment / framing / summary tables /
interpretation) and appends a machine-generated appendix: the full per-phase
distribution (n / p50 / p95 / p99 / mean / min / max) for every (scenario, N)
across all three raw CSVs (capture, recall, searchable).

The appendix stats go through the *original* PhaseLatency, so the percentile
math (np.percentile, linear interpolation) is identical to the summary tables
that the benchmark runner produced — the appendix and the summary never
disagree about how a number was computed.

Errored grid points have no rows in the CSV, so they simply do not appear in
the appendix; the summary tables (in the body) carry the ERROR markers that
record where each scenario hit the insert ceiling.
"""
from __future__ import annotations

import csv
from collections import OrderedDict
from pathlib import Path

from common import PhaseLatency

REPORTS = Path(__file__).resolve().parent.parent / "reports"
RAW = REPORTS / "raw"

# (feature label, csv filename) in report order. recall → searchable → capture.
SOURCES = [
    ("recall", "latency_sweep_v143_mm32ivf_recall_2026-05-26.csv"),
    ("searchable", "latency_sweep_v143_mm32ivf_searchable_2026-05-28.csv"),
    ("capture", "latency_sweep_v143_mm32ivf_capture_2026-05-28.csv"),
]

BODY = REPORTS / "_consolidated_v143_body.md"          # hand-written input
OUT = REPORTS / "latency_sweep_v143_mm32ivf_consolidated_2026-06-02.md"


def load(csv_path: Path):
    """Return ordered {scenario: {N: {phase: PhaseLatency}}} from a long CSV."""
    data: "OrderedDict[str, OrderedDict[int, OrderedDict[str, PhaseLatency]]]" = OrderedDict()
    with csv_path.open() as f:
        for row in csv.DictReader(f):
            sid, N, phase = row["scenario"], int(row["N"]), row["phase"]
            data.setdefault(sid, OrderedDict())
            data[sid].setdefault(N, OrderedDict())
            data[sid][N].setdefault(phase, PhaseLatency(name=phase))
            data[sid][N][phase].samples_ms.append(float(row["latency_ms"]))
    return data


def appendix() -> str:
    lines: list[str] = []
    lines.append("\n---\n")
    lines.append("## 부록 A — 확장 분포 통계 (per scenario × N)\n")
    lines.append(
        "요약 표는 phase p50 + total p95만 보여준다. 아래는 측정된 모든 "
        "(scenario, N) 조합의 phase별 전체 분포다 — `n`은 유효 측정 회차 수, "
        "단위는 ms. ERROR였던 grid point는 측정값이 없으므로 표에 나타나지 "
        "않는다(요약 표의 ERROR 표식이 그 위치를 기록한다).\n"
    )
    for feature, fname in SOURCES:
        data = load(RAW / fname)
        lines.append(f"\n### {feature}\n")
        for sid, by_n in data.items():
            lines.append(f"#### {sid}\n")
            for N, phases in by_n.items():
                lines.append(f"**N = {N:,}**\n")
                lines.append("| phase | n | p50 | p95 | p99 | mean | min | max |")
                lines.append("|---|---|---|---|---|---|---|---|")
                for name, p in phases.items():
                    lines.append(
                        f"| {name} | {p.n} | {p.p50:.1f} | {p.p95:.1f} "
                        f"| {p.p99:.1f} | {p.mean:.1f} | {p.min_ms:.1f} "
                        f"| {p.max_ms:.1f} |"
                    )
                lines.append("")
    return "\n".join(lines)


def main() -> None:
    body = BODY.read_text(encoding="utf-8")
    OUT.write_text(body.rstrip() + "\n" + appendix(), encoding="utf-8")
    print(f"Consolidated report → {OUT}")


if __name__ == "__main__":
    main()
