#!/usr/bin/env python3
"""Probe how `remaining_insertable_vectors_guaranteed` (and the per-shard
breakdown reachable via GetIndexInfo) responds to single-row inserts on a
v1.4.3 IVF_VCT index.

Background — `benchmark/runners/latency_bench.py` capture / searchable sweeps
hit `ValueError('Index is not insertable for 1 vectors, 0 available')` after
a small number of single inserts (the same pattern at every grid N). The
ceiling lives server-side in `_guaranteed`; the SDK only forwards the number
(see `pyenvector/api/grpc.py:1475-1476` and `index.py:1150-1152`). To
understand the formula behavior, we snapshot the server counters around each
insert and also reach into the proto response for the per-shard `is_raw`
flag, which the SDK dict wrapper drops.

Output — long-format CSV, one row per operation:

    op,t_ms,row_count,saved_row_count,_shards,_guaranteed,_best_effort,
    n_shards_total,n_shards_raw,n_shards_merged,error

Run only after the sweep finishes (same cluster) — the bench cluster gets
unstable under concurrent stress.

Usage
-----
    .venv/bin/python benchmark/runners/insertable_probe.py \\
        --prime-rows 100 --insert-count 30 --recover load \\
        --csv benchmark/reports/raw/insertable_probe_N100_<date>.csv

To trace the N-dependence run several invocations with different
--prime-rows; each uses a fresh index.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import os
import secrets
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import numpy as np

BENCHMARK_DIR = Path(__file__).resolve().parent.parent
RUNE_DIR = BENCHMARK_DIR.parent
MCP_DIR = RUNE_DIR / "mcp"

for _p in (str(RUNE_DIR), str(MCP_DIR), str(BENCHMARK_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from runners.sdk import get_sdk_adapter  # noqa: E402

PRIMER_BATCH_ROWS = 4096
BENCH_DIM = 1024
SNAPSHOT_COLUMNS = [
    "op",
    "t_ms",
    "row_count",
    "saved_row_count",
    "_shards",
    "_guaranteed",
    "_best_effort",
    "n_shards_total",
    "n_shards_raw",
    "n_shards_merged",
    "error",
]


@dataclass
class Snapshot:
    op: str
    t_ms: float = 0.0
    row_count: int = -1
    saved_row_count: int = -1
    shards: int = -1
    guaranteed: int = -1
    best_effort: int = -1
    n_shards_total: int = -1
    n_shards_raw: int = -1
    n_shards_merged: int = -1
    error: str = ""

    def as_row(self) -> dict[str, Any]:
        return {
            "op": self.op,
            "t_ms": f"{self.t_ms:.2f}",
            "row_count": self.row_count,
            "saved_row_count": self.saved_row_count,
            "_shards": self.shards,
            "_guaranteed": self.guaranteed,
            "_best_effort": self.best_effort,
            "n_shards_total": self.n_shards_total,
            "n_shards_raw": self.n_shards_raw,
            "n_shards_merged": self.n_shards_merged,
            "error": self.error,
        }


def snapshot(adapter, index_name: str, op: str, t_ms: float = 0.0, error: str = "") -> Snapshot:
    """Read aggregate counters and per-shard is_raw via GetIndexInfo proto stub.

    The SDK's `get_index_info` wrapper (`pyenvector/api/grpc.py:1383-1401`)
    drops `response.index_info.shards` — we re-issue the same RPC through the
    stub so we can read it. `get_index_summary` is enough for the aggregate
    counters, but we use a single GetIndexInfo call here to keep the snapshot
    server-roundtrip-consistent.
    """
    snap = Snapshot(op=op, t_ms=t_ms, error=error)
    try:
        import pyenvector as ev
        from pyenvector.proto_gen.v2.common import type_pb2 as envector_type_pb
        from pyenvector.proto_gen.v2.endpoint import endpoint_message_pb2 as envector_msg_pb2

        index = ev.Index(index_name)
        indexer = index.indexer

        request = envector_msg_pb2.GetIndexInfoRequest()
        request.header.type = envector_type_pb.MessageType.GetIndexInfo
        request.header.id = secrets.token_hex(10)
        request.index_name = index_name

        response_iter = indexer.stub.get_index_info(request, metadata=indexer.grpc_metadata)
        for stream_idx, response in enumerate(response_iter):
            if response.header.return_code != envector_type_pb.ReturnCode.Success:
                snap.error = (snap.error + "; " if snap.error else "") + f"return_code={response.header.return_code}"
                return snap
            if stream_idx == 0:
                info = response.index_info
                snap.row_count = info.row_count
                snap.saved_row_count = info.saved_row_count
                snap.shards = info.remaining_insertable_shards
                snap.guaranteed = info.remaining_insertable_vectors_guaranteed
                snap.best_effort = info.remaining_insertable_vectors_best_effort
                shards = list(info.shards)
                snap.n_shards_total = len(shards)
                snap.n_shards_raw = sum(1 for s in shards if s.is_raw)
                snap.n_shards_merged = snap.n_shards_total - snap.n_shards_raw
                break  # subsequent stream items carry only centroid chunks for IVF
    except Exception as e:
        snap.error = (snap.error + "; " if snap.error else "") + f"snapshot_failed: {type(e).__name__}: {e}"
    return snap


async def setup_adapter(index_name: str) -> Any:
    """Vault + adapter wiring lifted from latency_bench._setup_direct_envector.

    Trimmed: no embedding service, no production-runecontext interaction.
    Returns a connected V143Adapter.
    """
    from adapter.vault_client import VaultClient
    from agents.common.config import load_config

    cfg = load_config()
    vault = VaultClient(
        vault_endpoint=cfg.vault.endpoint,
        vault_token=cfg.vault.token,
        ca_cert=cfg.vault.ca_cert or None,
        tls_disable=cfg.vault.tls_disable,
    )
    bundle = await vault.get_public_key()

    key_id = bundle.pop("key_id", None)
    bundle.pop("index_name", None)
    agent_id = bundle.pop("agent_id", None)
    agent_dek_b64 = bundle.pop("agent_dek", None)
    ev_endpoint = bundle.pop("envector_endpoint", None) or cfg.envector.endpoint
    ev_api_key = bundle.pop("envector_api_key", None) or cfg.envector.api_key
    ev_secure = bundle.pop("envector_secure", None)

    if not key_id:
        raise RuntimeError("Vault did not return key_id")

    key_path = Path.home() / ".rune" / "keys"
    key_dir = key_path / key_id
    key_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    for filename, content in bundle.items():
        fp = key_dir / filename
        fd = os.open(str(fp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(content)

    agent_dek: Optional[bytes] = None
    if agent_dek_b64:
        import base64
        agent_dek = base64.b64decode(agent_dek_b64)

    adapter = get_sdk_adapter()
    if adapter.sdk_version != "1.4.3":
        raise RuntimeError(
            f"insertable_probe targets v1.4.3 (IVF_VCT); installed pyenvector={adapter.sdk_version}"
        )
    connect_kwargs = dict(
        address=ev_endpoint,
        key_id=key_id,
        key_path=str(key_path),
        access_token=ev_api_key,
        agent_id=agent_id,
        agent_dek=agent_dek,
    )
    if ev_secure is not None:
        connect_kwargs["secure"] = ev_secure
    adapter.connect(**connect_kwargs)

    return adapter, vault


def _reset_index(adapter, index_name: str) -> None:
    """Drop if exists, then create. Tolerates race with prior async drop."""
    existing = []
    try:
        existing = adapter.list_index_names()
    except Exception as e:
        print(f"  list_index_names failed (continuing): {e}", flush=True)
    if index_name in existing:
        try:
            adapter.drop_index(index_name)
        except Exception as e:
            print(f"  drop_index({index_name!r}) failed (continuing): {e}", flush=True)
    deadline = time.monotonic() + 60.0
    last_err: Optional[Exception] = None
    while time.monotonic() < deadline:
        try:
            adapter.create_index(index_name, BENCH_DIM)
            return
        except Exception as e:
            last_err = e
            time.sleep(2.0)
    raise RuntimeError(f"create_index({index_name!r}) failed after retries: {last_err}")


def _prime(adapter, index_name: str, n_rows: int, rng: np.random.Generator) -> float:
    """Batch-insert n_rows in PRIMER_BATCH_ROWS chunks with await+load.

    Mirrors V143Adapter.prime_insert semantics (already does await=True, load=True
    per batch). Returns wall-clock seconds elapsed.
    """
    start = time.monotonic()
    for batch_start in range(0, n_rows, PRIMER_BATCH_ROWS):
        batch_end = min(batch_start + PRIMER_BATCH_ROWS, n_rows)
        vectors = [
            rng.standard_normal(BENCH_DIM).astype(np.float32).tolist()
            for _ in range(batch_end - batch_start)
        ]
        metadata = [{"text": f"prime-{i}", "scope": "probe"} for i in range(batch_start, batch_end)]
        adapter.prime_insert(index_name, vectors, metadata)
    return time.monotonic() - start


def _single_insert(adapter, index_name: str, vec: list, *, await_completion: bool, load: bool) -> tuple[float, str]:
    """Single-row insert via the row-insert path. Returns (t_ms, error_str).

    error_str is "" on success. Catches ValueError ("0 available") and the
    generic SDK RuntimeError so the probe can log the snapshot at failure
    instead of crashing.
    """
    metadata = [{"text": "probe", "scope": "probe"}]
    t0 = time.perf_counter()
    try:
        adapter.insert(
            index_name,
            [vec],
            metadata,
            row_insert=True,
            await_completion=await_completion,
            load=load,
        )
    except Exception as e:
        t_ms = (time.perf_counter() - t0) * 1000.0
        return t_ms, f"{type(e).__name__}: {e}"
    t_ms = (time.perf_counter() - t0) * 1000.0
    return t_ms, ""


def _force_load(adapter, index_name: str) -> float:
    """Call Index.load() — forces server to publish merged shards. Probes
    whether `_guaranteed` and `n_shards_raw` recover after a stand-alone load.
    """
    import pyenvector as ev
    t0 = time.perf_counter()
    adapter.sdk._with_reconnect(lambda: ev.Index(index_name).load())
    return (time.perf_counter() - t0) * 1000.0


async def main_async(args: argparse.Namespace) -> int:
    out_path = Path(args.csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    adapter, vault = await setup_adapter(args.index_name)
    rng = np.random.default_rng(0xBEEF)

    rows: list[Snapshot] = []

    print(f"  reset[{args.index_name}]...", end=" ", flush=True)
    _reset_index(adapter, args.index_name)
    print("done")
    rows.append(snapshot(adapter, args.index_name, op="after_create"))

    if args.prime_rows > 0:
        n_batches = (args.prime_rows + PRIMER_BATCH_ROWS - 1) // PRIMER_BATCH_ROWS
        print(
            f"  priming {args.prime_rows} rows ({n_batches} batch(es))...",
            end=" ", flush=True,
        )
        try:
            elapsed_s = _prime(adapter, args.index_name, args.prime_rows, rng)
            print(f"done in {elapsed_s:.1f}s")
            rows.append(snapshot(adapter, args.index_name, op=f"after_prime[N={args.prime_rows}]", t_ms=elapsed_s * 1000.0))
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            print(f"FAILED: {err}")
            rows.append(snapshot(adapter, args.index_name, op=f"after_prime[N={args.prime_rows}]", error=err))
            # No point continuing the per-row probe if priming itself failed.
            _write_csv(out_path, rows)
            await vault.close()
            return 2

    hit_ceiling = False
    print(f"  single inserts (up to {args.insert_count}, use_row_insert=True, await=False, load=False)...")
    for i in range(args.insert_count):
        vec = rng.standard_normal(BENCH_DIM).astype(np.float32).tolist()
        t_ms, err = _single_insert(adapter, args.index_name, vec, await_completion=False, load=False)
        snap = snapshot(adapter, args.index_name, op=f"insert_row#{i + 1}", t_ms=t_ms, error=err)
        rows.append(snap)
        if err:
            print(f"    #{i + 1}: ERROR ({err}) — _guaranteed={snap.guaranteed} raw_shards={snap.n_shards_raw}/{snap.n_shards_total}")
            hit_ceiling = True
            break
        print(
            f"    #{i + 1}: ok t={t_ms:.0f}ms "
            f"_guaranteed={snap.guaranteed} _shards={snap.shards} "
            f"raw={snap.n_shards_raw}/{snap.n_shards_total}"
        )

    if hit_ceiling and args.recover != "none":
        print(f"  recovery: {args.recover}")
        if args.recover == "load":
            try:
                t_ms = _force_load(adapter, args.index_name)
                rows.append(snapshot(adapter, args.index_name, op="load()", t_ms=t_ms))
            except Exception as e:
                rows.append(snapshot(adapter, args.index_name, op="load()", error=f"{type(e).__name__}: {e}"))
        elif args.recover == "await_each":
            # One single insert with await=True, load=True — does the server free
            # the raw shard slots after this returns?
            vec = rng.standard_normal(BENCH_DIM).astype(np.float32).tolist()
            t_ms, err = _single_insert(adapter, args.index_name, vec, await_completion=True, load=True)
            rows.append(snapshot(adapter, args.index_name, op="insert_row(await=True,load=True)", t_ms=t_ms, error=err))

        # Try a couple more single inserts to see if the ceiling moved.
        for j in range(args.recover_probe):
            vec = rng.standard_normal(BENCH_DIM).astype(np.float32).tolist()
            t_ms, err = _single_insert(adapter, args.index_name, vec, await_completion=False, load=False)
            rows.append(snapshot(adapter, args.index_name, op=f"post_recover_insert#{j + 1}", t_ms=t_ms, error=err))
            if err:
                break

    print(f"  teardown: drop_index({args.index_name!r})")
    try:
        adapter.drop_index(args.index_name)
    except Exception as e:
        print(f"    drop_index failed (non-fatal): {e}")

    await vault.close()
    _write_csv(out_path, rows)
    print(f"  Wrote {len(rows)} rows → {out_path}")
    return 0


def _write_csv(path: Path, rows: list[Snapshot]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SNAPSHOT_COLUMNS)
        writer.writeheader()
        for r in rows:
            writer.writerow(r.as_row())


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--index-name", default="runebench_probe", help="bench index name (will be dropped+created)")
    p.add_argument("--prime-rows", type=int, default=0, help="batch-prime this many rows before the row-insert loop")
    p.add_argument("--insert-count", type=int, default=40, help="max single row-inserts to attempt (stops early on ceiling)")
    p.add_argument(
        "--recover",
        choices=("none", "load", "await_each"),
        default="load",
        help="after ceiling, try to recover via Index.load() or a single await+load insert",
    )
    p.add_argument("--recover-probe", type=int, default=3, help="row-inserts after recovery to test whether ceiling moved")
    p.add_argument("--csv", required=True, help="output CSV path")
    args = p.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
