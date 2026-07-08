# 2026-07-08 — 인물 관계 데이터 (1/6) 저작 규칙 정립 + 왕국 시대 파일럿 (task 139)

## Plan vs actual
- What went as planned: 7슬라이스(S1 AUTHORING.md · S2 스승제자 유형 · S3~S5 사무엘·사울·솔로몬 저작 · S6 프리베이크+빌드 · S7 Playwright)를 계획대로 완주. 신규 relObj 11개 append(24→35), 프리베이크 `null:0`(구절 참조 오탈자 0)·`kept:180`(다윗 국면 멱등 무변경), :8080 세 인물 렌더·다윗 무회귀·콘솔/API 에러 0. pair 재사용(사무엘↔사울 1개 저작 → 양쪽 노출, 다윗 pair 3종 재사용) 의도대로 동작.
- Divergences:
  - **워크플로우 아닌 직접 순차 실행**. S3~S5가 단일 파일 `relations.json`에 append + pair 중복 금지(교차 pair 조율)를 요구 → 병렬 서브에이전트는 같은 JSON 덮어쓰기·중복 pair 위험. 성경 구절 정확성도 단일 컨텍스트가 유리. fg-run "단일 에이전트로 충분하면 직접 처리" 조항으로 이탈.
  - **프리베이크 타깃 실행**. `generate_verse_text.py`의 `main()`은 event까지 굽느라 수 분 → `bake_relations()`만 모듈 import로 호출(필요한 32장만 fetch). argparse 부재로 이 방식.
  - **`up -d api`로는 신규 데이터 안 보임 → `restart api` 필요**(가장 큰 삽질). 백엔드 `_load_relations`/`_build_relations`가 `@functools.lru_cache`로 기동 시 카탈로그 캐시. `docker compose up -d api`는 config 무변경 시 재생성 안 함("Running")이라 옛 24관계 캐시를 계속 서빙(신규 0개 반환). `restart api`로 해결.
  - 밀도 비례로 사울 상대를 요나단·아브넬·미갈 3인으로 선별(계획 예시 "미갈·요나단 등"의 범위 내 축소, 규칙 7).

## Learnings
- Do differently next time:
  - **관계 데이터 검증은 `docker compose restart api`를 써라 — `up -d`가 아니다.** 백엔드가 relations 카탈로그를 `lru_cache`로 메모리 캐시하고, `up -d`는 config 무변경 시 프로세스를 안 죽여 캐시가 안 비워진다. ("오버레이 restart" 교훈 재확인. **AUTHORING.md 규칙 8에 이 내용으로 수정 반영함** → 파트 2~6은 처음부터 restart 사용.)
  - **관계 저작은 단일 파일 순차 — 병렬 워크플로우 금지.** `relations.json`은 단일 append 타깃이고 pair 중복 금지가 교차 인물 간 조율을 요구한다. 병렬 팬아웃은 덮어쓰기·중복 pair를 낳는다. 파트 2~6도 직접 순차.
  - **프리베이크는 `bake_relations()`만 타깃 실행하면 빠르다** — `main()`은 event 굽기로 수 분. `python3 -c "import generate_verse_text as g; g.bake_relations()"`(scripts 디렉터리에서).
  - 저작 후 `null` 카운트로 구절 참조 오탈자를 즉시 검출(getbible 해석 실패 = null). 이번엔 `null:0`.
- 관계 데이터 진입은 `#/person/<slug>/relations` 해시 URL로 직접 가능(urlState) — Playwright 검증 시 지도 클릭 플로우 우회.

## Doc updates
- CONTEXT.md promotion: **`스승제자` 유형을 107행 관계 유형 열거에 추가**(랍비-제자·후계 계승; 엘리↔사무엘·엘리야↔엘리사·예수↔제자). 관계 도메인 어휘에 8번째 유형이 실제 진입 → 글로서리 최신화.
- ADR added: none (되돌리기 어려운 결정 아님 — 운영 gotcha·저작 절차는 AUTHORING.md에 귀속).
- data/person_relations/AUTHORING.md 규칙 8-3: `up -d api` → `restart api`로 **정정**(참조 문서 버그 동반 수정, 파트 2~6 footgun 예방).
- restart footgun·"오버레이 restart"는 메모리 [[project-biblemap-status]]에 이미 요약됨.
