# 2026-06-27 — 프론트엔드 죽은 잔재(Vite 템플릿 찌꺼기) 정리 (task 86)

## Plan vs actual
- 계획대로, 발산 낮음. 에셋 4개 삭제 + index.css 죽은 규칙/변수 제거 + 불필요 export 2건(`API_BASE`/`selectedNodeRef`) 비공개화. 빌드 ✓ · lint exit 0 · Playwright 6뷰 콘솔에러 0 / 시각 회귀 0.
- 미세 차이: 죽은 `h1`을 공유 셀렉터 `h1, h2`에서 떼며 분리된 두 `h2` 규칙을 하나로 자연 병합(동작 동일). 규모가 작아 Dynamic Workflow 대신 단일 에이전트 직접 실행(fg-run 비용 가이드), 코드리뷰 생략(위험영역 아님).

## Learnings
- **"기능 전수 점검 → 불필요 삭제" 요청의 실체는 거의 항상 dead-residue다.** 3-병렬 Explore 감사 결과, 사용자 대면 기능 중 잘라낼 것은 0이었고(앱이 이미 lean — 볼록껍질/스파이더화/맵팝업/`/`단축키 전부 도메인 정합), 삭제 대상은 전부 Vite 스캐폴드 잔재였다. → 다음번에도 "기능 삭제" 요청은 (a) 자동 계획 가능한 무위험 dead-residue와 (b) 사용자 사인오프가 필요한 기능 컷(premise가 틀린 경우 많음)으로 분리해서 다루는 게 맞다.
- **감사 중 코드↔문서 정합도 같이 확인하니 스테일이 잡혔다.** 부수 발견: `CONTEXT.md:43`(Book Events 용어)·`STRUCTURE.md:79`가 task 85(`GET /books` 제거) 이후 스테일 — book_events 오버레이는 이제 `/books`가 아니라 `/events`(`_load_approx_book_index`)가 소비한다. CONTEXT.md는 구현 디테일(엔드포인트명)을 담지 않는 게 원칙이므로, 정정 시 "어느 엔드포인트가 싣는지"는 빼고 용어 의미만 남기는 방향이 맞다.
- **Do differently next time**: 코드베이스 맵/CONTEXT 신선도 점검을 감사 루틴에 포함. fg-map 재실행 또는 fg-quick로 위 스테일 1건 정정하면 깔끔.

## 후속 후보 (이번 비목표 — 별건)
- **문서 스테일 정정**: `CONTEXT.md:43` Book Events 항목 + `STRUCTURE.md:79`의 `/books` → `/events` 반영 (fg-quick 또는 fg-map).
- **보강 후보 목록**(유효 기능 강화, 사용자 선택 대기): 타임라인 인라인 구절 빈/로딩 상태 구분, 검색 동명이인 부제·디바운스 로딩 피드백, verseLang localStorage 영속, 장소 컨텍스트 빈 박스 lazy-render, 이웃 50개 절단 "상위 N" 표기, 에러 토스트 자동닫힘.

## Doc updates
- CONTEXT.md promotion: 없음 (새 도메인 용어 없음 — 스테일 정정은 별건 후속으로 분리)
- ADR added: 없음 (되돌리기 쉬운 dead-residue 삭제, 트레이드오프 없음)
