# 2026-06-17 — 추정 성경책 31권 → 사건 연결: book_events 오버레이 + 책 마커 ⚡사건 칩

## Plan vs actual
- What went as planned: 목표 달성 — 타임라인뷰 추정연도 책 31권 마커 행에 ⚡ 사건 칩 표시, 클릭 시 해당 사건 선택. 사건 행의 📖 근거 칩은 그대로 유지(무오염). 슬라이스 1·3·4 산출물 위치·형식은 계획대로(`generate_book_events.py`, `data/book_events/books.json`, `TimelineView.jsx`, `CONTEXT.md`).
- Divergences:
  - **[중대] 저장 방식: Neo4j `CONTAINS_BOOK` 주입(슬라이스 2) → 런타임 오버레이로 전환.** 실행 전 검토에서 설계 충돌 발견: `CONTAINS_BOOK`은 "구절 교집합 = 사건의 근거"라 `/events`가 근거 칩으로 내보내는데, 계획은 의미가 다른 추정 연결(집필 배경·저자)을 같은 관계에 섞으려 했다 → 사건 행에 서신서가 '근거'로 오염될 뻔. 사용자에게 3안 제시, **오버레이** 선택. `books.py`의 `_load_book_events()` lru_cache + `/books`의 `events` 필드로 재구현, inject 스크립트·deploy.sh 단계 없음. → **ADR-0004로 승급**(아래).
  - **슬라이스 1 데이터: Haiku 스크립트 실행 → Opus 직접 부트스트랩.** 이 환경에 `ANTHROPIC_API_KEY`·`NEO4J_PASSWORD`·`anthropic` SDK가 없어 스크립트를 못 돌림. `generate_book_events.py`는 **재생성 레시피 아티팩트**로 남기고, 커밋되는 `books.json`은 라이브 `/api/events`(450건) + Opus 매핑으로 직접 생성하되 **모든 eventId를 실제 집합과 대조(환각 0)**.
  - **커버리지 17/31(54%) — 데이터셋 한계(은폐 아님).** 사건 데이터가 AD57(바울 첫 로마 투옥)에서 끝나, 후기 서신(딤전후·딛·벧전후·요일이삼·유다)·계시록(AD95)·포로귀환(스·느·에)·룻기는 매칭 사건이 없어 빈 배열. UI "추정" 마커 + 빈 칩으로 정직히 노출. 향후 연대 보정 시 자동 채워짐.
  - 슬라이스 3 단순화: 오버레이로 `/books`가 책마다 `events`(id 배열)를 직접 줘서 계획의 `bookToEvents` 역방향 맵 불필요 — `eventById` useMemo로 이름·클릭만 풀면 됨.
  - 칩 색: `#f5a623` 하드코딩 계획 → 규약대로 `TYPE_COLOR.Event`(theme.js) import.

## Learnings
- Do differently next time:
  - **추정·보조 데이터를 의미가 정해진 권위 관계에 넣지 말 것 — 이젠 ADR-0004.** 2번째 반복이었고, 1차(2026-06-15) retro 로그 캡처만으로는 이번 계획이 또 Neo4j 주입을 제안하는 걸 막지 못했다. 새 추정 오버레이는 `book_years_approx`/`book_events`처럼 정적 JSON + 엔드포인트 런타임 오버레이 패턴을 따른다. 계획 단계(fg-ask)에서 "이 데이터가 권위 그래프에 들어가야 하나?"를 먼저 물을 것.
  - **외부 API/SDK·시크릿이 없는 환경에서의 데이터 생성**: 생성 스크립트는 *레시피 아티팩트*로 남기고, 실제 커밋 데이터는 라이브 엔드포인트 + 본 모델로 부트스트랩하되 **생성한 모든 ID를 실제 집합과 대조 검증**(환각 0)하는 패턴이 깔끔. 추정 오버레이라 스크립트 재실행이 다른 매핑을 내도 허용됨(스크립트=레시피, 데이터=일회성 커밋 — `book_context`와 동일).
  - **데이터셋 시간 경계(AD57)가 기능 커버리지의 상한**: 후기 서신·계시록·포로귀환이 빈 칩인 건 버그가 아니라 사건 데이터 한계. 비슷한 "사건 연결" 기능을 또 만들면 같은 cutoff에 막힘 — 먼저 사건 데이터의 시간 범위를 확인할 것.
  - 검증은 `docker compose up -d --build api`로 백엔드 재빌드 후 nginx :8080에서 — `curl /api/books`로 `events` 채워짐 확인 + Playwright로 칩 렌더·클릭→SidePanel 사건 로드.

## Doc updates
- CONTEXT.md promotion: **이미 실행 중 반영됨**(슬라이스 4) — "Book Events (책-사건 연결 오버레이)" 항목 신설 + "Book"·"사건의 근거" 항목 보완. 추가 승급 없음.
- ADR added: **ADR-0004** (추정·보조 데이터는 Neo4j 밖 런타임 오버레이로 유지 — CONTAINS_BOOK 주입 금지). 2번 반복 + retro 로그 캡처 실패가 승급 근거.
