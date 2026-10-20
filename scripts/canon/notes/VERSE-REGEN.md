# VERSE-REGEN — 구절 요소 14장면 재생성 → J1 예측 → 후보 화면 (task 376)

## 고정 절 (2026-10-20 12:29 KST — 생성·J1 예측 전에 적음)

사용자 요청: 375로 바뀐 장면을 다시 생성해 「다음 생성 묶음의 순서」를 끝까지 돌려 본다. 사람 화면은 **후보 화면**(용어집 「장면 고르기」)으로 28화면 이하.
계획 `.forge/plan.md`(1/2 = 생성 → 예측 → 후보 화면 공개, 2/2 = 사람 판정 → 기록·판정 → 현황 페이지).

### 기본값
- 장면 = `params.VERSE_ELEMENT_SCENES` 14개 전부(시글락도 — 묶음을 한 조건으로). 시드 = `REF_EDIT_SEEDS` 8개(11·42·7·23·5·101·202·303). 후보 편집 끔.
- 프롬프트 경로 = 375 규칙: 한 장 모드 칸(`whole_background`)이 있으면 `derive_scene.whole_prompt`, 없으면 `plate_whole_prompt`. 명세는 바꾸지 않는다.
- 판정자 = J1 고정(Sonnet v2 전 문항 + 지물만 Sonnet p2·크롭 2.5배, `judge_items.py predict`). 문구·모델·크롭은 바꾸지 않는다.
- 한 번 실행에 끝까지: `run_night.py all --set verse-regen` = 생성 → 문항 페이지(`verse-regen-pick.html`, J1이 문항을 읽는 곳 — 사람에게는 안 보임) → `predict --task 376` → 후보 화면(`verse-regen-cand.html`).

| 장면 | 제목 · 구절 | 경로 | 인물 |
|---|---|---|---|
| authored-david-ark-jerusalem | 법궤를 다윗 성으로 · 삼하 6:12-15 | plate | david |
| authored-david-gibeon-battle | 기브온 못가 · 삼하 2:12-17 | plate | abner · joab |
| authored-david-hebron-king-judah | 헤브론에서 유다 왕 · 삼하 2:4 | plate | david |
| authored-david-jerusalem-conquest | 시온 산성 · 삼하 5:6-9 | plate | david |
| authored-david-mahanaim-exile | 마하나임 피신 · 삼하 17:24 | plate | david |
| authored-david-nathan-covenant | 나단의 언약 · 삼하 7:12-16 | plate | nathan · david |
| authored-david-returns-jerusalem | 요단을 건너 돌아옴 · 삼하 19:15 | plate | david |
| authored-david-ziklag-base | 시글락 · 삼상 27:6-7 | plate | achish · david |
| authored-samuel-bethlehem-david-anointing | 베들레헴 기름 부음 · 삼상 16:4-13 | plate | samuel · david-boy · jesse |
| authored-saul-endor-medium | 엔돌 · 삼상 28:7-20 | plate | saul-old · samuel · endor-medium |
| authored-saul-gilboa-death | 길보아 · 삼상 31:1-13 | plate | saul-old · saul-armor-bearer |
| authored-david-gath-achish | 가드 미친 체함 · 삼상 21:10-15 | whole | david · achish |
| authored-david-nob-priests | 놉 · 삼상 21:1-9 | whole | ahimelech · david |
| authored-david-ramah-samuel | 라마 · 삼상 19:18 | whole | david · samuel |

### 판정 규칙 (J1 답을 보기 전에 고정)
- **J1 답** = 문항 종류가 지물이면 `J1-prop`, 아니면 `J1`(`judge_learn.j1_answer`). 답 없음(실패 호출)은 「틀림」으로 센다(후보에서 밀리는 쪽 — 안전).
- **후보** = J1이 장면 뜻(moment)을 「맞음」으로 본 시드 중 J1 「틀림」 칸이 가장 적은 시드, 동률이면 시드 목록 앞쪽.
- **되돌림** = J1이 moment를 8시드 전부 「틀림」(`judge_learn.machine_marks`의 reject 정의 그대로).
- **블라인드 표본** = 8시드를 `crc32("<장면>:<시드>")` 순으로 늘어놓아 후보가 아닌 첫 시드(J1 답과 무관한 순서 — 재현됨). 되돌림 장면은 표본 없음.
- 화면(폰 360px, 한 화면 한 질문, 기계 표시 없음):
  - 후보 화면: 후보 큰 그림 + 인물 크롭, 그 장면의 요소 문항(기존 qid·기대 문장)을 눌러 「틀림」 표시, 답 「쓸 만함 / 없음」. 아래 나머지 7시드 작은 그림 — 누르면 그 시드가 후보가 되고 요소 문항을 그 시드로 다시 묻는다(바뀐 사실을 기록).
  - 블라인드 표본 화면: 그 시드 그림 + 요소 문항만(답은 「다음」).
  - 되돌림 화면: 8시드 작은 그림 + 「기계: 장면 뜻이 모두 틀림 → 명세로 돌려보냄」 「동의」 / 살릴 시드를 누름(누르면 그 시드로 후보 화면).
  - 화면 수 = 2 × (14 − 되돌림) + 되돌림 ≤ 28.
- **`판정:` 줄**(2/2에서) — 셋 다면 `판정: 후보 화면 채택`, 하나라도 어기면 `판정: 보류`(어긴 항목 적음):
  1. 되돌림 장면에서 사람이 시드를 살린 수 = 0 (되돌림 장면 0개면 「해당 없음」으로 통과, 그 사실을 적음)
  2. 사람이 기계 후보를 다른 시드로 바꾼 장면 ≤ 되돌림이 아닌 장면 수의 1/4
  3. 블라인드 칸(후보·표본 화면의 요소 문항 답) 기준 J1 잡기 ≥ 0.75 그리고 통과 ≥ 0.75
- 함께 적는 측정값(규칙 아님): 사람 화면 수·걸린 분, 「쓸 만함」 장면 수, 되돌림 장면 수, 믿음 관문 종류별 하한 변화.
