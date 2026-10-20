# JORDAN-MOMENT — 요단 귀환 순간 다시 정하기: 19:18 전체(시므이 엎드림까지) · 사전 「엎드리다」를 단위로 · 8시드 사다리 → 사람 1화면 (task 385)

## 고정 절 (2026-10-21 — 생성·예측 전에 적음)

383 사람 메모 「다윗의 가족들, 신하들이 강가에서 나룻배를 타려고 대기중인데 시므이가 와서 엎드리는 장면이야」 — 낱말은 8/8 맞았는데 「둘 다 아님」이었다. 원인은 낱말이 아니라 **순간 범위**(두 겹 판정의 1층)로 본다. 그래서 정본 명세 `scenes/authored-david-returns-jerusalem.json`의 순간을 「19:15 · 19:18 전반」에서 **19:18 전체**로 옮기고(scripture-reviewer 1층 판정 뒤 — `.forge/reports/scripture-words-review.md` 「task 385」 절), 그 순간을 사전 단위로 다시 그린다.

### 장면·시드·경로
- 장면 1 = 요단 귀환(`authored-david-returns-jerusalem`), 판 경로(`derive_scene.route_prompt` → 칸 없음 → `plate_whole_prompt`).
- 시드 = 382와 같은 8개(11·42·7·23·5·101·202·303), 후보 편집 끔. 1216×640.
- **r1 = 고친 정본 그대로**: 정본의 단위 자리에 시작 단계 삽입꼴을 이미 써 두었다(`render(시작 단계) == 정본`). r2·r3·따로 시험만 사본(`samples/jordan-moment/specs/<회차>/`).
- A(기존 그림 비교 기준)는 없다 — 순간이 바뀌어 옛 그림과 견줄 수 없다. J1 문항은 고친 정본 명세에서 바로 만든다(`make_night_page.questions`, 379와 같은 방향 문항 꼴 wide=false, 정본 얼굴 문항 뺌).

### 단위 표
| 단위 | 등급 | 시작 단계 | 묻는 판정자 | 자리(정본 첫 언급) | 근거 |
|---|---|---|---|---|---|
| `bow-down` 엎드리다 | 핵심 | L2 | J1 머리말(v2, 전체 — 시므이는 cast가 없어 몸 크롭 없음) | `stages[5].prompt`(S4 시므이) 「a person kneeling low with the face toward the ground」 | 382 규칙(핵심 = L2 시작), verified 없음 |
| `ferry-boat` 나룻배 | 배경 | L2 | J1 머리말(v2, 전체) | `stages[1].prompt`(S1b) 「a small flat boat that carries people across a river」 | verified L2 조건부(with 요단) — 그 단계에서 시작 |
| `jordan` 요단 | 배경 | L1 | J1 머리말(v2, 전체) | `stages[0].prompt`(S1) 「the Jordan river」 | verified L1 조건부(with 나룻배) |

- **삽입꼴**: 382와 같다 — 그 단계 `look.en` 글자 그대로, 첫 글자 소문자, 끝 마침표 뗌, 문장 사이 「. 」→「, 」.
- **특징 문항**: 사전 `criteria.features` 전부(뺄 문항 없음 — 요단 「사람들이 건너는 강인가?」는 이 순간에 베냐민 무리가 요단을 밟고 건너왔으므로(19:17) 묻는다).
- **낱말 칸**(`word_qids`): J1 `background[0]`(요단 강가). 「다른 칸 지킴」에서 뺀다.
- **지워지는 정본 낱말**(PROMPTING 26 — 자리 교체는 그 자리의 정본 꾸밈말을 지운다): r1은 정본 그대로라 없음. 단계를 올리면 그 자리 삽입꼴이 통째로 바뀐다.
  - 나룻배 L2→L3: 「small」「carries people across a river」가 빠지고 「narrow, flat wooden … a few people … a boatman … long pole」이 들어온다.
  - 엎드리다 L2→L3: 주어 「a person」과 「low」「with the face toward the ground」가 빠지고 「kneeling with the back bent so the forehead nearly touches the ground, both hands rest on the ground in front」가 들어온다(주어는 앞의 「Shimei the son of Gera」가 맡는다).
  - 요단 L1→L2: 「the Jordan river」의 이름이 빠지고 「a wide river winding between flat banks」가 들어온다(이름은 S2c·S3의 「the Jordan」이 남는다).

