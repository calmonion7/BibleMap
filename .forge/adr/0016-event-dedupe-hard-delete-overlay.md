# 중복 이벤트는 실삭제(DETACH DELETE) + 오버레이 대장 — superseded 숨김 반려

task#166 분석이 확정한 중복 이벤트(같은 실제 사건의 authored↔theographic·authored↔authored 재저작)를 그래프에서 **실삭제**하기로 했다(task#168). 단 Neo4j는 `load_theographic.py` 재적재로 재구축될 수 있어 그래프에서만 지우면 중복이 되살아나므로, 삭제는 **`data/event_dedupe/` 오버레이 대장 + 멱등 적용 스크립트**로 영속화한다(date_corrections/task#158과 동일 패턴). authored 중복은 원천이 우리 저작 파일이므로 오버레이가 아니라 `data/authored_events/` **원천에서 직접 제거**한다.

## Considered Options

- **(채택) 실삭제 + 오버레이 대장** — 런타임·API·프론트에 잔존 코드 0. 복구 감사 추적은 3중(theographic 원본 JSON·분석 리포트·대장 파일)으로 충분.
- **(반려) superseded 표시 + 숨김** — 모든 이벤트 조회 지점에 필터 조건이 영구 잔존(eco 위배)하고, "삭제됐지만 존재하는" 노드가 집계·검증 스크립트마다 예외를 낳는다.

## Consequences

- 삭제 전 3중 보호가 적용 스크립트의 일부다: 구절 겹침 교차검증 게이트(양쪽 절 보유·교집합 공집합 → 적용 제외), 조건부 구절 이관(keep이 절 없으면 remove의 verseID 참조 이관 — CONTEXT 「구절 근거 원칙」 보존), 전 data/ removed-id 참조 스캔·리매핑.
- 파이프라인 재적재 후에는 `apply_event_dedupe.py`를 재실행해야 중복이 다시 제거된다(멱등) — load 계열 스크립트를 돌리는 사람은 이 후처리를 잊지 말 것.
- 리포트 low 5건(개요형 authored vs 세부 순차 사건)은 중복이 아니라 PART_OF 계층 문제로 판정 — 삭제 대상에서 영구 제외, 계층 재구성은 별개 과제.
