# Rune Latency Sweep Report — pyenvector 1.2.2

## Environment

- **sdk_version**: 1.2.2
- **date**: 2026-05-26
- **envector_endpoint**: rune-bench-opo0wzsyy45s.clusters.envector.io
- **vault_endpoint**: tcp://193.122.124.173:50051
- **embedding_model**: Qwen/Qwen3-Embedding-0.6B
- **embedding_mode**: sbert
- **key_id**: vault-key
- **eval_mode**: rmp
- **index_type**: flat
- **insert_mode**: single
- **network_rtt**: unknown
- **runs_per_scenario**: 12
- **warmup_runs**: 3
- **direct_envector**: True
- **sweep_mode**: True
- **sweep_grid_N**: 100,1000,10000,20000,25000,32000,50000,100000
- **sweep_scenarios**: capture
- **bench_index_prefix**: runebench
- **reset_policy**: mutating groups: per-scenario drop+create+prime; read-only recall: one drop+create+prime per (N, group), all T5/T6/T7 scenarios share that primed index


## Sweep results

Rows = primed index size N. Columns = phase p50 (ms); the final column is `total` p95. A blank cell means that N was not measured for the scenario; `ERROR` means the scenario failed at that N.

### T1_short_en

_feature: `capture`_

| N | embed p50 | score p50 | vault_topk p50 | insert p50 | total p50 | total p95 |
|---|---|---|---|---|---|---|
| 100 | 72.5 | 66.4 | 21.4 | 145.8 | 314.0 | 336.2 |
| 1000 | 72.6 | 75.3 | 21.7 | 137.4 | 307.6 | 355.7 |
| 10000 | 72.2 | 163.4 | 26.3 | 135.2 | 403.5 | 450.1 |
| 20000 | 72.6 | 251.9 | 31.5 | 138.5 | 501.8 | 549.0 |
| 25000 | 72.4 | 306.7 | 35.7 | 149.1 | 571.4 | 608.2 |
| 32000 | 76.4 | 393.3 | 38.7 | 160.5 | 664.8 | 758.0 |
| 50000 | 72.3 | 599.7 | 49.5 | 158.6 | 887.4 | 943.3 |
| 100000 | 72.1 | 1142.8 | 75.8 | 170.4 | 1468.9 | 1527.4 |

### T2_long_en

_feature: `capture`_

| N | embed p50 | score p50 | vault_topk p50 | insert p50 | total p50 | total p95 |
|---|---|---|---|---|---|---|
| 100 | 89.1 | 78.0 | 21.4 | 145.3 | 325.0 | 375.4 |
| 1000 | 89.6 | 81.6 | 21.9 | 139.5 | 333.9 | 365.0 |
| 10000 | 89.9 | 157.5 | 26.9 | 139.8 | 420.2 | 448.5 |
| 20000 | 90.1 | 241.5 | 31.5 | 134.1 | 488.2 | 598.0 |
| 25000 | 89.3 | 291.1 | 35.7 | 153.7 | 572.6 | 614.5 |
| 32000 | 91.0 | 389.1 | 38.5 | 168.4 | 684.4 | 742.9 |
| 50000 | 89.8 | 592.1 | 49.4 | 166.0 | 904.7 | 964.0 |
| 100000 | 89.5 | 1156.3 | 76.5 | 169.2 | 1504.5 | 1596.2 |

### T3_korean

_feature: `capture`_

| N | embed p50 | score p50 | vault_topk p50 | insert p50 | total p50 | total p95 |
|---|---|---|---|---|---|---|
| 100 | 121.3 | 65.9 | 21.6 | 138.9 | 361.2 | 395.8 |
| 1000 | 119.7 | 85.3 | 22.1 | 128.6 | 355.7 | 441.5 |
| 10000 | 119.3 | 163.6 | 26.6 | 150.3 | 454.7 | 490.6 |
| 20000 | 119.8 | 232.8 | 31.6 | 142.3 | 535.6 | 609.2 |
| 25000 | 127.7 | 292.1 | 35.4 | 152.0 | 606.0 | 671.6 |
| 32000 | 119.3 | 395.3 | 38.8 | 166.8 | 725.2 | 766.8 |
| 50000 | 120.3 | 585.5 | 49.7 | 151.3 | 907.1 | 1009.8 |
| 100000 | 119.8 | 1190.6 | 77.4 | 174.1 | 1580.0 | 1656.3 |