### 사다리 (382와 같음)
- 회차: **r1** → **r2·r3**(단계 올리기) → 따로 시험. **B2는 하지 않는다**(PROMPTING 26 — 다시 시험하지 않음).
- **문턱**: 단위 특징 문항이 전부 맞은 시드가 8개 중 **6개 미만**이면 그 단위만 한 단계 올려 같은 8시드로 다시 그린다.
- **예산**: 파생 프롬프트 **512토큰** 초과면 핵심 먼저, 같은 등급은 단위 표 순서(A가 없어 A 틀린 장 수 대신). 못 받은 단위는 **상한**.
- **따로 시험**: 함께 올린 단위가 틀리면 그 단위만 같은 단계로 올린 사본 8장 → 맞으면 **밀어냄(낱말끼리)**, 틀리면 다음 단계.
- **L3에서도 틀리면 문구 한계** · **되돌림**: 다른 칸(J1 틀림, 낱말 칸 제외) 8시드 합이 직전 회차보다 **+4를 넘게** 나빠지면 그 회차를 되돌리고 올린 단위는 **밀어냄(다른 칸)**.
- **맞은 단계**: 그 회차에 바뀐 단위가 하나뿐이면 **확정**, 여럿이면 **조건부**(`with`). r1은 세 단위가 함께라 조건부.
- **사다리 끝** = 되돌리지 않은 마지막 회차(따로 시험 회차 제외) = **최종**.
- 최대 약 40장(r1 8 + r2·r3 각 8 + 따로 시험), 무인.

### 1위·2위·사람 화면
- **장면 낱말 맞힘** = 세 단위 특징 문항이 **모두** 맞은 시드 수(/8).
- **1위** = 특징 문항을 다 맞은 시드 중 J1 틀림 칸(지물 칸은 J1-prop 답)이 가장 적은 시드, 같으면 시드 순서 앞. 다 맞은 시드가 없으면 맞은 특징 문항 수가 가장 많은 시드 중에서 같은 규칙. **2위** = 1위를 뺀 나머지에 같은 규칙.
- **사람 화면 1화면**(폰 360px 비공개 Artifact): 최종 회차 1위·2위를 블라인드 좌우(장면 id 해시로 고정). 질문 하나 「굵은 절에 맞게 그린 쪽은?」(왼쪽 / 오른쪽 / 둘 다 아님). 성경 원문 상자(19:14-18, 19:18 굵게·스크롤), 여러 줄 메모칸, 쉼 뺀 타이머, 접힌 칸에 최종 회차 8장 전부(기계 불통과 포함 — 시드 번호만 표시).
- 사람 답(「판정 문장」)은 `samples/jordan-moment/pick-verdict.txt`에 원문 그대로 둔다.

### `판정:` 규칙
- 사람이 후보 하나(왼쪽/오른쪽)를 고르면 `판정: 순간 채택`, 「둘 다 아님」이면 `판정: 보류`.
- 채택이면 정본 명세 `approved.final`에 고른 그림을 적고(`run_night.py record`와 같은 꼴), 정본 `route_prompt`가 최종 회차 프롬프트와 글자까지 같게 둔다(최종이 r2·r3이면 그 사본을 정본으로).
- 판정과 상관없이 사다리가 「맞음」으로 멈춘 단위는 사전 `verified_level`에 규칙 7대로 적는다(이 묶음 단위만 — 다른 묶음이 적은 그림 증거는 그대로).

### 측정만 (규칙 아님)
- 단위마다 멈춘 단계와 사유 · 나룻배 맞힘(382 r1 8/8 대비) · J1 틀림 합 · 회차별 토큰 · 이상한 점(O1, 기록만) · 쉼 뺀 사람 시간.

