# 2026-07-04 — 큐레이션 여정 사건에 실제 공동등장 인물 추가 (① 공백 7인 보강)

## Plan vs actual
- What went as planned: 계획의 편집 대상 그대로 7파일 17건 `participants` 추가 → `load_person_events.py` 재적재 → api 재시작 → UAT. 함께등장 보유 15→22/34(+7). 나머지 12 고립 인물 미착수. joshua↔moses는 계획대로 commission(모세 사후) 대신 `moses-kadesh-spies`(12정탐) 사용 — 트레잇 "믿음 민14:8-9 갈렙과 함께"가 뒷받침.
- Divergences (낮음): **다윗·여호수아의 동시대 섹션이 사라짐**. 동시대는 "함께등장에 이미 나온 인물 제외" 규칙이라, 왕국 4인·출애굽정복 2인이 전원 함께등장으로 승격되면 동시대가 빈다. 계획에 명시 안 했으나 설계상 정확한 부수효과(더 구체적 관계로 승격 = 개선).

## Learnings
- Do differently next time:
  - **authored 여정 사건에 큐레이션 공동참여자 추가는 대칭이다** — 한 사건 `participants[1..]`에 상대를 넣으면 양쪽 시트에 상호 노출된다. 쌍마다 한 번만 편집하면 됨(양쪽 파일 다 안 건드려도 됨). 단 상대 era 인물이 전부 함께등장으로 승격되면 그 인물의 ②동시대는 빈다(중복 제거) — 의도된 동작.
  - **`load_person_events.py`는 deploy.sh가 안 돌린다** → 여정 데이터 편집 후 반드시 **호스트에서 수동 재적재**(호스트 python에 neo4j 드라이버 있음, `NEO4J_URI=bolt://localhost:7687`) + **api 재시작**(`_build_connections`/persons lru_cache 무효화). 이 호스트가 곧 프로덕션 neo4j라 재적재 즉시 라이브 반영.
  - **대량 JSON 편집은 무편집 라운드트립 diff=0 확인 후 스크립트로** — `json.dump(indent=2, ensure_ascii=False)`가 기존 포맷(2-space·비ASCII·트레일링 개행 없음)을 그대로 재현함을 david.json으로 먼저 확인한 뒤 일괄 편집 → 참여자 추가만 남는 최소 diff. participants[0]=self 계약은 편집 스크립트에서 assert.
  - **"고립 인물의 ① 공백은 버그가 아니라 정확함"** — 사사들·요나·에스더·다니엘 등은 성경상 다른 큐레이션 인물과 공동등장이 없어 ①이 비는 게 옳다. 억지 주입 금지. 향후 인물 추가 시 이 구분을 먼저 판단.

## Doc updates
- CONTEXT.md promotion: '인물 연결 > 함께 등장한 인물' 항목의 데이터 스냅샷을 **count-free로 갱신**("15인만/다윗·솔로몬 비며" → 클러스터 예시 + "고립 인물은 공백이 정확"). CONCERNS의 "13인" stale-문서 함정 재발 방지 목적. (새 용어 아님 — 기존 항목 정확성 유지.)
- ADR added: none (기존 모델 안 데이터 큐레이션, 되돌리기 어려운 결정 아님).
