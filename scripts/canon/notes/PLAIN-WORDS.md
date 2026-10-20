# PLAIN-WORDS — 성경 낱말 사전으로 구절을 이해하고 다시 쓴 명세 → 단계 올리기 → 쉬운 말(B2) → 기존 그림과 기계 비교 → 사람 후보 화면 (task 382·383)

## 고정 절 (2026-10-20 — 생성·예측 전에 적음)

질문은 하나다: **「장면 묘사를 구절을 제대로 이해해서, 더 자세히, 어린아이도 알아듣게 쓰면 그림이 좋아지는가」**. 사전은 `data/scripture_words/words.json`(task 381), 낱말 판정은 사전 `criteria.features`를 모든 회차 그림에 같은 말로 묻는다(회차 명세 글로 묻지 않음 — 자기 문구로 자기를 재는 순환을 피함).

### 장면·시드·기준선
- 장면 4 = 아래 ```json fixed``` `scenes`. 시드 = 376과 같은 8개(11·42·7·23·5·101·202·303), 후보 편집 끔.
- **A(0회차)** = 이미 있는 그림과 J1 답을 그대로 쓴다(다시 그리지 않음): 베들레헴·요단 귀환 = spec-regen(379), 놉·가드 = verse-regen(376). 2026-10-20 fg-ask 확인 — 4장면 모두 저장된 프롬프트가 지금 명세 `route_prompt`와 글자까지 같고, C2가 정본 명세를 그대로 지킨다.
- 경로 = `derive_scene.route_prompt`(칸 있으면 whole, 없으면 plate). 회차 사본 = `samples/plain-words/specs/<회차>/<장면>.json`(`r1`·`r2`·`r3`·`iso-<회차>-<단위>`·`b2`).

### 단위 표 (사전으로 순간 절을 다시 읽음)
| 장면 | 순간 절 | 핵심 단위(L2 시작) | 배경 단위(L1 시작) | 이해 어긋남(지금 명세) |
|---|---|---|---|---|
| 베들레헴 | 삼상 16:13 | 기름 뿔 `oil-horn` | — | `small horn of oil` — 짐승 뿔이라는 뜻이 빠짐 |
| 요단 귀환 | 삼하 19:15 · 19:18 전반 | 나룻배 `ferry-boat` | 요단 `jordan` | `beside a river` — 강 이름 없음. 「엎드리다」(시므이, 19:18 후반)는 명세가 순간 밖으로 정해 단위 아님 |
| 놉 | 삼상 21:9 | 보자기에 싸이다 `wrapped-in-cloth` | 에봇 `ephod` · 진설병 `showbread` | 칼 크기 `huge`는 본문 밖(저작) — 사전 문구가 대신함 |
| 가드 | 삼상 21:13 후반 | 대문짝에 그적거리다 `scrawl-door` · 침을 수염에 흘리다 `drool-beard` | — | `feigning madness`를 따로 그리라 함 → 「미친 체」는 그릴 수 없는 낱말(`drawable:false`) — 이름 문구를 빼고 표지 둘로 잰다 |

- **자리**: 단위마다 그 단위를 **처음 소개하는 명사구 한 곳**(경로 프롬프트 안 첫 언급)을 바꾼다. 뒤 언급(「the ferry boat steady」「the bowed head」 같은 되짚음)은 그대로 둔다. 그 밖의 문구와 순서도 그대로(PROMPTING 19).
- **삽입꼴**: 그 단계 `look.en`을 글자 그대로 넣되, 첫 글자를 소문자로, 끝 마침표를 떼고, 문장 사이 「. 」를 「, 」로 잇는다(명사구 자리에 들어가게). 낱말은 하나도 바꾸지 않는다.
- **특징 문항**: 사전 `criteria.features` 전부. 단, 순간 밖 내용을 묻는 문항은 미리 뺀다(`skip`, 사유는 json) — 그대로 두면 늘 「틀림」이고, 사다리가 L3까지 올라 순간과 부딪히는 문구(진설병 L3 「제사장이 떡을 건넴」)를 그림에 넣는다.
- **묻는 판정자**: 지물(`prop`) = J1-prop 머리말(p2, Sonnet, 쥔 인물 몸 크롭 2.5배) · 동작(`act`) = J1 머리말(v2, Sonnet, 전체 + 그 인물 몸 크롭) · 장면 사물(`scene`) = J1 머리말(v2, 전체만). 머리말은 그대로, 문항만 「기대: <특징 문항>」.
- **낱말 칸**(`word_qids`): J1 칸 중 낱말 자체를 묻는 칸. 「다른 칸 지킴」에서 뺀다.
- **J1 문항**: 모든 회차 그림에 A 페이지(376·379 `*-pick.html`)의 문항 글을 그대로 묻고 크롭만 그 그림 상자로 잡는다(정본 명세 → `make_night_page.questions`, A 과제와 같은 방향 문항 꼴). 가드 `figures[0].pose` 한국어 설명은 A 뒤에 정본에서 「…침을 수염에 흘린다」로 바뀌었지만(프롬프트 밖 칸) A와 같은 말로 묻는다. 4장면 모두 A 페이지와 문항·크롭이 같음을 `predict-a`가 단언한다.
- **A 답**: J1·J1-prop·O1은 376·379 답을 그대로 옮기고(같은 판정자·같은 문항), 특징 문항만 새로 묻는다.

