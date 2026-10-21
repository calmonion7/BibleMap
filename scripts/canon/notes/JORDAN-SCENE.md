# JORDAN-SCENE — 장면 구절로 요단 명세 다시 쓰기: 같은 때의 구절 전부로 상황부터 · 바르실래 더함·다윗 칼 뺌 · 문구 8시드 → 시므이 자리는 국소 편집 → 사람 1화면 (task 387)

## 고정 절 (2026-10-21 — 생성·예측 전에 적음)

385 사람 답 「한구절만 하니 상황묘사가 정확히 안되네 / 해당장면에 필요한 구절 모두를 파악하여 장면묘사가 우선」. 그릴링 정정 「시간관점에서 같은 구절만 대상」. 그래서 정본 명세 `scenes/authored-david-returns-jerusalem.json`을 [[장면 구절]]로 다시 썼다 — `verses.quotes` = 장면 구절 8절, 새 칸 `situation`(상황 산문 + 절마다 같은 때인 이유), `moment.why`는 상황 안에서 순간을 고른 이유로 줄임. scripture-reviewer 1층 판정은 `.forge/reports/scripture-words-review.md` 「task 387」 절.

### 장면 구절
| 절 | 들어온 이유(`situation.same_time`) | 그림에 둔 것 |
|---|---|---|
| 19:15 | 왕이 요단에 이르고 유다 족속이 맞으러 와 있음 | 요단 강가 · 유다 무리(crowds[0]) · 다윗 |
| 19:16 | 시므이가 유다 사람과 함께 내려와 이 자리에 있음 | 시므이(S4) · 유다 무리 |
| 19:17 | 베냐민 일천·시바 일행이 요단을 건너 왕 앞에 와 있음 | 베냐민·시바 무리(crowds[2]) |
| 19:18 | **고정한 순간** — 나룻배가 건너가고 왕이 건너려 할 때 시므이가 엎드림 | 나룻배(S1b) · 가족·신복(crowds[1]) · 다윗 · 시므이 엎드림 |
| 19:19 | 19:18과 한 문장 — 엎드린 채 「죄 주지 마옵소서」 | 시므이가 엎드려 빎(S4 「pleading with the king for mercy」) |
| 19:20 | 같은 말의 끝 | (말 속 앞선 걸음은 out) |
| 19:31 | 바르실래가 왕과 「함께 요단에 이르니」 | 바르실래(S5, 다윗 곁 구역 단계) |
| 19:32 | 같은 때 거기 있는 바르실래의 나이 | 「a very old man of eighty」 |

- 빠진 것: 16:5-13(원인) · 19:14(앞선 때 — 가족·신복의 신복은 「본문 밖 · 383 사람 메모」) · 19:21-23(다음 일) · 19:24-30(다른 자리) · 19:39-43(건넌 뒤).
- 다윗: `prop: "none"`(칼은 장면 구절에 없음 · 엔게디 사울 선례), 판 문구 「his hands empty」.

### 장면·시드·경로
- 장면 1 = 요단 귀환, 판 경로(`route_prompt` → `plate_whole_prompt`, 301토큰 ≤ 512). 묶음 `jordan-scene`(`plain_words.py --set jordan-scene`).
- 시드 8개(11·42·7·23·5·101·202·303) · 후보 편집 끔 · 1216×640 · **사다리 없음(r1 한 회차)** — r1 = 고친 정본 그대로.
- 382·385 묶음은 옛 정본·사전을 만든 시점 커밋으로 읽는다(385 = `1ce6720`, 382 = `03b0b07`) — 두 묶음 `check`가 계속 `ok`여야 한다.

### 기계 판정 (claude -p Sonnet)
- **J1**(v2 머리말, 전체·몸 크롭) — 정본 명세 문항(`make_night_page.questions`, wide=false, 정본 얼굴 문항 뺌): 순간 · 배경 · 무리 셋(crowds[0] 유다 · [1] 가족·신복 · [2] 베냐민·시바) · 다윗 자세·지물(「none」 = 빈손)·방향 · 가드.
- **J1-prop**(p2 머리말, 크롭 2.5배) — 지물 칸만, 지물 칸 답은 이쪽.
- **E**(v2 머리말, 전체) — 장면 요소 문항(아래 `elements`): 시므이 엎드려 빎 · 시므이가 다윗 바로 앞 · 아주 늙은 노인이 다윗 곁 · 다윗 손에 칼 없음.
- **W**(v2 머리말, 전체) — 사전 특징 문항: 나룻배(L2) 3 · 요단(L1) 3.
- **O1**(이상한 점) — 기록만.

