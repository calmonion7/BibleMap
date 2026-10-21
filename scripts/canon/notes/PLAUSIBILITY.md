# 상식 규칙집 — 그림이 논리적으로 맞는가 (2026-10-21)

사용자: 「자연스럽지 않은 행동을 판별할 수 없나 · 논리적으로 안 맞는 · 칼을 손으로 잡을 수 없고 · 배가 땅 위에 있고(이 장면에는 아니잖아) · 이런 규칙들 세울 수 있음 세워줘」.

**왜 따로 만드나**: task 378 「이상한 점」(O1) 판정자는 문항 하나로 「모호하면 이상함」을 물어 너무 많이 잡았다 — 이상 없음 통과 11/33(채택 기준 0.75, `notes/SPEC-JUDGE.md`). 이 규칙집은 반대로 **상식 규칙을 하나씩 구체 문항으로** 묻고, **결함이 분명히 보일 때만 「틀림」**으로 답하게 한다(머리말 `pl1`).

## 규칙 (고정 절 `rules`)

- **늘 묻는 규칙** — 발이 땅에 닿음 · 팔다리 수와 몸 섞임 · 할 수 있는 자세 · 원근.
- **명세에 그 대상이 있을 때만 묻는 규칙**(걸림 낱말 = 장면 파생 문구의 낱말 경계 정규식): 쥔 물건 · 칼 손잡이 · 도구가 대상에 닿음 · 무거운 물건 · 배가 물에 · 배에 오름 · 엎드림(누움 아님) · 한 사람만의 관.
- 규칙은 장면마다 다시 쓰지 않는다 — 명세 낱말이 규칙을 고른다. 장면 뜻·구절 충실은 J1·E 몫이고, 여기는 **물리·몸·사물의 상식**만 본다.

## 검증 (판정 전에 고정)

- 묶음 = 사람 라벨이 있는 그림:
  - **결함 있음(사람이 지적)** — 엔게디 365 「손·칼」 틀림 12장(`notes/ENGEDI-GAZE.md` G-hand) → 칼·쥔 물건·도구 닿음 규칙 · 요단 r5 s202 「시므이가 누웠음」→ 엎드림 · r5 s23 「배타는게 이상함」→ 배에 오름 · 요단 387 r1 s42·s101 「배는 강어귀에, 가족이 배에 오르려는 장면」→ 배가 물에·배에 오름 · 놉 b2 s101 「대검을 한 손으로 받기엔 무겁다」→ 무거운 물건 · 요단 r3 s42·s202 금관 쓴 사람 둘(**실행자 눈** 라벨) → 한 사람만의 관.
  - **결함 없음** — 엔게디 365 「손·칼」 맞음 13장(그 세 규칙만) · 사람 승인 최종 12장(모든 규칙).
- 그림마다 걸린 규칙을 한 번에 3회 묻고(claude -p Sonnet · 머리말 `pl1`) 문항마다 다수결.
- **규칙 채택**(거르기에 넣음) = 지적 그림에서 잡음 ≥ 2/3 **그리고** 결함 없는 그림 헛경보 ≤ 20%. 지적 그림이 없는 규칙(늘 묻는 넷)은 헛경보 ≤ 10%면 「기록만」으로 남기고 거르기엔 넣지 않는다. 묶음 잡음은 묶음 안 규칙 하나라도 틀림이면 잡음으로 센다(엔게디 「손·칼」 라벨은 칼·손·자르기를 함께 봤다).

