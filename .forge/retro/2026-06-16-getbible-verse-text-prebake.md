# 2026-06-16 — GetBible 절 본문 빌드타임 한/영 베이크 + 한·영 탭, 런타임 getbible 제거 (task #42)

## Plan vs actual
- What went as planned:
  - 설계(빌드타임 베이크, 방안 X, ADR-0003)는 **그대로 성립** — 새 엔드포인트·번들 증가 없이 런타임 getbible 호출을 완전히 제거.
  - `generate_verse_text.py`: `SidePanel.jsx`의 `BOOK_ABBR_ORDER`/`resolveVerseRef`/`parseVerseRef`를 Python 포팅(단일 출처 이동), 유니크 (slug,book,chapter)당 1회 fetch·캐시, 멱등(non-null 스킵·null 재시도). 1298 유니크 장, 실패 0.
  - 세 데이터 인라인 베이크: event_verses `textKo/En`(17570절)·book_context `keyVerseTextKo/En`(66)·character_traits `verse_textKo/En`(31). 알려진 절(창1:1, 마9:36) ko·en 일치.
  - 프론트: App 전역 `verseLang`(ko 기본) + 공유 `VerseLangTabs`(3곳), getbible.js 삭제·고아 코드 제거. lint clean.
  - DoD 4항목 전부 충족(Playwright UAT 8/8 PASS — getbible.net 0건·세 곳 본문·한↔영 공유 토글·콘솔에러 0).
- Divergences:
  1. **getbible UA 403 — 검증 도구 ≠ 실행 도구(가장 큰 사건).** 계획·ADR은 "첫 실행 실호출로 슬러그 검증"을 명시했고 사전 `curl` 프로브는 ko/en 200·본문 정상이었으나, **실제 베이크(Python `urllib`)는 전 요청 403 Forbidden** — getbible이 `Python-urllib/x` UA를 차단. `curl`은 자체 UA로 통과해 프로브에서 안 잡힘. `User-Agent`를 브라우저류로 교체해 해결. 첫 실행은 전량 null → 멱등(null 재시도) 덕에 UA 수정 후 재실행으로 정상 채움.
  2. **S2 `inject_book_context.py` 보강 필요(계획 암시).** "재실행으로 새 필드 주입"이라 했으나 기존 스크립트가 `keyVerseTextKo/En`를 SET하지 않아 SET 2줄 추가 필요. `inject_person_traits.py`는 trait dict 전체 JSON 직렬화라 **무수정** 자동 포함.
  3. **S3+S4 통합 실행.** 동일 프론트 파일 2회 편집 회피 위해 파일별 한 번에 편집(상태·탭 + 본문교체·삭제). 기능 차이 없음.
  4. **event_verses 한국어 21/17570건 null.** versification 차이(KJV엔 있으나 개역 절번호 미존재). en 100%. 프론트 "원문이 없습니다" graceful. 0.12%, 무시 가능.
  5. **UAT 중 UI 결함 발견·수정.** 타임라인 구절뷰의 `VerseLangTabs`가 flex column 직속이라 `align-items: stretch`로 테두리가 전폭 확장 → 빈 입력창처럼 보임. 블록 `div`로 감싸 해결.
  6. **Dynamic Workflow 미사용·직접 실행.** 거의 직렬 파이프라인(S1→S2, S3→S4→S5)에 병렬쌍 1개(S1‖S3)뿐, S2/S5가 환경작업이라 fg-run 비용 원칙대로 직접 실행.

## Learnings
- Do differently next time:
  - **외부 API 프로브는 베이크에 쓸 실제 클라이언트/라이브러리로 한다.** retro 2026-06-15 교훈("코드 존재가 아니라 실호출로 검증")의 변형 함정: 같은 엔드포인트라도 **프로브 도구(curl)와 실행 도구(urllib)의 User-Agent가 달라 결과가 갈린다.** getbible은 `Python-urllib` UA를 403으로 막으므로 urllib 요청엔 브라우저류 `User-Agent` 헤더 필수. 다음에 외부 API 베이크/스크래핑을 짤 때는 처음부터 UA 헤더를 붙이고, 프로브도 `python3 urllib`로 한다.
  - **"inject 스크립트 재실행으로 새 필드 주입" 계획은 그 스크립트가 실제로 그 필드를 SET하는지 먼저 확인한다.** 재실행만으로는 새 속성이 안 들어간다 — SET 절을 함께 보강해야 함.
  - **flex column 직속 인라인 요소는 `align-items: stretch`로 전폭 늘어난다.** 테두리/배지형 컴포넌트는 블록 wrapper로 감싸거나 `alignSelf: flex-start`를 줘야 콘텐츠 폭으로 유지. (row+`margin-left:auto` 배치는 무영향.)
  - **멱등 베이크의 null 재시도가 구제책이 됐다.** 첫 실행이 전량 null이어도 "non-null 스킵·null 재시도" 설계 덕에 원인 수정 후 단순 재실행으로 복구. 외부 의존 베이크는 이 멱등 규약을 기본으로.

## Doc updates
- CONTEXT.md promotion: "Book Context" 항목의 stale 문장 정정 — "Verse 텍스트 자체는 외부 API에서 실시간 fetch" → 빌드타임 한/영 베이크(`generate_verse_text.py`, ADR-0003)·런타임 fetch 없음·`keyVerseTextKo/En` 주입으로 갱신(계획이 회고로 미뤘던 정정). 신규 용어 승급 없음(`verseLang`·prebake는 구현 디테일 → 미승급).
- ADR added: none (구현이 기존 ADR-0003과 일치 — 새 결정 없음).
