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
- **sweep_scenarios**: searchable
- **bench_index_prefix**: runebench
- **reset_policy**: mutating groups: per-scenario drop+create+prime; read-only recall: one drop+create+prime per (N, group), all T5/T6/T7 scenarios share that primed index


## Sweep results

Rows = primed index size N. Columns = phase p50 (ms); the final column is `total` p95. A blank cell means that N was not measured for the scenario; `ERROR` means the scenario failed at that N.

### T10_short_en_searchable

_feature: `searchable`_

| N | embed p50 | score p50 | vault_topk p50 | insert_searchable p50 | total p50 | total p95 |
|---|---|---|---|---|---|---|
| 100 | 79.4 | 73.6 | 21.4 | 240.9 | 424.4 | 487.9 |
| 1000 | 73.5 | 80.5 | 21.4 | 233.7 | 403.5 | 490.2 |
| 10000 | 81.4 | 161.1 | 26.3 | 325.0 | 590.0 | 663.9 |
| 20000 | 73.1 | 232.4 | 31.2 | 427.9 | 768.5 | 813.9 |
| 25000 | 73.9 | 288.3 | 35.1 | 476.4 | 863.5 | 964.0 |
| 32000 | 73.0 | 408.5 | 38.3 | 597.1 | 1138.9 | 1198.5 |
| 50000 | 72.4 | 608.1 | 48.6 | 828.1 | 1552.2 | 1706.5 |
| 100000 | 72.4 | 1133.4 | 76.4 | 1433.0 | 2713.7 | 2919.4 |

### T11_long_en_searchable

_feature: `searchable`_

| N | embed p50 | score p50 | vault_topk p50 | insert_searchable p50 | total p50 | total p95 |
|---|---|---|---|---|---|---|
| 100 | 90.6 | 69.5 | 21.3 | 235.7 | 413.0 | 499.8 |
| 1000 | 91.3 | 76.5 | 21.4 | 245.8 | 428.5 | 637.8 |
| 10000 | 90.4 | 156.3 | 26.4 | 325.2 | 613.1 | 660.8 |
| 20000 | 91.4 | 242.7 | 31.0 | 429.4 | 791.5 | 842.7 |
| 25000 | 89.9 | 301.7 | 35.3 | 472.1 | 899.0 | 994.8 |
| 32000 | 90.3 | 403.9 | 38.0 | 591.0 | 1140.2 | 1201.6 |
| 50000 | 89.7 | 605.0 | 48.7 | 834.1 | 1575.6 | 1708.5 |
| 100000 | 89.4 | 1138.8 | 76.2 | 1382.4 | 2706.8 | 2867.5 |

### T12_korean_searchable

_feature: `searchable`_

| N | embed p50 | score p50 | vault_topk p50 | insert_searchable p50 | total p50 | total p95 |
|---|---|---|---|---|---|---|
| 100 | 120.2 | 61.8 | 21.4 | 228.4 | 435.6 | 533.5 |
| 1000 | 121.0 | 69.5 | 21.6 | 233.7 | 449.3 | 557.2 |
| 10000 | 120.5 | 153.3 | 26.4 | 322.1 | 634.5 | 708.1 |
| 20000 | 122.2 | 232.3 | 32.6 | 422.8 | 811.0 | 861.5 |
| 25000 | 119.9 | 307.4 | 35.2 | 492.0 | 966.5 | 1033.4 |
| 32000 | 119.8 | 412.0 | 37.8 | 598.2 | 1152.3 | 1286.1 |
| 50000 | 120.6 | 615.9 | 48.7 | 846.7 | 1654.5 | 1750.0 |
| 100000 | 119.7 | 1147.1 | 76.9 | 1380.1 | 2731.5 | 2854.0 |
