# Rune Latency Sweep Report — pyenvector 1.4.3

## Environment

- **sdk_version**: 1.4.3
- **date**: 2026-05-28
- **envector_endpoint**: runebench-052701-czpcmtt1q9f3.clusters.envector.ai
- **vault_endpoint**: tcp://161.118.149.143:50051
- **embedding_model**: Qwen/Qwen3-Embedding-0.6B
- **embedding_mode**: sbert
- **key_id**: vault-key
- **eval_mode**: mm32
- **index_type**: ivf_vct
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
| 100 | 72.6 | 855.7 | 8.4 | 1503.8 | 2461.2 | 3171.5 |
| 1000 | 82.2 | 848.7 | 8.6 | 1441.3 | 2430.6 | 2720.0 |
| 10000 | 80.5 | 1027.8 | 13.2 | 1608.5 | 2826.1 | 3261.1 |
| 20000 | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |
| 25000 | 72.9 | 994.6 | 16.7 | 1605.2 | 2703.5 | 3247.8 |
| 32000 | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |
| 50000 | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |
| 100000 | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |

### T2_long_en

_feature: `capture`_

| N | embed p50 | score p50 | vault_topk p50 | insert p50 | total p50 | total p95 |
|---|---|---|---|---|---|---|
| 100 | 101.5 | 1022.7 | 8.5 | 1551.6 | 2654.6 | 3024.5 |
| 1000 | 94.1 | 812.7 | 8.5 | 1514.2 | 2457.6 | 2657.1 |
| 10000 | 89.9 | 955.7 | 13.4 | 1660.1 | 2658.1 | 3139.0 |
| 20000 | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |
| 25000 | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |
| 32000 | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |
| 50000 | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |
| 100000 | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |

### T3_korean

_feature: `capture`_

| N | embed p50 | score p50 | vault_topk p50 | insert p50 | total p50 | total p95 |
|---|---|---|---|---|---|---|
| 100 | 131.2 | 964.9 | 8.6 | 1522.8 | 2628.9 | 3139.9 |
| 1000 | 130.1 | 817.9 | 8.6 | 1467.6 | 2411.9 | 2695.9 |
| 10000 | 132.0 | 971.5 | 13.4 | 1557.7 | 2713.8 | 3102.5 |
| 20000 | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |
| 25000 | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |
| 32000 | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |
| 50000 | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |
| 100000 | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |
