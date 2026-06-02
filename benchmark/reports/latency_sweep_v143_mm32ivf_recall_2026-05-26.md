# Rune Latency Sweep Report — pyenvector 1.4.3

## Environment

- **sdk_version**: 1.4.3
- **date**: 2026-05-26
- **envector_endpoint**: runebench-0520-2-scfomauvy6cn.clusters.envector.ai
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
- **sweep_scenarios**: recall
- **bench_index_prefix**: runebench
- **reset_policy**: mutating groups: per-scenario drop+create+prime; read-only recall: one drop+create+prime per (N, group), all T5/T6/T7 scenarios share that primed index


## Sweep results

Rows = primed index size N. Columns = phase p50 (ms); the final column is `total` p95. A blank cell means that N was not measured for the scenario; `ERROR` means the scenario failed at that N.

### T5_exact_match

_feature: `recall`_

| N | embed p50 | score p50 | vault_topk p50 | remind p50 | total p50 | total p95 |
|---|---|---|---|---|---|---|
| 100 | 52.7 | 898.8 | 8.5 | 76.2 | 1035.8 | 1308.2 |
| 1000 | 56.1 | 934.5 | 8.6 | 45.2 | 1053.5 | 1190.1 |
| 10000 | 55.0 | 999.0 | 13.3 | 98.1 | 1168.3 | 1419.4 |
| 20000 | 53.3 | 1091.6 | 16.4 | 111.6 | 1274.5 | 1576.9 |
| 25000 | 52.6 | 1059.8 | 16.9 | 88.7 | 1219.9 | 1450.4 |
| 32000 | 52.6 | 1103.5 | 17.9 | 92.6 | 1268.2 | 1388.8 |
| 50000 | 52.5 | 1078.9 | 16.7 | 113.2 | 1282.1 | 1399.7 |
| 100000 | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |

### T6_cross_lang

_feature: `recall`_

| N | embed p50 | score p50 | vault_topk p50 | remind p50 | total p50 | total p95 |
|---|---|---|---|---|---|---|
| 100 | 53.9 | 796.9 | 8.4 | 77.0 | 935.3 | 1045.1 |
| 1000 | 53.6 | 805.1 | 8.6 | 44.9 | 912.8 | 1186.2 |
| 10000 | 54.9 | 1088.1 | 13.5 | 98.7 | 1253.5 | 434585.2 |
| 20000 | 53.9 | 1020.1 | 16.2 | 105.6 | 1200.7 | 1395.9 |
| 25000 | 53.5 | 957.2 | 17.0 | 88.3 | 1116.8 | 1406.7 |
| 32000 | 53.5 | 1092.9 | 17.9 | 94.1 | 1257.8 | 1615.5 |
| 50000 | 54.6 | 949.6 | 16.9 | 94.9 | 1117.1 | 1403.8 |
| 100000 | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |
