# LOCAL-EDIT — 놉 제사장·가드 아기스 국소 편집 (task 371)

370에서 문구(칸·판 두 묶음)로 8/8이 안 움직인 두 장면의 칸을 **문구 A/B 없이** klein 국소 편집으로 고친다(PROMPTING 24 · 370 회고). 수단은 엔게디 「칼만 고치기」(`notes/ENGEDI-HANDFIX.md`) 그대로다: 작은 크롭 → 1024 klein 지시 편집 → `color_match` → 타원 마스크 되붙임, 지시는 한 편집에 하나.

## 고정 절 (실행 전, 2026-10-20)

- 바탕: `params.LOCAL_EDIT_BASES` — 370 칸 묶음(`~/.local/biblemap-imggen/whole-wide/<장면>/base/s<시드>.png`)에서 처치 칸 밖 문항이 깨끗한 장.
  - 놉 제사장 s7·s202(같은 사람·자세 틀림 시드 5·11·23·42·101·303 제외).
  - 가드 s5·s7(다윗 같은 사람이 맞은 s5·s7·s23·s303 중 앞 둘, 아기스 문항은 8장 모두 맞음).
- 편집: FLUX.2-klein-4B(mflux q8, 4스텝, 1024), klein 시드 `params.LOCAL_EDIT_SEEDS` = 1·2·3. 새 바탕 생성 없음, 정본 참조 편집 없음, Z-Image 인페인트 없음.
- 크롭·마스크 상자(원본 1216×640 좌표, 실행자가 그림을 보고 잡음 — `gen_local_edit.BOX`):

  | 장면 · 바탕 | 크롭 (L, T, 변) | 마스크 상자 | 편집 부위 |
  |---|---|---|---|
  | 놉 s7 | 440, 250, 380 | 445, 355, 810, 500 | 칼과 두 사람의 칼 쥔 손 |
  | 놉 s202 | 430, 260, 380 | 435, 390, 810, 535 | 칼과 두 사람의 칼 쥔 손 |
  | 가드 s5 | 20, 120, 400 | 70, 140, 400, 505 | 다윗 상체·팔 + 왼쪽 어깨 옆 |
  | 가드 s7 | 20, 120, 400 | 70, 140, 400, 505 | 다윗 상체·팔 + 왼쪽 어깨 옆 |

  가드 몸 크롭은 계획 어림(280~360)보다 크다(400). 기대는 자세가 어깨·고개·팔에 걸려 상체가 다 들어가야 해서다.
- 팔(arm):
  - 놉 제사장: **N1**(「칼을 하얀 천으로 완전히 감싼 긴 꾸러미, 한쪽 끝에 손잡이만」) · **N2**(같은 뜻, 다른 낱말 — 「칼날 전체를 접은 천 두루마리 속에 숨기고 끈으로 묶음」). 바탕 2 × 시드 3 × 문구 2 = 12장.
  - 가드 1단계(몸): **I**(지시만 — 「옆의 높은 나무 성문 기둥에 어깨를 기댐, 고개 기울고 두 팔 늘어짐」) · **G**(가이드 — 크롭 위 다윗 왼쪽 어깨 옆 x 88~118에 갈색 세로 띠를 붙인 뒤 「이 갈색 막대를 낡은 나무 성문 기둥으로 다시 그리고 그가 어깨를 기댐」). 바탕 2 × 시드 3 × 팔 2 = 12장.
  - 가드 2단계(얼굴): **F**(「벌린 입에서 침이 수염으로 흘러내리고 눈은 초점 없이 풀림」) × 1단계에서 사람이 고른 장 1 × 시드 3 = 3장. 얼굴 크롭은 고른 장을 보고 잡는다(metrics에 기록). 1단계 「없음」이면 건너뛴다.
- 실행자 눈 확인은 거르기 관문이 아니다. 깨진 파일만 본다. 기계 거르기 없음(ADR 260905-104910).

### 판정 페이지 (한 화면 한 문항, 「틀린 그림을 누르세요」)
- 후보는 「후보 NN」 번호로만 보이고, 번호는 `LOCAL_EDIT_SHUFFLE_SEED`(371)로 섞는다(대응은 metrics `candidates[].label`). **처치 없는 바탕(가드 2단계는 1단계 고른 장)을 같은 화면에 섞는다.**
- 카드는 편집 부위 크롭(얼굴 문항은 머리 크롭, 장면 문항은 전체). 「크게」는 전체 그림 + 편집 부위 크롭.
- 1단계 페이지(UAT 1):
  - 놉 제사장: `prop`(칼이 보자기에 싸여 손잡이만 보이지 않는 그림) · `moment`(두 사람이 그 꾸러미를 함께 잡고 있지 않은 그림) · `seam`(편집 자리가 튀는 그림 — 색·화풍·이음새) · `figures[0].identity`(아히멜렉) · `figures[1].identity`(다윗) → 고르기.
  - 가드 1단계: `figures[0].pose`(기둥에 기대지 않은 그림) · `figures[0].facing`(누군가와 마주 보는 그림 — 허공을 봐야 함) · `figures[0].prop`(나무 성문 기둥이 없는 그림) · `seam` · `figures[0].identity`(다윗) → 고르기.
- 2단계 페이지(UAT 2, 가드만): `spit`(침이 안 보이는 그림) · `moment`(미친 체하는 얼굴이 아닌 그림) · `figures[0].identity` · `seam` → 고르기.
- 고르기는 **편집 후보만**(섞은 바탕은 대조라 고를 수 없다) 또는 `없음`. 가드 2단계는 「1단계 그림 그대로(침 편집 없음)」도 고를 수 있다.

### 결론 규칙
- 장면 **고침** = 사람이 편집 후보 하나를 골랐고, 고른 후보에 그 단계 문항 틀림 표시가 하나도 없다. 가드는 1단계 고른 장과 2단계 고른 장이 모두 그렇다.
- `판정: 둘 다 고침` / `하나 고침` / `못 고침`.
- 고른 그림은 틀림 표시와 무관하게 사람 승인이다 → 명세 `approved.final` = `{path: "local-edit", seed: 바탕 시드, image, steps: [편집 차례], by: user, on}`. 승인 그림은 `samples/local-edit/approved-<장면>.png`로 레포에 둔다.
- 결론 밖 기록: 팔 I 대 G(가드 `figures[0].prop`·`pose` 틀림 수), 문구 N1 대 N2(놉 `prop` 틀림 수), 섞은 바탕의 틀림(대조 — 처치 문항이 바탕에서 맞으면 문항이 무디다는 신호), 사람 소요 분.
- 못 고친 장면의 다음 과제는 이 수단의 반복이 아니라 다른 수단(순간을 다시 정하는 명세 그릴링 등)으로 적는다.

### 어림 시간
- klein 27장 × 약 1분 ≈ 30분(무인) + 사람 1단계 약 11화면 · 2단계 약 5화면.

## 결과 (2026-10-20, 사람 판정 = 1단계 페이지 1회, 8.16분)

판정: 못 고침
다음 과제: 국소 편집 반복이 아니라 명세 그릴링으로. 놉 제사장은 지물 칸을 「골리앗의 대검(삼상 21:9 — 크고 긴 칼)이 보자기에 싸였어도 칼 모양·크기가 드러남」으로 다시 정한다(지금 칸 `a cloth-wrapped sword`에는 크기·골리앗 칼이 없어 문항도 그것을 묻지 못했다). 가드는 순간을 21:13 원문(「대문짝에 그적거리며 침을 수염에 흘리매」)으로 다시 그릴링하고, 기둥을 몸 편집으로 만들지 않는다(바탕 포함 14/14 「나무 기둥 아님」, 몸 편집은 잔상을 남김).

### 문항 × 팔 (틀린 후보 수, 편집 6장씩 · 대조 바탕 2장)

| 장면 | 문항 | 팔 1 | 팔 2 | 대조 바탕 |
|---|---|---|---|---|
| 놉 제사장 | `prop` 보자기·손잡이만 | N1 0/6 | N2 0/6 | 1/2(s7) |
| 놉 제사장 | `moment` 함께 잡음 | N1 0/6 | N2 0/6 | 0/2 |
| 놉 제사장 | `seam` | N1 0/6 | N2 0/6 | 0/2 |
| 놉 제사장 | 같은 사람 아히멜렉·다윗 | 0/6 · 0/6 | 0/6 · 0/6 | 0/2 |
| 가드 1단계 | `figures[0].pose` 기댐 | I 0/6 | G 0/6 | 0/2 |
| 가드 1단계 | `figures[0].facing` 허공 | I 2/6 | G 5/6 | 2/2 |
| 가드 1단계 | `figures[0].prop` 나무 성문 기둥 | I 6/6 | G 6/6 | 2/2 |
| 가드 1단계 | `seam` | I 3/6 | G 6/6 | 0/2 |
| 가드 1단계 | 같은 사람 다윗 | I 4/6 | G 2/6 | 0/2 |

- 고르기: 놉 「없음 — 대검(골리앗의 검)인데 칼 크기가 너무 작고, 보자기에 싸였어도 칼 모양이 나야」 · 가드 「없음 — 잔상도 있고 나무 기둥도 아니고 침도 안 흘림」. 가드 2단계(얼굴)는 1단계 「없음」이라 건너뜀(편집 0장).
- **놉: 편집본 12장 모두 다섯 문항 틀림 0인데 「없음」.** 사람의 거절 기준(칼 크기·골리앗 대검)이 명세 지물 칸에도 문항에도 없었다. 수단(klein 국소 편집)은 지시한 것(보자기 꾸러미, 이음새 없음)을 해냈다 — 지시가 틀렸다.
- **가드: 기둥 문항은 바탕 포함 14/14.** 팔 G(갈색 띠 가이드)는 이음새 6/6으로 I(3/6)보다 나빴고 허공 시선도 나빴다(5 대 2). 기댐(`pose`) 문항은 바탕까지 0/8이라 무뎠다 — 메모(「성벽 옆 나무문 옆에 기댄 모습」)로 보아 사람은 자세보다 기댄 대상을 봤다.
- 팔 I 대 G: I가 이음새·시선에서 낫고 같은 사람에서 나쁨(4 대 2). 문구 N1 대 N2: 차이 없음(둘 다 0).
- 사람 소요 8.16분(놉 5.89 · 가드 4.94, 어림 11화면).
- 생성: klein 24장 964초(장당 약 40초, 어림 1분).

---

# task 386 — 고른 그림 국소 편집: 베들레헴 r2 s42에 기름 흘러내림 · 가드 r2 s5에 침

## 고정 절 (편집 전, 2026-10-21)

383에서 사람이 고른 두 그림(`~/.local/biblemap-imggen/plain-words/r2/<장면>/s<시드>.png`)에 남은 낱말 하나씩을 371 조리법 그대로(작은 크롭 → 1024 klein 지시 편집(지시 하나) → 원본 크롭 색 맞춤 → 타원 마스크 안쪽만 되붙임) 더한다. 둘 다 L3 문구로도 안 움직인 작은 동작·지물이라(PROMPTING 24·26) 문구 A/B가 아니라 국소 편집 차례다.

- 베들레헴 r2 s42: 사람 메모 「기름뿔에서 기름이 흘러내리는 모습이 없음」 — 지금은 뿔 끝 방울 몇 개(삼상 16:13 「기름 뿔을 취하여 … 부었더니」).
- 가드 r2 s5: 턱 밑 가는 줄 하나 — 침으로 읽히지 않음(삼상 21:13 「침을 수염에 흘리매」).
- 편집: FLUX.2-klein-4B(mflux q8, 4스텝, 1024), 시드 1·2·3(`params.LOCAL_EDIT_SEEDS`). **갈래 2 × 시드 3 = 장면마다 6장, 모두 12장.** 지시 끝에 371의 「Keep …」 문장(가드는 371 `KEEP_FACE` 그대로, 베들레헴은 같은 꼴로 손·뿔·소년 얼굴·배경·화풍).
- 크롭·마스크(원본 1216×640 좌표, 실행자가 그림을 보고 잡음):

  | 장면 · 바탕 | 크롭 (L, T, 변) | 마스크 상자 | 편집 부위 |
  |---|---|---|---|
  | 베들레헴 r2 s42 | 310, 160, 240 | 365, 210, 470, 330 | 뿔 입구 ~ 소년 정수리·곱슬머리(사무엘 얼굴은 크롭 밖) |
  | 가드 r2 s5 | 250, 110, 240 | 315, 200, 395, 300 | 입가 ~ 수염 끝·턱 아래(눈 y≈175는 마스크 밖) |

