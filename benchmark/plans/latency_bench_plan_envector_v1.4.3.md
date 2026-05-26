# Rune × envector-msa-1.4.3 Latency Benchmark Plan

> **[측정 환경]** pyenvector 1.4.3 사용. eval_mode=mm32, index_type=ivf_vct.
> envector-cloud-be에 배포된 v1.4.3 클러스터 엔드포인트 사용.
> Vault는 원격(`tcp://193.122.124.173:50051`)에서 TLS로 실행 중.

## Context

v1.2.2 latency benchmark(`benchmark/plans/latency_bench_plan_envector_v1.2.2.md`)의 후속으로,
**envector-msa-1.4.3 환경**에서 두 가지 insert_mode(single, batch)를 각각 측정한다.

v1.2.2 plan과 달라진 환경:

| 항목 | v1.2.2 | v1.4.3 |
|------|--------|--------|
| pyenvector | 1.2.2 | 1.4.3 |
| eval_mode | rmp | mm32 |
| index_type | flat | ivf_vct |
| insert_mode | single | **single**, **batch** 각각 측정 |
| envector 엔드포인트 | `0511-1401-0001-4r6cwxfc908b.clusters.envector.io` | v1.4.3 클러스터 (배포 후 결정) |

> **[비교 주의]** eval_mode, index_type, 인프라가 동시에 달라졌으므로  
> v1.2.2 수치와의 차이를 단일 요인으로 해석해선 안 된다.

> **[insert_mode 정의]** Rune `batch_capture` MCP tool(embed+score만 수행, insert 없음)과 무관.
> - `single insert`: `use_row_insert=True`, `data=[vec]` — row insert API 경로 (벡터 1개)
> - `batch insert`: `use_row_insert=False`, `data=[v1,...,vN]` — batch insert API 경로 (벡터 N개)

---

## 측정 대상 기능 및 파이프라인 분해

### Feature 1: `capture` (MCP tool)

```
[1] 텍스트 → Embedding (로컬, Qwen/Qwen3-Embedding-0.6B)
[2] Novelty Check → envector inner_product (FHE, eval_mode=mm32, index_type=ivf_vct)
[3] Vault TopK Decrypt (gRPC tcp://193.122.124.173:50051)
[4] FHE Encrypt → index.insert (single: 1개 / batch: N개 한 번에)
────
Total end-to-end
```

### Feature 2: `recall` (MCP tool)

```
[1] 쿼리 → Embedding (로컬)
[2] Encrypted Search → envector (eval_mode=mm32, ivf_vct nprobe 기반)
[3] Vault TopK Decrypt (gRPC 원격)
[4] 메타데이터 조회 (로컬 JSON 파싱)
────
Total end-to-end
```

### Feature 3: `vault_status` (MCP tool)

- Vault gRPC 연결 latency (원격 서버 RTT 포함)

### Feature 4: `multi_capture` — 제외됨

