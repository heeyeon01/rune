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
- **sweep_scenarios**: searchable
- **bench_index_prefix**: runebench
- **reset_policy**: mutating groups: per-scenario drop+create+prime; read-only recall: one drop+create+prime per (N, group), all T5/T6/T7 scenarios share that primed index


## Sweep results

Rows = primed index size N. Columns = phase p50 (ms); the final column is `total` p95. A blank cell means that N was not measured for the scenario; `ERROR` means the scenario failed at that N.

### T10_short_en_searchable

_feature: `searchable`_

| N | embed p50 | score p50 | vault_topk p50 | insert_rpc p50 | merge_wait p50 | publish_wait p50 | total p50 | total p95 |
|---|---|---|---|---|---|---|---|---|
| 100 | 81.7 | 858.8 | 8.5 | 1372.1 | 15575.7 | 272.8 | 18531.4 | 18875.0 |
| 1000 | 73.2 | 872.7 | 8.6 | 1425.2 | 15593.4 | 245.3 | 18646.1 | 18969.7 |
| 10000 | 80.2 | 907.8 | 13.2 | 1420.0 | 15712.9 | 297.4 | 18833.5 | 19273.7 |
| 20000 | 79.9 | 929.8 | 16.2 | 1402.7 | 15693.0 | 400.1 | 18980.3 | 19602.2 |
| 25000 | 79.8 | 955.4 | 16.9 | 1446.5 | 15839.1 | 456.4 | 19323.2 | 19620.7 |
| 32000 | 77.0 | 827.7 | 17.9 | 1391.7 | 15864.7 | 536.9 | 19250.0 | 19550.2 |
| 50000 | 79.9 | 936.7 | 16.8 | 1585.5 | 15678.4 | 512.5 | 19406.2 | 19751.1 |
| 100000 | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |

### T11_long_en_searchable

_feature: `searchable`_

| N | embed p50 | score p50 | vault_topk p50 | insert_rpc p50 | merge_wait p50 | publish_wait p50 | total p50 | total p95 |
|---|---|---|---|---|---|---|---|---|
| 100 | 93.5 | 890.5 | 8.5 | 1377.1 | 15582.4 | 235.6 | 18448.3 | 18866.9 |
| 1000 | 98.3 | 804.9 | 8.6 | 1333.2 | 15618.2 | 214.9 | 18402.7 | 18642.2 |
| 10000 | 89.9 | 766.5 | 13.3 | 1293.9 | 15718.3 | 256.2 | 18495.6 | 18611.0 |
| 20000 | 97.4 | 960.7 | 16.3 | 1437.1 | 15686.8 | 365.8 | 19092.1 | 19404.9 |
| 25000 | 93.4 | 888.4 | 16.8 | 1503.3 | 15862.5 | 478.4 | 19420.9 | 19678.3 |
| 32000 | 98.0 | 904.3 | 17.8 | 1439.8 | 15790.5 | 416.5 | 19106.0 | 19722.2 |
| 50000 | 98.9 | 837.7 | 16.9 | 1397.4 | 15770.5 | 512.3 | 19188.7 | 19784.7 |
| 100000 | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |

### T12_korean_searchable

_feature: `searchable`_

| N | embed p50 | score p50 | vault_topk p50 | insert_rpc p50 | merge_wait p50 | publish_wait p50 | total p50 | total p95 |
|---|---|---|---|---|---|---|---|---|
| 100 | 124.6 | 892.0 | 8.5 | 1429.2 | 15721.7 | 243.8 | 18722.3 | 19267.4 |
| 1000 | 129.1 | 813.4 | 8.6 | 1400.6 | 15663.8 | 205.4 | 18594.5 | 18847.7 |
| 10000 | 131.4 | 872.4 | 13.4 | 1479.5 | 15788.6 | 327.8 | 18931.2 | 19379.1 |
| 20000 | 125.0 | 923.2 | 16.2 | 1475.3 | 15678.5 | 365.7 | 18938.2 | 19660.7 |
| 25000 | 129.9 | 964.0 | 16.9 | 1433.9 | 15788.6 | 426.0 | 19188.8 | 33438.9 |
| 32000 | 130.3 | 913.3 | 17.7 | 1404.4 | 15881.3 | 521.4 | 19436.2 | 33237.5 |
| 50000 | 128.7 | 940.5 | 16.9 | 1417.1 | 15765.2 | 496.9 | 19382.6 | 21698.3 |
| 100000 | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |
