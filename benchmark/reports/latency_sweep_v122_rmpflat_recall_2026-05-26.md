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
- **sweep_scenarios**: recall
- **bench_index_prefix**: runebench
- **reset_policy**: mutating groups: per-scenario drop+create+prime; read-only recall: one drop+create+prime per (N, group), all T5/T6/T7 scenarios share that primed index


## Sweep results

Rows = primed index size N. Columns = phase p50 (ms); the final column is `total` p95. A blank cell means that N was not measured for the scenario; `ERROR` means the scenario failed at that N.

### T5_exact_match

_feature: `recall`_

| N | embed p50 | score p50 | vault_topk p50 | remind p50 | total p50 | total p95 |
|---|---|---|---|---|---|---|
| 100 | 63.9 | 36.6 | 8.4 | 15.5 | 126.5 | 131.9 |
| 1000 | 56.8 | 46.6 | 8.6 | 15.7 | 127.4 | 139.7 |
| 10000 | 56.0 | 116.6 | 13.0 | 17.5 | 209.3 | 214.1 |
| 20000 | 55.2 | 204.5 | 17.7 | 17.9 | 293.9 | 308.1 |
| 25000 | 56.1 | 241.5 | 21.5 | 18.4 | 334.6 | 360.8 |
| 32000 | 53.8 | 356.9 | 24.6 | 18.7 | 454.6 | 470.5 |
| 50000 | 53.9 | 550.1 | 34.8 | 20.3 | 661.4 | 689.6 |
| 100000 | 53.5 | 1087.3 | 61.6 | 25.5 | 1232.7 | 1293.1 |

### T6_cross_lang

_feature: `recall`_

| N | embed p50 | score p50 | vault_topk p50 | remind p50 | total p50 | total p95 |
|---|---|---|---|---|---|---|
| 100 | 57.7 | 36.8 | 8.4 | 16.1 | 118.4 | 134.6 |
| 1000 | 56.2 | 47.2 | 8.7 | 16.5 | 130.4 | 148.4 |
| 10000 | 55.5 | 114.6 | 12.8 | 16.9 | 204.1 | 215.4 |
| 20000 | 56.0 | 202.9 | 17.8 | 17.9 | 294.3 | 311.5 |
| 25000 | 54.9 | 234.6 | 21.6 | 18.3 | 331.5 | 366.7 |
| 32000 | 54.7 | 353.2 | 24.4 | 19.3 | 456.0 | 476.9 |
| 50000 | 54.6 | 560.1 | 35.1 | 20.8 | 672.2 | 694.8 |
| 100000 | 54.8 | 1109.0 | 61.6 | 25.4 | 1257.9 | 1323.8 |