- 갈래(지시 글은 아래 json이 정본 — `gen_local_edit.py`가 그대로 읽고, `check386`이 기록과 글자까지 대조):
  - 베들레헴 **O1** = 사전 `oil` L3 `en` 그대로 + Keep · **O2** = 짧은 직접 지시(뿔의 열린 끝에서 금빛 기름이 가는 줄기로 소년의 곱슬머리 위로 흘러내림) + Keep.
  - 가드 **D1** = 사전 `drool-beard` L3 `en` 그대로 + Keep · **D2** = 371 F에서 눈 부분을 뺀 「입에서 침이 수염으로 흘러내림」 + Keep.

### 기계 거름 (사람 화면 전)
- 대상 = 편집 12장 + 원본 2장. 판정자 Sonnet(`claude -p`), 판정자 J1 = v2 전 문항 + 지물 칸만 p2(크롭 2.5배).
- **특징 문항**: 사전 `criteria.features` 전부 — 베들레헴 `oil` · 가드 `drool-beard`. J1-prop 머리말(p2), 크롭 = 편집 크롭 상자(2.5배).
- **장면 J1 문항**: 382 r2에서 이 두 그림에 물은 J1 문항 글 그대로(`plain_words.j1_qs` — 376·379 A 페이지 문항, 크롭은 바탕 시드 상자. 편집은 마스크 안만 바뀌므로 상자를 그대로 쓴다).
- **1위** = 특징을 다 맞은 편집 중 J1 틀림 칸(지물 칸은 J1-prop 답)이 가장 적은 장 — 같으면 갈래 순서(O1·O2 / D1·D2) → 시드 순서(1·2·3). 특징을 다 맞은 편집이 없으면 특징 맞힘이 가장 많은 장을 1위로 두고 화면 머리에 그 사실을 적는다.

### 사람 화면 (장면마다 1화면, 모두 2화면 — 폰 360px 비공개 Artifact)
- 원본과 1위 편집을 블라인드 좌우(장면 id 해시로 고정). 카드마다 편집 부위 크롭을 함께(「크게」는 전체 + 크롭).
- 질문 하나: 「굵은 절의 모습이 보이고 이음 자국이 없는 쪽은?」(왼쪽 / 오른쪽 / 둘 다 아님). 성경 원문 상자(베들레헴 16:13 · 가드 21:13 굵게), 여러 줄 메모칸, 쉼 뺀 타이머, 접힌 칸에 그 장면 편집 6장 전부(기계 불통과 포함 — 갈래·시드만 표시).
- 사람 답(「판정 문장」)은 `samples/local-edit/pick-verdict-386.txt`에 원문 그대로.

### `판정:` 규칙
- 장면 **고침** = 사람이 편집 쪽을 골랐다. `판정: 둘 다 고침` / `하나 고침` / `못 고침`.
- 고침이면 그 장면 명세 `approved.final` = `{path: local-edit, seed: 바탕 시드, image, steps: [{바탕 출처 plain-words r2 s<시드>·갈래·편집 시드·크롭·상자·지시}], by: user}`(371 `record`와 같은 꼴), 승인 그림은 `samples/local-edit/approved-<장면>.png`로 레포에. 못 고침이면 다음 수단을 적는다.
- 측정만: 갈래·시드별 특징 맞힘, 기계 1위와 사람 고름의 일치, 쉼 뺀 사람 시간. 편집 결과는 사전 `verified_level`에 적지 않는다(규칙 7은 문구 단계의 그림 증거).
- 결과는 371 metrics와 섞지 않게 `samples/local-edit/metrics-386.json`.