```json fixed
{
  "reps": 3,
  "rules": [
    {"id": "p.feet", "always": true, "q": "발", "what": "서 있거나 걷는 사람의 발이 땅·바닥·배 바닥에 닿아 있나(공중에 뜨거나 물 위에 서 있지 않음)?"},
    {"id": "p.body", "always": true, "q": "몸", "what": "사람마다 머리 하나·팔 둘·다리 둘이고, 다른 사람과 몸이 붙거나 겹쳐 하나로 섞이지 않았나?"},
    {"id": "p.joints", "always": true, "q": "자세", "what": "모든 사람의 자세가 사람이 실제로 할 수 있는 자세인가(관절이 반대로 꺾이거나 몸이 뒤틀리지 않음)?"},
    {"id": "p.scale", "always": true, "q": "원근", "what": "가까운 사람은 크고 먼 사람은 작아 원근이 맞나(비슷한 거리의 사람끼리 크기가 터무니없이 다르지 않음)?"},
    {"id": "p.held", "triggers": ["holding", "holds", "in (?:his|her|one|both) hands?", "knife", "sword", "spear", "harp", "lyre", "horn", "staff", "cloak corner"], "q": "쥔 물건", "what": "손에 든 물건이 손에 실제로 쥐어져 있나(손 옆에 떠 있거나 손을 뚫고 지나가지 않음)?"},
    {"id": "p.blade-grip", "group": "blade", "triggers": ["knife", "sword", "blade", "dagger"], "q": "칼 쥐기", "what": "칼·단검을 든 사람은 손잡이를 쥐고 있나(날을 맨손으로 쥐거나 날이 손을 뚫지 않음)?"},
    {"id": "p.tool-contact", "group": "blade", "triggers": ["cut", "cutting", "pour", "pouring", "pours"], "q": "도구 닿음", "what": "도구로 무엇을 하는 동작(자르기·붓기)이면 도구 끝이 그 대상에 실제로 닿아 있나(허공에서 하는 시늉이 아님)?"},
    {"id": "p.weight", "triggers": ["heavy", "goliath", "great sword", "large sword"], "q": "무게", "what": "크고 무거운 물건(대검·큰 돌 등)을 받는 사람이 그 무게에 맞게 두 손이나 몸으로 받치고 있나(한 손가락이나 한 손으로 가볍게 들고 있지 않음)?"},
    {"id": "p.boat-water", "group": "boat", "triggers": ["boat", "ferry"], "q": "배와 물", "what": "배가 물 위에 떠 있거나 물가에 닿아 있나(물에서 떨어진 마른 땅 위에 있지 않음)?"},
    {"id": "p.boarding", "group": "boat", "triggers": ["climbing into", "boarding", "into the (?:landed )?boat"], "q": "배에 오름", "what": "배에 오르는 사람들이 배 안에 있거나 배에 발을 디디고 있나(배 밖 강가에 줄지어 서 있지 않음)?"},
    {"id": "p.bow-kneel", "triggers": ["kneel(?:ing)?", "bowed", "bowing", "prostrat\\w*", "forehead to the ground"], "q": "엎드림", "what": "엎드려 절하는 사람이 무릎을 꿇고 엉덩이를 들고 이마를 땅에 대고 있나(배를 깔거나 등을 대고 누워 있지 않음)?"},
    {"id": "p.one-crown", "triggers": ["circlet", "the only one crowned", "only man wearing a crown"], "q": "관 하나", "what": "머리에 관을 쓴 사람이 한 사람뿐인가(곁의 다른 사람도 관을 쓰지 않음)?"}
  ],
  "validate": {
    "engedi_hand": {"metrics": "samples/engedi-gaze/metrics.json", "screen": "G-hand", "pressed": [2, 4, 6, 9, 11, 15, 16, 17, 20, 21, 22, 23],
                    "paths": {"r2": "prompt-512/engedi/s{seed}.png", "A": "engedi-gaze/A/s{seed}.png", "B": "engedi-gaze/B/s{seed}.png", "ref": "@samples/face-ab/approved-engedi.png"},
                    "scene": "authored-david-en-gedi-saul", "group": "blade"},
    "flagged": [
      {"image": "restyle-r5/cn/s202.png", "scene": "authored-david-returns-jerusalem", "rules": ["p.bow-kneel"], "source": "사람 r5 「시므이가 누웠음」"},
      {"image": "restyle-r5/cn/s23.png", "scene": "authored-david-returns-jerusalem", "rules": ["p.boarding"], "source": "사람 r5 「배타는게 이상함」"},
      {"image": "jordan-scene/r1/authored-david-returns-jerusalem/s42.png", "scene": "authored-david-returns-jerusalem", "rules": ["p.boat-water", "p.boarding"], "source": "사람 387 「배는 강어귀에 다다르고 가족들이 배에 오르려는 장면」"},
      {"image": "jordan-scene/r1/authored-david-returns-jerusalem/s101.png", "scene": "authored-david-returns-jerusalem", "rules": ["p.boat-water", "p.boarding"], "source": "사람 387 같은 메모"},
      {"image": "plain-words/b2/authored-david-nob-priests/s101.png", "scene": "authored-david-nob-priests", "rules": ["p.weight"], "source": "사람 382 「대검을 한 손으로 받기엔 무겁다」"},
      {"image": "restyle-r3/cn/s42.png", "scene": "authored-david-returns-jerusalem", "rules": ["p.one-crown"], "source": "실행자 눈 r3 금관 둘"},
      {"image": "restyle-r3/cn/s202.png", "scene": "authored-david-returns-jerusalem", "rules": ["p.one-crown"], "source": "실행자 눈 r3 금관 둘"}
    ]
  },
  "adopt": {"catch": 0.667, "false_alarm": 0.2, "always_false_alarm": 0.1}
}
```

## 명령
- `python3 batch/plausibility.py validate` (판정 · 3회) → `report` → 채택 규칙은 `adopted()`로 다른 판정 묶음이 쓴다.

## v1 결과 (2026-10-21)