> **[제외 — 2026-05-22]** `multi_capture`는 측정 시나리오에서 **제거**됐다.
> **사유**: multi_capture의 insert는 batch insert(`use_row_insert=False`) 경로인데,
> v1.4.3 클러스터는 batch insert RPC 누적 시 `async split batch data failed:
> UNAVAILABLE`로 다운된다(`benchmark/repro/BUG_REPORT.md`). 2026-05-22 검증에서
> 풀런 완주가 불가능했고 `await_completion=True, load=True`(BUG_REPORT의 "안전
> 패턴")로도 재현됐다. 검증 로그: `benchmark/reports/raw/multi_capture_awaitload_verify*`.
> 파이프라인·시나리오(T13/T14) 정의는 git 이력에서 확인 — 클러스터 결함 수정 후 재개 검토.

### Feature 5: `searchable` (insert → MERGED_SAVED 대기)

```
[1] 텍스트 → Embedding (로컬)
[2] Novelty Check → envector score (FHE)
[3] Vault TopK Decrypt (gRPC)
[4] FHE Encrypt → index.insert(await_searchable=True)
     — RPC 제출 + 서버 MERGED_SAVED 상태까지 대기 포함
────
Total end-to-end (MERGED_SAVED 시점까지)
```

> **[주의]** `EnVectorClient.insert()`는 request_id를 반환하지 않으므로
> RPC 제출 시간과 서버 대기 시간을 분리 측정할 수 없다.
> 세부 분해가 필요한 경우 `benchmark/runners/insert_row_only.py` 사용.

> **[시나리오]** T1–T3 입력(짧은 영어, 긴 영어, 한국어)을 그대로 재사용.
> T10 = T1 입력 / T11 = T2 입력 / T12 = T3 입력.

---

## 테스트 시나리오

시나리오 정의(T1–T9), 입력 텍스트, topk 변형, batch size는 v1.2.2 plan과 동일.  
모든 시나리오는 **ivf_vct 인덱스** 대상.

| ID | Feature | insert_mode | 내용 |
|----|---------|-------------|------|
| T1 | capture | 지정값 | 짧은 영어 (~30 tokens) |
| T2 | capture | 지정값 | 긴 영어 (~150 tokens) |
| T3 | capture | 지정값 | 한국어 |
| T5 | recall  | — | exact match query |
| T6 | recall  | — | cross-lang KO→EN |
| T7 | recall  | — | topk scaling (1, 3, 5, 10) |
| T8 | vault_status | — | gRPC health check |
| T10 | searchable | — | 짧은 영어 → insert(await_searchable=True), MERGED_SAVED 대기 포함 |
| T11 | searchable | — | 긴 영어 → insert(await_searchable=True), MERGED_SAVED 대기 포함 |
| T12 | searchable | — | 한국어 → insert(await_searchable=True), MERGED_SAVED 대기 포함 |

> **[제외된 시나리오]** 아래는 측정 대상에서 제거됐다 (정의는 git 이력 참고):
> - **T13·T14 (`multi_capture`)** — v1.4.3 클러스터가 batch insert 누적 시 크래시. Feature 4 참고. (제거 2026-05-22)
> - **T4 (`duplicate`, 중복 입력)** — `capture`(T1)와 사실상 중복 측정. capture는 같은 텍스트를
>   반복 capture하고 warmup run이 이미 사본을 인덱스에 심으므로, capture의 측정 run들이 이미
>   near-duplicate `score` 경로를 밟는다. 게다가 T4는 run마다 사본이 누적돼(drift) 고정 조건의
>   깨끗한 반복 샘플이 못 된다. (제거 2026-05-22)

---

## 측정 방법론

- **반복**: 10회 (warmup 2회 제외, 유효 8회)
- **보고 지표**: p50, p95, p99, mean (ms 단위)
- **타이머**: `time.perf_counter()`
- **단계별 측정**: embed / score / vault_topk / insert(또는 remind) / total 개별 계측
- **시나리오 격리**: 모든 시나리오는 같은 시작 조건(정확히 N개 primed records,
  fresh index, 선행 시나리오의 잔류 상태 없음)에서 측정한다.
  - **사유**: 격리된 환경에서 측정해야 신뢰할 수 있는 latency 데이터가 나온다.
    선행 시나리오가 인덱스 상태(row 수, raw/merged shard 비율, 클러스터 캐시,
    배경 merge worker 상태 등)를 흔든 채로 다음 시나리오를 측정하면 그 수치가
    "N 사이즈의 인덱스에서 X 시나리오의 latency"인지 "T1을 N+δ회 돌린 다음
    T2 latency"인지 구분이 안 된다.
  - **정책 — mutating vs read-only**:
    - **mutating 시나리오** (capture T1/T2/T3, searchable T10/T11/T12): 측정 중
      insert가 일어나 인덱스 상태를 바꾸므로 시나리오마다 drop+create+prime 다시.
      공유 인덱스에서는 (a) 후행 시나리오 수치가 선행 시나리오의 누적 insert를
      반영해 측정값이 오염되고, (b) row-insert 슬롯 소진으로 후행이 실패하는
      사례까지 관찰됨 (2026-05-25 capture sweep, 메커니즘
      `benchmark/reports/insertable_probe_v143_2026-05-26.md`).
    - **read-only 시나리오** (recall T5/T6 — sweep mode / single-grid 공통,
      그리고 single-grid 전용 T7 topk 변형): 측정이 인덱스 상태를 바꾸지 않으므로
      동일 N의 primed 인덱스를 공유. 시나리오마다 재-prime하면 같은 데이터를
      다시 까는 셈이며, 특히 N=100000에서는 priming 한 번이 ~16분이라 시간 손실이 큼.
      시나리오별 warmup run이 클러스터 캐시 워밍 차이는 흡수.
  - **구현**:
    - sweep mode: mutating은 `{bench_index}_N{N}_{sid}` per-scenario 유니크 인덱스,
      read-only(recall T5/T6)는 `{bench_index}_N{N}_recall` 그룹 공유 인덱스.
      T7은 sweep 측정 대상이 아님(N과 무관).
    - single-grid mode: mutating 시나리오는 각각 reset+prime,
      recall 블록(T5/T6/T7 topk 4종)은 한 번 reset+prime 후 공유.

---

## 인프라 전제조건

1. envector-msa-1.4.3 → envector-cloud-be에 배포 완료
2. **ivf_vct 인덱스** 사전 생성 (nlist, default_nprobe 설정 포함)
3. Vault에 mm32 eval_mode 키 등록 완료
4. `~/.rune/config.json`의 `envector.endpoint` → v1.4.3 클러스터 URL로 업데이트

---

## 구현 파일

| 파일 | 설명 |
|------|------|
| `benchmark/runners/latency_bench_v1.4.3.py` | 신규 runner. `--insert-mode single|batch` 필수 |
| `benchmark/runners/common.py` | `PhaseLatency`, `LatencyScenarioResult`, `LatencyBenchReport` |
| `agents/common/envector_client.py` | `eval_mode` 파라미터 추가 (기본값 "mm32") |

---

## 실행 방법

> **[multi_capture 제외]** `multi_capture`(T13/T14)는 Feature 4 사유로 측정하지
> 않는다. runner에 feature 제외 플래그가 없으므로 `--feature multi_capture`는
> 돌리지 않는다. `--feature` 생략 전체 실행 시 multi_capture가 맨 마지막에 돌며
> T13/T14가 FAIL로 남는데(앞서 측정된 다른 feature 수치는 유효), 그 FAIL은 무시한다.

```bash
# 사전 확인: vault 연결만 테스트
.venv/bin/python benchmark/runners/latency_bench_v1.4.3.py \
    --insert-mode single --feature vault_status --runs 3 --warmup 1

# single insert 전체 실행
.venv/bin/python benchmark/runners/latency_bench_v1.4.3.py \
    --insert-mode single --runs 10 --warmup 2 \
    --report benchmark/reports/latency_results_v1.4.3_ivfvct_single_$(date +%Y-%m-%d).md \
    --format md

# batch insert 전체 실행
.venv/bin/python benchmark/runners/latency_bench_v1.4.3.py \
    --insert-mode batch --runs 10 --warmup 2 \
    --report benchmark/reports/latency_results_v1.4.3_ivfvct_batch_$(date +%Y-%m-%d).md \
    --format md
```

---

## 검증 방법

1. **단계별 합계 일치**: `sum(phase latencies) ≈ total` (±5% 허용)
2. **재현성**: 같은 시나리오 재실행 시 p50 변동 < 20%
3. **batch 효율**: T1 insert_ms(batch) < N × T1 insert_ms(single) (배치 효율 확인)
4. **IVF_VCT score latency**: v1.2.2 flat score와 비교 → nprobe 오버헤드 반영 여부 확인