### 1위·2위
- **틀림 칸** = J1(지물 칸은 J1-prop 답) + E + W에서 「틀림」인 문항 수. **「다윗 바로 앞」(`e.before-david`)은 뺀다.**
- **문구 1위** = 틀림 칸이 가장 적은 시드, 같으면 시드 순서 앞. **문구 2위** = 1위를 뺀 나머지에 같은 규칙.

### 편집 갈래 (문구 1위의 「다윗 바로 앞」이 틀림일 때만)
- 문구 1위가 이미 「다윗 바로 앞」 맞음이면 편집을 건너뛰고 metrics `edit`에 「건너뜀」과 사유를 적는다.
- 바탕 = 문구 1위·2위 두 장. 지시 둘(`edit.arms` — P1은 출발점 = 다윗 발 앞, PROMPTING 27) × klein 시드 1·2·3 = **12장**. 371·386 조리법(작은 크롭 → 1024 klein 편집 → 색 맞춤 → 타원 마스크 안쪽만 되붙임, `gen_local_edit.edit`).
- 바탕마다 크롭(L, T, 변)·마스크 상자는 실행자가 그림을 보고 잡아 **이 절 아래 「편집 상자」 추가분으로 커밋한 뒤** 편집한다(386 회고: 기계 거름 전 커밋).
- 편집본 판정 = 같은 J1·J1-prop·E·W 문항(크롭은 바탕 시드 상자) + 추가 문항 「엎드린 사람이 그림 전체에 한 사람뿐인가?」(`e.one-bowing`).
- **편집 1위** = 「다윗 바로 앞」·「엎드려 빎」·「한 사람뿐」이 모두 맞은 편집본 중 틀림 칸(위 정의, `e.before-david` 뺌)이 가장 적은 장. 같으면 바탕 순서(문구 1위 바탕 먼저) → 지시 순서 → klein 시드 순서. 없으면 「없음」과 사유.

### 사람 화면 1화면 (폰 360px 비공개 Artifact)
- 좌우 블라인드(장면 id 해시): **문구 1위 / 편집 1위**. 편집을 건너뛰었거나 편집 1위가 없으면 **문구 1위 / 문구 2위**.
- 질문 하나 「장면 구절에 맞게 그린 쪽은?」(왼쪽 / 오른쪽 / 둘 다 아님).
- 성경 원문 상자(장면 구절 8절 전부, 19:18 굵게, 스크롤) · 여러 줄 메모칸 · 쉼 뺀 타이머 · 접힌 칸에 r1 8장과 편집 12장 전부(기계 불통과 포함 — 시드·갈래만 표시).
- 사람 답(「판정 문장」)은 `samples/jordan-scene/pick-verdict-387.txt`에 원문 그대로 둔다(루프 검사 꼴 `*387*verdict*`). 화면 대신 대화로 오면 원문을 그 파일 메모에 두고 `source: conversation`으로 적는다.

### `판정:` 규칙
- 사람이 후보 하나(왼쪽/오른쪽)를 고르면 `판정: 장면 채택`, 「둘 다 아님」이면 `판정: 보류`.
- 채택이면 정본 명세 `approved.final`에 고른 그림을 적는다(문구 쪽은 `run_night.py record`와 같은 꼴, 편집본이면 386과 같은 `local-edit` 꼴). 승인 그림 사본은 `samples/jordan-scene/approved-authored-david-returns-jerusalem.png`.
- 보류면 이 노트에 다음 수단을 적는다(같은 문구 A/B는 다시 묻지 않는다 — 다음 수단은 ControlNet 구도 가이드, 따로 계획).

### 측정만 (규칙 아님)
- 문항별 맞힘(385 r2 대비 — 무리 셋·순간·「왕 앞」 0/8) · 바르실래 있음 · 칼 없음 · 나룻배 유지(385 8/8 — 인물·무리가 일곱 덩어리로 늘어 밀려나나) · 편집 갈래별 맞힘 · 토큰 · O1 · 쉼 뺀 사람 시간.

### 명령
- `VENV=~/.local/biblemap-imggen/.venv314/bin/python` · `$VENV batch/plain_words.py <cmd> --set jordan-scene`
  - `one`(시험 1장) · `scene`(r1 8장 생성 + 기계 판정, 무인) · `check`(사본·답 검사 → `ok`) · `edit`(편집 갈래, 상자는 고정 절 추가분) · `cand`(후보 화면) · `record <판정.txt>` · `verdict` · `report`
