# 2026-06-11 — 소스 정리 구조·품질 티어 (Slice A 실행, B4/B5/B6 보류)

## 계획 vs 실제

- 계획대로 간 것:
  - Slice A 전부 실행·검증. A1 매직넘버 상수화(`SEARCH_LIMIT`/`MAX_NEIGHBORS_PER_TYPE`/`NODE_NEIGHBOR_LIMIT`, 값 동일), A2 좌표 `float()` 가드(깨진 좌표→해당 place만 스킵, 전체 500 방지), A3 TimelineView 정렬키 `?? 0`(number↔number 보장).
  - 검증: vite build green, eslint clean, py_compile clean, A2는 DB 없는 standalone 로직 테스트 통과. 커밋 2개(`b7928de` frontend, `6ceb3fb` backend).
- 발산:
  1. **6슬라이스 중 3개(Slice A)만 실행, B4/B5/B6 보류.** B5(cy 증분)·B6(풀텍스트 인덱스)는 계획서가 각각 "보류 가능"·"fg-ask로 분리·ADR" 명시 → 계획 승인 범위 내. B4(fit 통합)는 계획 외 추가 보류(실행자 판단).
  2. **A3 전제 보정** — 계획이 단정한 혼합타입 정렬 버그는 실제 미발현(잠재). `/events`가 `sortKey`를 항상 `float`로 반환(`events.py:24`)해서 `?? startDate` 폴백은 null/undefined에서만 발동 = dead. fix가 아니라 hazard 제거였음.
  3. **워크플로우 미사용 — 직접 실행.** 실효 작업량이 surgical edit 4건이라 병렬 서브에이전트는 과함. fg-run "scale 작으면 직접 처리" 제약 적용.
  4. **런타임(live API) 검증 미실시 — 스택 다운(HTTP 000).** Docker 이중 스택/Neo4j 미기동. 동작 보존 변경(A1/A3) 위해 전체 스택을 띄우진 않고 static+standalone로 대체.

## 학습

- 다음에 다르게 할 것:
  1. **계획이 검증 모달리티를 섞으면 fg-run에서 쪼개진다.** 이 plan은 자동검증 가능분(Slice A: build/compile)과 human-in-loop분(B4/B5: 라이브 브라우저, B6: ADR+DB 재적재)을 한 계획에 담았다. fg-run 워크플로우는 런타임 중 사람 입력을 못 받는다. → 다음 fg-ask에서 "cleanup/품질" 계획을 만들 땐 **검증 모달리티(자동검증 / 브라우저 수동 / ADR필요)로 슬라이스를 먼저 갈라** 별도 task로 분리할 것. 한 plan에 섞으면 결국 보류·분리된다.
  2. **GraphView fit/layout 변경은 정적으로 "동작 보존" 판정 불가.** B4가 막힌 실제 이유: 초기 fit(`GraphView.jsx:150`)이 고정 padding 40을 쓰는 건 같은 `.then` 클로저 안에서 `overlay` state가 아직 stale이기 때문. 단일 경로 통합엔 ref 도입 등 실제 동작 변경이 따른다. `graphview-uat-bugfix` 회고와 동일 결("fit/layout 버그는 런타임에서만 발견"). → GraphView 구조 변경은 반드시 dev 스택 띄운 브라우저 검증 슬롯과 묶어 계획.
  3. **계획이 "버그"라 단정해도 fix 전 데이터/API 계약을 먼저 확인.** A3가 그 예 — 계약(`sortKey` 항상 float)을 보면 버그가 미발현임이 드러나고 fix 범위가 "hazard 제거"로 좁아진다.
  4. **`git stash --keep-index`를 "안전한 no-op"으로 쓰지 말 것.** 파일 단위 커밋 분리하려다 이 명령을 무해하다 착각해 미staged였던 `search.py` 변경이 stash로 빠졌다. `git checkout stash@{0} -- <file>`로 복구. 커밋 나눌 땐 stash 장난 없이 순서대로 add/commit.

## 문서 업데이트

- CONTEXT.md 승격: 없음 (sortKey 계약 등은 구현 디테일 — 글로서리 오염 방지).
- ADR 추가: 없음 (보류 결정들은 가역적·비-아키텍처. B6 풀텍스트 인덱스 ADR은 별도 fg-ask로 분리 예정).
