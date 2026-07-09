# 2026-07-09 — 욥(Job) 인물 추가 (task 147: 저작 인물 노드 + 여정 7 + 관계 7 + 성품 4)

## Plan vs actual
- What went as planned: 욥을 저작 인물(`authored-person-job`, ADR-0008)로 추가 — 노드+백엔드 등록(_ERA/_NAME_KO)·우스 땅(에돔 전승 lat 30.7/lng 35.6)·여정 7사건·관계 7개(하나님4·아내1·엘리바스/빌닷/소발 3×3·엘리후2·자녀3 = 19국면)·성품 4개. 프리베이크 null 0(관계 38·성품 8 filled), relations 164→171 무손실. 큐레이션 34→35인. Playwright 콘솔 에러 0, 앱 /api 실패 0, 여정·관계·성품 렌더 확인. coParticipants 공백은 예측대로(고립 인물), 동시대=족장 4인.
- Divergences:
  - **[중] 계획 S6이 `enrich_place_coords.py`를 빠뜨림.** `load_person_events.py`는 Place를 **MATCH**(생성 아님)하므로, 새 authored 장소(우스)를 만드는 `enrich_place_coords.py`를 먼저 안 돌리면 OCCURS_AT가 안 생겨 인물 지도가 빈다. 첫 적재 후 Neo4j 검증(`places=[]`)에서 포착 → enrich 실행 후 load_person_events 재실행(멱등)으로 복구(OCCURS_AT +7).
  - [소] 교차장 범위(`38:1–42:6`)는 event_verses에서 앵커절(38:1)만 확장 — rangeLabel 정상, 파서 기존 동작(결함 아님).
  - [소] 적재 스크립트가 컨테이너에 없음(Dockerfile이 `app/`만 복사) → 호스트에서 실행(호스트 neo4j 6.2.0 + :7687 공개).
  - 백엔드 코드(_ERA/_NAME_KO) 변경이라 `docker compose up -d --build api`(restart 아님 — 2026-07-09 relations retro footgun 그대로 적용, 문제 없이 통과).

## Learnings
- Do differently next time:
  - **새 authored 인물+새 장소를 추가할 때 정본 적재 순서 = `load_authored_persons` → `enrich_place_coords` → `load_person_events` → `inject_person_traits`.** ADR-0008은 "authored_persons가 person_events보다 먼저"만 명시하는데, **장소 로더가 그 사이에 빠지면 지도가 조용히 빈다**(load_person_events의 Place는 MERGE가 아니라 MATCH). 기존 인물 추가는 대개 기존 장소를 재사용해 이 함정을 안 밟았지만, 신규 장소를 동반하는 인물(욥=우스)에서 드러남. 다음 "인물 추가" 작업 계획 시 S6 파이프라인에 enrich_place_coords를 반드시 포함.
  - **적재 후 Neo4j에서 `HAS_PARTICIPANT→Event→OCCURS_AT→Place` 경로를 직접 쿼리해 places 비었는지 먼저 확인**하면 API/UI 검증 전에 이 누락을 즉시 잡는다(이번에 그렇게 잡음).
  - 인물 1명 데이터 저작은 **직접 실행이 워크플로보다 적합**(단일파일 순차 저작·순차 적재 파이프라인). 이번에 fg-run Constraints대로 직접 실행해 저렴·무충돌. "single person = direct" 휴리스틱 재확인.
- 사소/일회성: 프리베이크(generate_verse_text·generate_person_event_verses)는 getbible urllib이라 API키 불필요·호스트에서 실행 가능. 성품 verse_text도 generate_verse_text가 relations와 함께 프리베이크(별도 스크립트 아님).

## Doc updates
- CONTEXT.md promotion: none — 새 용어 없음(기존 저작 인물·여정·인물 관계 패턴 그대로).
- ADR added: none — ADR-0008 적용. 적재순서 보완은 절차 학습이라 위 "Do differently"에 기록(하드 결정 아님). 향후 인물 추가가 잦아지면 ADR-0008 Consequences에 장소 로더 한 줄 추가를 검토할 여지.
