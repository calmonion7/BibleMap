# 정본 절 사전(data/bible/verses.json) + API 합성 — event_verses 인라인 본문의 정규화 전환

event_verses 오버레이는 절 본문을 인라인 저장(ADR-0003)해 9.3MB까지 커졌고, 절 인스턴스 21,336개 중 유니크는 16,918개로 본문 중복이 누적됐다. task#167에서 성경 전체 31,103절(한국어 `korean` + 영어 `kjv`)을 빌드타임 프리베이크한 **정본 절 사전** `data/bible/verses.json`(verseID `BBCCCVVV` → `{textKo, textEn}`, `generate_bible_text.py`)을 신설하고, `event_verses/events.json`은 **verseID 참조만** 남기며(9.76MB→2.54MB), `/event/{id}/verses`가 응답 시 사전에서 본문을 합성하도록 바꿨다(`overlays.bible_verses()` lru_cache 1회 로드, 응답은 골든 diff 전 797건 바이트 동일로 검증).

ADR-0003의 목표(런타임 외부 fetch 0)는 그대로 유지된다 — 바뀐 것은 *사건 근거 절* 본문의 저장 위치(인라인 → 정본 사전)뿐이다. 소량 인라인 절(책 keyVerse, 인물 traits·소개·관계 인용절)은 작고 안정적이라 인라인 유지(비정규화 잔존은 의도된 경계).

## Considered Options

- **(채택) 정본 사전 + API 합성** — 본문 단일 출처, 이벤트당 절 추가·수정 시 참조만 관리, 향후 "성경 읽기/장 열람"류 기능의 데이터 기반 확보. 대가: 전권 사전 +10.3MB(순증 ~3MB)와 API 합성 한 단계.
- **(반려) 인라인 유지 + 중복만 감수** — 파일이 계속 커지고(이벤트·절 추가마다 중복 가속), 동일 절 본문의 수정이 N곳 산탄이 됨.
- **(반려) Neo4j Verse 노드** — ADR-0004 원칙(그래프는 구조, 대용량 본문은 오버레이) 위배.

## Consequences

- `generate_verse_text.py`의 `bake_events`(event_verses 인라인 재주입)는 **제거됨** — 되살리면 정규화가 조용히 되돌아가는 재주입 함정이 된다. 절 본문 공급은 이제 `generate_bible_text.py`(멱등, 전체본 2회 fetch) 몫.
- `generate_event_verses.py` 재빌드는 원래 본문 없는 구조를 만들므로 정규화와 자연 정합(`preserve_non_theographic`의 비-theographic 엔트리 보존 역할은 유지).
- API 응답 계약은 불변(verse 키 순서 verseID·chapter·verse·textKo·textEn 포함) — 합성 코드를 만질 때 이 순서가 바이트 동일성의 전제임에 유의.
- 기존 textKo null 24절은 getbible 한글 사전 자체 공백으로 사전에서도 null — 응답 동작 동일.