### 명령
- `VENV=~/.local/biblemap-imggen/.venv314/bin/python` · `$VENV batch/plain_words.py <cmd> --set jordan-moment`
  - `one`(시험 1장) · `ladder`(r1 → r2·r3·따로 시험, 무인) · `check`(회차 사본 검사 → `ok`) · `cand`(후보 화면) · `record <판정.txt>` · `verdict` · `lexicon` · `report`
- 후보 화면 검사: `/opt/homebrew/bin/python3 check_cand_page.py 385 ~/.local/biblemap-imggen/pages/jordan-moment-cand.html`

```json fixed
{
  "seeds": [11, 42, 7, 23, 5, 101, 202, 303],
  "threshold": 6,
  "token_max": 512,
  "revert_plus": 4,
  "levels": ["L1", "L2", "L3"],
  "forbidden": ["pretend", "feign", "feigning", "sacred", "holy", "ceremonial", "symbolic", "ritual", "divine"],
  "scenes": {
    "authored-david-returns-jerusalem": {
      "wide": false,
      "word_qids": ["background[0]"],
      "units": [
        {"id": "bow-down", "role": "core", "judge": "scene",
         "slot": {"path": "stages[5].prompt", "old": "a person kneeling low with the face toward the ground"}},
        {"id": "ferry-boat", "role": "bg", "start": "L2", "judge": "scene",
         "slot": {"path": "stages[1].prompt", "old": "a small flat boat that carries people across a river"}},
        {"id": "jordan", "role": "bg", "judge": "scene",
         "slot": {"path": "stages[0].prompt", "old": "the Jordan river"}}
      ]
    }
  }
}
```

## 결과 — 무인 생성·사다리·후보 화면 (2026-10-21, task 385 S3·S4)

- 시험 1장(r1 s11): 경로 정상, 특징 9문항 중 8 맞음(엎드리다 「왕 앞에서 낮춘 모양인가?」 틀림).
- **r1**(정본, 263토큰): 장면 낱말 0/8 · 엎드리다 **0/8** · 나룻배 **8/8**(382 r1 8/8과 같음 — 인물·무리가 넷으로 늘어도 안 밀려남) · 요단 8/8 · 다른 칸 틀림 합 46.
  - 엎드리다 문항별: 무릎 꿇음 7/8 · 이마 땅 가까이 7/8 · **왕 앞에서 낮춤 0/8** — 자세는 그려지는데 다윗 앞 자리가 안 잡힌다(문구가 아닌 배치 문제로 보임).
  - J1 칸: 무리 셋 거의 다 틀림(유다 0/8·가족신복 1/8·베냐민 0/8 맞음), 순간 0/8 맞음, 다윗 자세 3/8·지물 1/8 맞음.
- **r2**(엎드리다 L3만 올림, 274토큰): 엎드리다 **5/8**(문턱 6 미만) · 나룻배 8/8 · 요단 8/8 · 다른 칸 틀림 45(되돌림 아님).
- **사다리 끝 = r2** · 단위 멈춤: 엎드리다 L3 **문구 한계** · 나룻배 L2 **맞음(조건부, with 엎드리다·요단)** · 요단 L1 **맞음(조건부, with 엎드리다·나룻배)**. r3·따로 시험 없음(올릴 단위 없음). 모두 16장.
- 회차 사본 검사 `plain_words.py check --set jordan-moment` → `ok` · 382 묶음 `check` → `ok`(옛 정본·사전 고정 읽기).
- **후보 화면 1화면**: 최종 r2 1위 s101 · 2위 s5(좌 s5 · 우 s101 — 장면 id 해시) · 접힌 칸 r2 8장. `check_cand_page.py` 통과(360·1280px 가로 넘침 0 · 19:18 굵게 · textarea · 타이머).
  - 비공개 Artifact: https://claude.ai/artifact/K5CJe53Y4V2hqdMjZcvMwY
- 사람 답 대기 — 「판정 문장」을 `samples/jordan-moment/pick-verdict.txt`에 두고 `record` → `verdict` → (채택이면 approved.final·정본 = r2 사본) → `lexicon`.