### 사다리 (단계 올리기 — 남는 실패에만)
- 회차 순서: **r1**(사전 명세 — 위 단위 표 넷을 한 번에: 묶음 자리·표지·시작 단계·이해 어긋남) → **r2·r3**(단계 올리기) → 따로 시험 → **b2**(쉬운 말 다시 쓰기). 회차 안에서 원인을 나누지 않는다(PROMPTING 22).
- **문턱**: 단위 특징 문항이 전부 맞은 시드가 8개 중 **6개 미만**이면 그 단위만 한 단계 올려 같은 8시드로 다시 그린다. 다시 그리는 것은 회차마다 올릴 단위가 남은 장면뿐이다.
- **예산 순서**: 파생 프롬프트가 **512토큰**(Z-Image 인코더 상한, 채팅 틀 포함)을 넘으면 핵심 단위가 먼저 받고, 같은 등급끼리는 A에서 틀린 장 수(단위 특징 전부 맞지 않은 시드 수)가 많은 단위가 먼저다. 예산을 못 받은 단위는 그 단계에서 **상한**으로 멈춘다.
- **따로 시험**: r2·r3에서 다른 단위와 **함께 올린** 단위가 틀리면, 다음 단계로 가기 전에 그 단위만 같은 단계로 올린 사본(나머지는 직전 회차 단계)을 한 번(8장) 더 그린다. 맞으면 **밀어냄(낱말끼리)** 으로 그 단계에서 멈추고, 틀리면 다음 단계로 올린다. (r1은 처치 회차라 따로 시험이 없다.)
- **L3에서도 틀리면** **문구 한계**로 멈춘다.
- **되돌림**: 단계를 올린 회차에서 그 장면의 다른 칸(J1 틀림, 낱말 칸 제외) 8시드 합이 직전 회차보다 **+4를 넘게** 나빠지면 그 회차를 되돌리고(그 장면 단계는 직전 회차로) 올린 단위를 **밀어냄(다른 칸)** 으로 멈춘다(PROMPTING 10).
- **맞은 단계**: 그 회차에 그 장면에서 바뀐 단위가 그것 하나뿐이면 **확정**, 여럿이면 **조건부**(`with` = 함께 바뀐 단위). r1도 같은 셈(장면에 단위가 하나면 확정).
- **사다리 끝** = 장면마다 되돌리지 않은 마지막 회차(r1·r2·r3 중 — 따로 시험 회차는 제외).

### B2 (쉬운 말 다시 쓰기, 마지막 회차)
- 사다리 끝 사본 위에서 장면 문장 전체를 아이 눈높이로 다시 쓴다: 짧은 문장, 구체적인 낱말, 「누가 · 무엇을 들고 · 무엇을 하며 · 어디를 보나」 순서. 본문 앞뒤 문맥의 세부를 더해 **더 자세히**. 추상어 금지 목록은 사전과 같다(`pretend, feign, feigning, sacred, holy, ceremonial, symbolic, ritual, divine`).
- 낱말 자리는 사다리가 고른 단계 삽입꼴을 글자 그대로 둔다. 근거 `verse` 칸은 바꾸지 않는다. 512를 넘으면 중복만 뺀다.

### 1위·최종·사람 화면
- **장면 낱말 맞힘** = 그 장면 단위 특징 문항이 **모두** 맞은 시드 수(/8).
- **1위** = 특징 문항을 다 맞은 시드 중 J1 틀림 칸(지물 칸은 J1-prop 답)이 가장 적은 시드 — 같으면 시드 순서(11·42·7·23·5·101·202·303) 앞. 다 맞은 시드가 없으면 맞은 특징 문항 수가 가장 많은 시드 중에서 같은 규칙.
- **최종** = 사다리 끝과 B2 중 장면 낱말 맞힘이 더 많은 쪽, 같으면 B2.
- **사람 화면** = 장면마다 1화면, 모두 4화면(폰 360px 비공개 Artifact): A 1위와 최종 1위를 블라인드로 좌우에 둔다(좌우는 장면 id 해시로 고정). 질문 하나 「굵은 절에 더 맞게 그린 쪽은?」(왼쪽 / 오른쪽 / 둘 다 아님), 성경 원문 상자(순간 절 굵게), 여러 줄 메모칸, 쉼 뺀 타이머.