- 판정 132건(44장 × 3회) 답 빠짐 0. **헛경보는 거의 없지만(결함 없는 그림에서 틀림 0) 결함도 거의 못 잡았다**: 칼 쥐기 0/12 · 도구 닿음 0/12 · 엎드림 0/1 · 배와 물 0/2 · 무게 0/1 · 배에 오름 2/3 · 관 하나 2/2. O1(너무 많이 잡음)과 반대쪽 실패다.
- 기준 계산 바로잡음: 노트 기준은 「잡음 ≥ 2/3」인데 코드가 0.667과 비교해 2/3(0.6667)을 떨어뜨렸다 — 기준을 바꾼 것이 아니라 코드를 노트에 맞춰 분수 비교로 고쳤다. 고친 셈으로 v1 채택 = 배에 오름 · 관 하나.
- 못 잡은 까닭(판정자 이유를 읽음):
  - **라벨 대응 잘못**: 387 s42·s101 사람 메모는 「배가 강어귀에(이쪽 강가에) 닿아야」 — 배가 물에 없다는 상식 결함이 아니라 명세 몫(E `e.boat-landed`)이다. 엔게디 「손·칼」 라벨은 「두 손·칼 위치가 자르는 동작에 맞지 않음」으로 쥐는 법이 아니라 동작 자세를 봤다 — 판정자는 「손잡이를 쥐고 칼끝이 자락에 닿음」.
  - **문항이 너무 너그러움**: s202 시므이를 판정자는 「웅크려 이마를 땅에 댐 · 눕지 않음」으로 봤다. 사람이 본 결함은 다리를 뒤로 뻗은 몸이었다 — 「무릎 꿇었나」가 아니라 **눈으로 셀 수 있는 모양**(정강이가 엉덩이 밑에 접혔나)으로 물어야 한다.

채택: p.boarding · p.one-crown

## v2 (판정 전에 고정)

- 바꾼 것(Reflexion — 같은 문항 다시 묻지 않음): ① 라벨 바로잡음 — 387 두 장은 「배와 물」에서 빼고 「배에 오름」만 ② 결함 모양을 셀 수 있게 다시 쓴 문항 다섯(`*2`) ③ **대상 칸 크롭**을 함께(지금 명세 regions + 둘레 0.08, 그 장면에 칸이 없으면 전체만) ④ 머리말 `pl2` — 문항마다 대상의 상태를 먼저 적고 판정.
- 나머지 규칙·묶음·3회·채택 기준(분수 비교)은 v1 그대로. v2 문항이 채택되면 v1 같은 이름 문항을 대신한다.

```json fixed2
{
  "rules": [
    {"id": "p.bow-kneel2", "of": "p.bow-kneel", "crop": ["shimei"], "q": "엎드린 다리", "what": "엎드린 사람의 정강이가 엉덩이 밑에 접혀 무릎이 땅에 닿아 있나(다리를 뒤로 쭉 뻗거나 배를 깔고 누워 있지 않음)?"},
    {"id": "p.boarding2", "of": "p.boarding", "crop": ["boat", "household"], "q": "배에 탄 사람", "what": "배에 오르는 사람들이 배 안에 앉거나 서 있거나 뱃전에 발을 올리고 있나(배 밖 마른 땅에 줄지어 서 있기만 하지 않음)?"},
    {"id": "p.blade-grip2", "of": "p.blade-grip", "crop": ["david", "ahimelech"], "q": "칼 쥔 주먹", "what": "칼을 쥔 손의 주먹이 칼의 손잡이를 감싸고 있나(손이 날을 감싸거나, 칼이 손에서 떨어져 떠 있지 않음)?"},
    {"id": "p.tool-contact2", "of": "p.tool-contact", "crop": ["david", "saul"], "q": "자르는 손", "what": "자르기·붓기 동작이면 도구가 대상에 닿아 있고, 그 일을 하는 두 손·팔의 자리가 그 동작에 맞나(한 손은 대상을 붙잡거나 받치고, 팔이 엉뚱한 쪽을 향하거나 비틀리지 않음)?"},
    {"id": "p.weight2", "of": "p.weight", "crop": ["ahimelech", "david"], "q": "무게 받침", "what": "대검처럼 크고 무거운 물건을 받는 사람이 두 팔로 받쳐 몸으로 그 무게를 견디는 자세인가(손끝으로 집거나 한 손으로 가볍게 들고 있지 않음)?"}
  ],
  "drop_flagged": {"jordan-scene/r1/authored-david-returns-jerusalem/s42.png": ["p.boat-water"], "jordan-scene/r1/authored-david-returns-jerusalem/s101.png": ["p.boat-water"]},
  "pad": 0.08,
  "zoom": 2.0
}
```