```json fixed386
{
  "src": "~/.local/biblemap-imggen/plain-words/r2/{scene}/s{seed}.png",
  "seeds": [
    1,
    2,
    3
  ],
  "scenes": {
    "authored-samuel-bethlehem-david-anointing": {
      "base": 42,
      "word": "oil",
      "crop": [
        310,
        160,
        240
      ],
      "box": [
        365,
        210,
        470,
        330
      ],
      "arms": {
        "O1": "Gold, a little thicker than water, shining. It runs in a thin stream from the mouth of a horn and wets the hair. Keep the old man's hand and the horn, the boy's face and curly hair, the background, the lighting and the same soft pencil and colored-pencil illustration style.",
        "O2": "Golden oil pours in a thin stream from the open end of the horn and runs down over the boy's curly hair. Keep the old man's hand and the horn, the boy's face and curly hair, the background, the lighting and the same soft pencil and colored-pencil illustration style.",
        "O3": "Golden oil pours out of the dark open hole of the horn's wide mouth and falls from that opening straight down onto the boy's curly hair. Keep the old man's hand and the horn, the boy's face and curly hair, the background, the lighting and the same soft pencil and colored-pencil illustration style.",
        "OG": "Redraw the golden vertical band as golden oil pouring out of the horn's open mouth hole and falling onto the boy's curly hair. Keep the old man's hand and the horn, the boy's face and curly hair, the background, the lighting and the same soft pencil and colored-pencil illustration style."
      },
      "guide": {
        "OG": {
          "rect": [
            431,
            238,
            439,
            264
          ],
          "rgb": [
            214,
            168,
            48
          ]
        }
      },
      "extra_features": [
        {
          "q": "기름이 뿔의 열린 입구(구멍) 안에서 나오나?",
          "grounds": "사용자 지시(2026-10-21 편집 뒤) 「기름이 원뿔 구멍에서 나와야지」 · [추론] 삼상 16:13 「기름 뿔을 취하여 … 부었더니」 — 뿔에 담긴 기름을 붓는다."
        }
      ]
    },
    "authored-david-gath-achish": {
      "base": 5,
      "word": "drool-beard",
      "crop": [
        250,
        110,
        240
      ],
      "box": [
        315,
        200,
        395,
        300
      ],
      "arms": {
        "D1": "Spit runs from the corner of the mouth down the chin beard in a long strand, and the beard is wet and shiny. Keep his face shape, hair, beard, the lighting and the same soft pencil and colored-pencil illustration style.",
        "D2": "Saliva drips from his mouth down into his beard. Keep his face shape, hair, beard, the lighting and the same soft pencil and colored-pencil illustration style."
      }
    }
  }
}
```
### 사용자 지시 추가 (2026-10-21, O1·O2 편집 12장 뒤 — 기계 거름 전)
- 사람(편집 시험 그림을 보고): 「기름이 원뿔 구멍에서 나와야지..」. 베들레헴 O1·O2 6장 모두 기름이 뿔 **바깥 몸통·테두리를 타고** 흘렀다 — 뿔 입구가 옆(오른쪽)을 향해 있어 지시만으로는 「구멍에서 나옴」이 안 잡혔다.
- **갈래 둘 더함(베들레헴만, 시드 1·2·3 → 6장, 베들레헴 모두 12장)**: **O3** = 「뿔 넓은 입구의 어두운 구멍에서 나와 그 구멍에서 곧장 머리로 떨어짐」 지시 · **OG** = 가이드(구멍 안쪽 아래 → 머리, 원본 x 431~439 · y 238~264 금빛 띠를 크롭에 칠함) + 「이 금빛 띠를 뿔 구멍에서 쏟아지는 기름으로 다시 그림」(371 가드 G와 같은 수단, PROMPTING 24). 갈래 순서 O1·O2·O3·OG.
- **특징 문항 하나 더함(베들레헴)**: 「기름이 뿔의 열린 입구(구멍) 안에서 나오나?」 — 사전 `oil` 문항 3개와 함께 「특징 다 맞음」에 든다. 사전 항목은 이번에 고치지 않는다(사전 손질은 다음 과제 — `oil` 특징 3 「머리나 뿔 입구에서 쏟아지나?」가 구멍과 바깥 몸통을 가르지 못함).
- 접힌 칸은 베들레헴 12장 · 가드 6장. 나머지 규칙(1위·화면·판정)은 그대로.