### `판정:` 규칙 (3/3에서 적용 — 셋 다 지키면 `판정: 낱말 사전 채택`, 하나라도 어기면 `판정: 보류 (어긴 규칙 …)`)
1. **낱말 맞힘**: 최종의 장면 낱말 맞힘 − A의 장면 낱말 맞힘 ≥ 3/8인 장면이 4장면 중 **2개 이상**.
2. **다른 칸 지킴**: 최종의 J1 틀림 칸 합(4장면 × 8시드, 낱말 칸 제외) ≤ A 합 + 4.
3. **사람**: 4화면 중 최종을 고른 화면이 **3개 이상**.

### 측정만 (규칙 아님)
- **1회차 대 A**(이해하고 쓰기의 효과 — 사용자의 처음 질문): 규칙 1과 같은 셈.
- 단위마다 멈춘 단계와 사유(맞음 확정/조건부 · 문구 한계 · 상한 · 밀어냄(낱말끼리/다른 칸)), 사다리 대 B2 귀속, 회차별 토큰 수, 이상한 점(O1) 기록, 쉼 뺀 사람 시간.

### 명령
- 생성·예측·사다리: `$VENV batch/run_night.py <cmd> --set plain-words` = `$VENV batch/plain_words.py <cmd>` (`predict-a` · `round <회차>` · `ladder` · `b2` · `cand` · `check`).
- **회차 사본 검사(C3)**: `~/.local/biblemap-imggen/.venv314/bin/python batch/plain_words.py check` → `ok`

```json fixed
{
  "seeds": [11, 42, 7, 23, 5, 101, 202, 303],
  "threshold": 6,
  "token_max": 512,
  "revert_plus": 4,
  "levels": ["L1", "L2", "L3"],
  "forbidden": ["pretend", "feign", "feigning", "sacred", "holy", "ceremonial", "symbolic", "ritual", "divine"],
  "scenes": {
    "authored-samuel-bethlehem-david-anointing": {
      "a": {"dir": "spec-regen", "task": 379},
      "word_qids": ["figures[0].prop"],
      "units": [
        {"id": "oil-horn", "role": "core", "judge": "prop", "who": "samuel",
         "slot": {"path": "stages[1].prompt", "old": "one small horn of oil"}}
      ]
    },
    "authored-david-returns-jerusalem": {
      "a": {"dir": "spec-regen", "task": 379},
      "word_qids": ["background[0]"],
      "units": [
        {"id": "ferry-boat", "role": "core", "judge": "scene",
         "slot": {"path": "stages[1].prompt", "old": "a wooden ferry boat"}},
        {"id": "jordan", "role": "bg", "judge": "scene",
         "slot": {"path": "stages[0].prompt", "old": "a river"}}
      ]
    },
    "authored-david-nob-priests": {
      "a": {"dir": "verse-regen", "task": 376},
      "word_qids": ["background[1]", "figures[0].prop", "figures[1].prop"],
      "units": [
        {"id": "wrapped-in-cloth", "role": "core", "judge": "prop", "who": "ahimelech",
         "slot": {"path": "figures[0].gesture.en", "old": "the huge cloth-wrapped sword"}},
        {"id": "ephod", "role": "bg", "judge": "scene",
         "slot": {"path": "whole_background.en", "old": "a linen ephod"},
         "skip": {"2": "21:9 순간엔 칼을 이미 에봇 뒤에서 꺼내 내민다 — 「그 뒤에 물건이 놓여 있나」는 순간 앞"}},
        {"id": "showbread", "role": "bg", "judge": "scene",
         "slot": {"path": "whole_background.en", "old": "stacked round loaves"},
         "skip": {"2": "떡을 건넨 것은 21:6 — 21:9 순간에 제사장은 칼을 건넨다"}}
      ]
    },
    "authored-david-gath-achish": {
      "a": {"dir": "verse-regen", "task": 376},
      "word_qids": ["figures[0].prop", "figures[0].pose"],
      "units": [
        {"id": "scrawl-door", "role": "core", "judge": "act", "who": "david",
         "slot": {"path": "figures[0].gesture.en", "old": "scratching marks on the doors of the gate"}},
        {"id": "drool-beard", "role": "core", "judge": "act", "who": "david",
         "slot": {"path": "figures[0].gesture.en", "old": "drool running down his beard"}}
      ],
      "signs": [
        {"id": "feigned-madness", "signs": ["scrawl-door", "drool-beard"],
         "remove": {"path": "figures[0].expression.en", "old": "feigning madness with "}}
      ]
    }
  }
}
```