- 후보 화면 검사: `/opt/homebrew/bin/python3 check_cand_page.py 387 ~/.local/biblemap-imggen/pages/jordan-scene-cand.html`

```json fixed
{
  "seeds": [11, 42, 7, 23, 5, 101, 202, 303],
  "threshold": 6,
  "token_max": 512,
  "revert_plus": 4,
  "levels": ["L1", "L2", "L3"],
  "forbidden": ["pretend", "feign", "feigning", "sacred", "holy", "ceremonial", "symbolic", "ritual", "divine"],
  "no_ladder": true,
  "scenes": {
    "authored-david-returns-jerusalem": {
      "wide": false,
      "word_qids": ["background[0]"],
      "units": [
        {"id": "ferry-boat", "role": "bg", "start": "L2", "judge": "scene",
         "slot": {"path": "stages[1].prompt", "old": "a small flat boat that carries people across a river"}},
        {"id": "jordan", "role": "bg", "judge": "scene",
         "slot": {"path": "stages[0].prompt", "old": "the Jordan river"}}
      ],
      "elements": [
        {"id": "e.shimei-bow", "q": "시므이", "what": "한 사람이 무릎 꿇고 이마를 땅 가까이 대고 엎드려 비는 모양인가?"},
        {"id": "e.before-david", "q": "시므이 자리", "what": "엎드린 사람이 다윗(왼쪽에 서 있는 왕) 바로 앞, 발 앞 가까이에 있나?"},
        {"id": "e.old-man", "q": "바르실래", "what": "아주 늙은 노인(흰 수염·늙은 몸)이 다윗 곁에 서 있나?"},
        {"id": "e.no-sword", "q": "다윗 손", "what": "다윗 손에 칼이 없나(빈손인가)?"}
      ],
      "before_qid": "e.before-david",
      "edit_extra": [
        {"id": "e.one-bowing", "q": "엎드린 사람 수", "what": "엎드린 사람이 그림 전체에 한 사람뿐인가?"}
      ],
      "edit_required": ["e.before-david", "e.shimei-bow", "e.one-bowing"]
    }
  },
  "edit": {
    "klein_seeds": [1, 2, 3],
    "arms": {
      "P1": "Starting right at David's feet: on the ground directly in front of the standing king's feet, one man kneels with his forehead touching the ground and his two hands pressed together, begging. Keep everything else exactly the same: the standing king, the other people, the river, the boat, the lighting and the same soft pencil and colored-pencil illustration style.",
      "P2": "Add a single man bowed down low right before the king's feet, face to the earth, palms joined in a plea for mercy, close against the king. Keep everything else exactly the same: the standing king, the other people, the river, the boat, the lighting and the same soft pencil and colored-pencil illustration style."
    }
  }
}
```

## 고정 절 추가분 — 편집 상자 (2026-10-21, r1 기계 판정 뒤 · 편집 전)

r1 결과: 문구 1위 **s101** · 2위 **s42**(틀림 칸 4 · 6). s101의 「다윗 바로 앞」이 틀림(r1 8장 모두 0/8) → 편집 갈래.
두 바탕 모두 원래 엎드린 사람이 다윗에게서 먼 오른쪽 무리 앞에 있다(s101 x 635~780 · s42 x 755~890).

- **s101**: 크롭 (150, 0, 640) — 다윗 몸(x 150~223)부터 원래 엎드린 사람까지 한 크롭에 든다. 마스크 상자 (215, 420, 800, 640) — 다윗 발 앞에서 원래 엎드린 사람까지 덮어, klein이 엎드린 사람을 다윗 발 앞으로 옮길 수 있게 한다(덮인 무리 다리는 「Keep … the other people」에 맡김).
- **s42**: 크롭 (150, 0, 640) — 원래 엎드린 사람은 크롭 밖(640px에 다윗과 함께 들지 않음). 마스크 상자 (225, 460, 540, 635) — 다윗 발 앞 풀밭만. 엎드린 사람이 둘로 남을 수 있다 → 「한 사람뿐」 문항이 거른다.

```json edit-boxes
{"bases": {"101": {"crop": [150, 0, 640], "box": [215, 420, 800, 640]},
           "42": {"crop": [150, 0, 640], "box": [225, 460, 540, 635]}}}
```
