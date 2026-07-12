# 2026-07-12 — 성경 전체 절 적재(정본 절 사전) + event_verses 본문 정규화 (task#167)

- 실행: 메인 세션 직접(워크플로우 미사용 — 결정적 코드/데이터 작업, eco)
- 검증: yes — 골든 diff 전 797 이벤트 응답 바이트 동일 + Playwright 3화면(타임라인 모달·책 페이지·여정) 절 본문 실렌더·콘솔 에러 0 + 창1:1·요3:16·계22:21 스팟체크
- 커밋: `24ca232`

## Plan vs actual

- **What went as planned:**
  - DoD 전부 충족: `data/bible/verses.json` 31,103절(textKo 31,084/textEn 31,102), event_verses 본문 21,336건 제거(9.76MB→2.54MB), `/event/{id}/verses` 응답 불변, 프론트 무변경.
  - 합성 지점은 계획대로 라우트 1곳 + `overlays.bible_verses()`(lru_cache 1회 로드). verse 키 순서(verseID·chapter·verse·textKo·textEn) 유지로 바이트 동일 성립.

- **Divergences:**
  - **장 단위 fetch(≈2,378회) 대신 getbible v2 전체 번역본 단일 파일 2회 fetch.** 계획이 명시한 기존 장 단위 패턴 재사용을 버리고 전체본 엔드포인트(한 13.5MB·영 8.9MB)를 실측 확인 후 채택 — "실패 장 재시도 보고" 요건 자체가 소멸. UA 403 우회·멱등 skip은 재사용.
  - **골든 diff 안전장치(인라인 본문 우선 반영)는 실측 결과 불발동** — getbible 전체본과 기존 인라인 본문 불일치 0건, textKo null 24건도 getbible 한글 사전에 원래 없는 절이라 자연히 null 유지.
  - **계획 밖 1건: `generate_verse_text.py`의 `bake_events`(event_verses 인라인 재주입) 제거.** 남기면 재실행 시 정규화가 되돌아가는 잠복 함정 — link-verses 회고의 "누적 아티팩트 재빌드 함정"과 동형이라 함께 제거(feedback_fix_adjacent_bugs).
  - 골든 diff 표본을 "≥20개(시편 포함)"에서 **전 797건 전수**로 확대 — 시편은 이벤트 보유 책이 아니라 표본 조건이 성립 불가했고, 로컬 전수가 더 싸고 강함.
  - Playwright 시행착오 3회: 앱 인물 slug는 Neo4j slug(`noah_2210`)가 아니라 큐레이션 slug(`noah`), `text=📖` 첫 매치가 헤더 "성경 책 둘러보기" 버튼과 충돌, 비가시 매칭은 `>> visible=true` 필요.

## Learnings

- **Do differently next time:**
  - **응답 보존 리팩토링의 게이트는 "표본 골든"이 아니라 가능하면 전수 골든으로.** 로컬 API 전수 캡처(797건)는 몇 분·무비용인데 보장은 절대적 — 표본 수를 계획 단계에서 고민할 필요가 없었다.
  - **외부 API 대량 fetch 설계 전에 더 굵은 단위 엔드포인트를 1회 실측하라.** 장 단위 2,378회 설계가 전체본 2회로 줄었다(curl 프로브 2회로 확인). "기존 패턴 재사용" 관성보다 상위 단위 존재 확인이 먼저.
  - **본문/데이터를 다른 곳으로 옮기는 정규화는 "옛 위치에 다시 채우는 스크립트"를 반드시 함께 제거하라** — 이번 `bake_events`처럼 재주입 경로가 남으면 정규화가 조용히 되돌아간다. regen 계열 함정 목록에 추가되는 세 번째 사례(load_books 재fetch, generate_event_verses 덮어쓰기, bake_events 재주입).
  - **Playwright로 앱을 몰 때 URL slug는 DB가 아니라 앱(허브 클릭 → location.hash)에서 얻어라.** 큐레이션 slug와 그래프 slug가 다른 앱에서는 DB 조회가 오답을 준다.

## Doc updates

- CONTEXT.md promotion: 「Book Context」 항목의 절 본문 문장 정정 — 사건 근거 절은 이제 인라인이 아니라 정본 절 사전(`data/bible/verses.json`)에서 API 합성(ADR-0015 참조)
- ADR added: ADR-0015 (정본 절 사전 + API 합성 — event_verses 인라인 베이크의 정규화 전환)
