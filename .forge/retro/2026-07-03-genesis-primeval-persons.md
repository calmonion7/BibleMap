# 2026-07-03 — 창세기 원시사 대표인물 추가 (task 118): 아담·노아 여정 큐레이션 +16사건

## Plan vs actual
- What went as planned: Dynamic Workflow(저작 병렬 3 → 장소 → 적재 → 검증, sonnet 캡+ECO)로 완주. 아담·노아 각 8사건(밴드 6~8 내), participants[0]은 Theographic rec id 실측(아담 recyYgUiSETdWFgEP·노아 recVMHzYdllgvTo09). authored 장소 2개(에덴·아라랏) 적재, 구절 16건(null 0)·인물사건 16개 적재, HAS_PARTICIPANT 16·OCCURS_AT 6·CONTAINS_BOOK 16. Playwright UAT: /persons/curated 원시사·eventCount 8 일치, PersonHub 원시사 섹션+2카드, stops 8·지도 마커·구절 드릴다운, 콘솔에러 0.
- Divergences: 경미 1건 — `books:[]` 빈 배열이 `generate_person_event_verses.py`의 멱등 skip을 유발(스크립트가 books **키 존재**만 보고 skip). 적재 에이전트가 키 제거 후 재실행해 정상 생성. 장소 로더는 `enrich_place_coords.py`였음(계획은 로더 미지정, 정상 해석). timeline-only 비율 높음(아담 4/8·노아 6/8)은 원시사 지리 특성상 의도된 결과.

## Learnings
- Do differently next time:
  - **큐레이션 인물 추가는 person_events 파일만으론 로스터에 안 뜬다 — 레지스트리 화이트리스트 등록이 선행.** `/persons/curated`(`persons.py _build_list`)는 `sorted(_ERA.keys())`만 순회하는 **하드코딩 화이트리스트**다(참여자 자동노출 아님 — 초기 조사가 이를 오판했고 그릴링 코드검증이 교정). 신규 인물 = **4개 터치포인트**: `persons.py`의 `_ERA`(slug→시대)·`_NAME_KO`(slug→한글) + (신규 시대면)`_ERA_ORDER` + `PersonHub.jsx`의 `ERA_ORDER`·`ERA_META`. journey.py는 persons.py 딕셔너리를 import하므로 자동. **백/프론트 `ERA_ORDER` 순서가 어긋나면 PersonHub가 미등록 era를 조용히 필터링(line ~221)해 API가 반환해도 화면에서 사라진다** — 반드시 짝수정.
  - **인물사건 저작 시 `books` 키를 아예 생략하라(빈 배열 금지).** `generate_person_event_verses.py`는 books 키가 있으면(빈 배열이어도) 멱등 skip해 context 파싱을 건너뛴다. 키를 넣지 않아야 스크립트가 EN 약어를 파싱해 채운다.
  - **Theographic에 실존하는 인물은 authored Person 경로(ADR-0008)가 아니라 족장 경로다.** 아담·노아·아벨·가인·셋·에녹은 이미 Theographic Person 노드(nameKo·traits 포함) → `participants[0]`에 rec id + slug 레지스트리 + person_events 파일로, 아브라함·이삭·야곱·요셉과 동일. ADR-0008의 authored-person 예외는 Theographic에 노드가 **없는** 사사들에만 적용. 다음에 창세기 얇은 인물(가인·에녹 등)을 추가할 때도 이 경로.
  - 기존 fuel 재확인: occursAt 장소 id 실측·EN 약어(풀네임 금지)·여정 응답 키 `stops`·공유자원(신규장소) 선반영→에이전트는 반환/오케스트레이터 병합 — 이번에도 그대로 유효.

## Doc updates
- CONTEXT.md promotion: none — "원시사"는 표준 시대명이고 era 분류는 glossary 미추적(이전 인물 로스터 회고 관례와 일치), 새 도메인 개념 없음.
- ADR added: none — books-키 gotcha·레지스트리 절차는 가역적 프로세스 선택(3조건 미충족); Theographic 실존 인물의 족장 경로는 ADR-0008 기존 커버(이번 케이스가 그 예외가 아님을 재확인한 것뿐).
