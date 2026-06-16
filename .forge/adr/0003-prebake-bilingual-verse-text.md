# GetBible 절 본문을 빌드타임에 한/영 이중으로 미리 구워 런타임 외부 호출 제거

현재 `frontend/src/getbible.js`가 한국어 성경 본문을 **브라우저에서 런타임에 직접** fetch한다(소비처 3곳: TimelineView 사건 근거, SidePanel 대표구절·인물 성품). 이는 BibleMap의 유일한 런타임 외부 의존성으로, getbible.net의 가용성·지연·CORS에 앱 동작이 묶이고, 실제로 한동안 한 번도 성공하지 못한 잠재 버그였다(retro 2026-06-15 person-trait-verse-text). 그런데 앱이 표시하는 절의 집합은 세 생성 데이터(`event_verses`·`book_context`·`character_traits`)에서 **빌드타임에 완전히 결정**된다. 따라서 빌드 시 getbible에서 본문을 1회 받아 이 데이터에 함께 저장(미리 굽기)하면 런타임 외부 호출을 없앨 수 있다. 사용자 요구로 한국어와 함께 **영어 본문도 저장**하고, 표시 시 한국어/영어 **탭 전환**을 제공한다.

## Considered Options

- **(채택) 빌드타임 베이크 (방안 X)** — getbible에서 ko(`korean`)+en 본문을 빌드 시 받아 기존 3개 데이터에 인라인 저장(`textKo`/`textEn` 등). 소비처는 이미 로드하는 데이터(`/event/{id}/verses` 인라인, Neo4j 노드 속성)에서 본문을 읽고, `getbible.js`와 런타임 fetch는 전부 삭제. 런타임 외부 의존성 완전 제거, 새 엔드포인트·번들 증가 없음, 사건/노드 단위 응답이라 본문 인라인해도 페이로드 안 커짐.
- **(반려) 절 본문 전용 파일 + 백엔드 엔드포인트 (방안 Y)** — 인용 절을 한 파일로 모아 백엔드가 서빙, `getbible.js`는 그 파일을 보도록 변경. 파이프라인은 더 가볍지만 **런타임 fetch(우리 백엔드로)와 getbible.js 인다이렉션이 남아** "완전 제거"가 아니고, 서빙·캐싱 방식을 새로 떠안는다.
- **(반려) 프론트 번들에 JSON 포함** — 번들 비대화. 직전 리팩토링(retro 2026-06-16 refactor-3of4 bundle-code-splitting)의 번들 크기 관리 의도와 충돌.

## Consequences

- `getbible.js` 및 세 소비처의 런타임 fetch 로직이 삭제된다 — **런타임에 api.getbible.net 호출 0건**.
- 절 본문이 한/영 이중(`ko`/`en`)으로 빌드타임에 저장되고, 앱 전역 `verseLang` 상태 + 한국어/영어 탭으로 전환된다(TimelineView·SidePanel 공유 — 한 곳에서 바꾸면 다른 곳도 따라감).
- 빌드 파이프라인에 `backend/scripts/generate_verse_text.py`(getbible ko/en 1회 fetch·캐시 + 약어/범위 해석 + 세 파일에 본문 주입)가 추가된다. `book_context`·`character_traits`는 기존 `inject_*`로 Neo4j 재주입, `event_verses`는 파일 인라인이라 api 재시작으로 `lru_cache`만 무효화.
- 약어→bookOrder 매핑(`BOOK_ABBR_ORDER`)과 ref/범위 파싱이 프론트(`SidePanel.jsx`)에서 빌드타임 Python으로 **단일 출처 이동**한다.
- `event_verses/events.json`은 본문 인라인으로 디스크 용량이 증가하나, `/event/{id}/verses`는 사건 단위 반환이라 개별 응답 크기는 작게 유지된다.
- 영어 번역본은 getbible `kjv`(King James Version)를 기본으로 한다 — 슬러그 한 줄 교체로 WEB/ASV 등 교체 가능. 빌드 첫 실행에서 실제 응답으로 슬러그 가용성을 확인한다(retro 2026-06-15 교훈: 외부 API는 코드 존재가 아니라 실제 호출로 검증).
- 되돌리기 비용: 런타임 fetch 재도입(= getbible.js + 소비처 fetch 복원)은 중간 정도 — 그래서 ADR로 남긴다.
- `CONTEXT.md`의 "Book Context" 항목 중 "Verse 텍스트 자체는 외부 API(getbible.net 등)에서 실시간 fetch" 문장은 이 작업 후 거짓이 된다 → 회고(fg-learn)에서 정정.