## 386 결과 — 편집·기계 거름·후보 화면 (2026-10-21, S2~S4)

- 편집 18장(베들레헴 O1·O2·O3·OG × 3 · 가드 D1·D2 × 3), 한 장 약 41초(klein). `gen_local_edit.py check386` → `ok`(장면별 장 수 · 마스크 밖 차 0 · 지시 글 고정 절과 같음).
- 눈 확인(거르기 관문 아님): 베들레헴 O1·O2 6장 모두 기름이 뿔 바깥 몸통·테두리를 타고 흐름 → 사용자 지시로 O3·OG 추가. O3-k2·O3-k3은 구멍 아래 입술에서 머리로 떨어짐, OG(가이드)는 바깥 흐름 그대로.
- 기계 거름(특징 = J1-prop 머리말·편집 크롭 2.5배, J1 = 382 r2 문항, 답 없음 0):

| 장면 | 원본 특징 | 특징 다 맞은 편집 | 1위 |
|---|---|---|---|
| 베들레헴(4문항, 구멍 문항 포함) | 3/4 | O3-k2(J1 틀림 1) · O1-k3(2) · O3-k3(2) | **O3-k2** |
| 가드(3문항) | 2/3 | D1-k1·D1-k2·D1-k3(각 1) · D2-k1·D2-k2(각 2) | **D1-k1** |

- 갈래별 특징 맞힘(편집 3장 합): O1 10 · O2 7 · O3 11 · OG 9 / D1 9 · D2 8.
- 후보 화면 2화면 `check_cand_page.py` 통과(360·1280px 가로 넘침 0 · 순간 절 굵게 · textarea · 타이머), 5.08MB.
  - 비공개 Artifact: https://claude.ai/artifact/6V2RGRLy22qwh4PvUBcEWc
- 사람 답 대기 — 「판정 문장」을 `samples/local-edit/pick-verdict-386.txt`에 두고 `record386` → `verdict386`.

## 386 판정 — 사람 답·기록 (2026-10-21, S5)

- 사람 판정 문장 원문: `samples/local-edit/pick-verdict-386.txt` → `gen_local_edit.py record386`(좌우 출처가 화면을 만든 그대로인지 단언). 화면 2 · 쉼 뺀 1.48분.

| 장면 | 사람 답 | 메모 |
|---|---|---|
| 베들레헴 | **편집**(O3-k2) | 기름을 부으는 위치가 이상함 |
| 가드 | **편집**(D1-k1) | — |

판정: 둘 다 고침

- 두 명세 `approved.final` = `{path: local-edit, seed: 42 / 5, image: samples/local-edit/approved-<장면>.png, steps: [O3-k2 / D1-k1 · 바탕 plain-words r2 s<시드>], by: user}`.
- 측정: 기계 1위와 사람 고름 일치 2/2 · 갈래별 특징 맞힘 O3 11 > O1 10 > OG 9 > O2 7 / D1 9 > D2 8 · 가이드(OG) 효과 없음.
- 남은 것(다음 과제): 베들레헴 메모 「기름을 부으는 위치가 이상함」 — 뿔 입구가 옆을 향해 있고 기름이 정수리가 아닌 앞머리 쪽으로 떨어진다. 지시 편집이 아니라 뿔 기울기(입구가 머리 위를 향함)부터 — 사무엘 손·뿔을 함께 다시 그리는 국소 편집이나 가이드 그림. 사전 `oil` 특징 3 「머리나 뿔 입구에서 쏟아지나?」를 「뿔 입구(구멍)에서 정수리로」로 손질.
