# JORDAN-STEP1 — 장면 5(다윗 귀환 — 요단, 삼하 19장) 단계 ① 명세 (task 455)

단계 ① 통과 기준은 둘이다. 하나는 `spec_failures` 실패·못 잼 0이고, 다른 하나는 scripture-reviewer 판정표 틀림 0이다. GPU는 쓰지 않았다.

## 시도 1 — 걸린 규칙 (2026-10-31 재검 판 d044f9bf3b3f)

| 규칙 | 걸린 까닭 |
|---|---|
| `spec.stage-from-scripture` | david-elder·shimei의 `stage_why`가 없다 |
| `generate.guide-body-build` | guide에 사람 꼴이 있는데 `body`가 `card`가 아니다 |
| `derive.prop-size-relative` | 사전 ferry-boat에 `look.size`가 없다(notes/SCALE.md 재검 목록 3에서 미룸) |

## 보완

- **나이 근거(stage_why)**
  - 다윗: [추론] 삼하 5:4·15:7과 연대 파일(`data/person_events/david.json` 출생 BC 1040경 · 귀환 BC 978경)로 약 62세 → david-elder.
  - 시므이: [추론] 왕상 2:9 「그 백발의 피를 흘려」 — 임종 8년쯤 앞이라 희끗해 가는 나이. 50대는 다윗·바르실래(19:32 「나이 팔십 세라」)와 가르려고 저작자가 정했다(카드 _why와 같음).
- **가이드 몸 너비**: `guide.body = "card"`(기브아·두 여인과 같음).
- **나룻배 크기**: 사전 ferry-boat에 `look.size`를 넣었다(man-height 2.5 · 「about two and a half times as long as a man is tall」 · [저작]). L2 en에도 그 구절을 넣었다. 명세 안에서 옛 L2 문구가 실린 세 곳을 같이 고쳤다(S1b·verse_elements[7]·whole_background). 옛 문구만 두면 `spec.verse-elements`·`spec.lexicon-link`가 걸린다.
- **512토큰(후속 fu-acec)**
  - 크기 구절(+15)로 한 장 프롬프트가 527이 됐다.
  - 구절 요소 문구와 사람 메모 문구는 두고, whole_background의 꾸밈말만 뺐다.
    - 「wide dry」
    - 「empty pale sky」
    - 「at the water's edge」
    - 「the far bank across the water」 — 서편 둑은 유다 족속 구절 「across the river on the far western bank」가 그대로 싣는다.
  - 결과는 512 이하다(규칙 `derive.512-tokens` 통과). 판 단계(stages) 문구는 그대로다.
  - **다음에 이 장면에 낱말을 더할 때 줄일 자리**: S2b·S2 앞의 「on the near bank」 반복(둘 중 하나) · 바르실래 「a wealthy man」을 뺄지(19:32 구절 요소라 빼려면 사람 결정).

## 시도 2 — 규칙 재검

`spec_failures('authored-david-returns-jerusalem')` → `[]`. 앞 장면 다섯은 그대로 통과했고, 시험 207개도 통과했다.

## 본문 검토 (scripture-reviewer)

- **1차**(전 명세): 틀림 0 · 약함 6.
  - 시므이 stage_why의 「그 백발」 주인 → 왕상 2:8 인용을 더함.
  - 배 크기 [저작] 표기가 S1b.verse·verse_elements[7].ko에 없음 → 더함.
  - 가족 12명 대 작은 배 → crowds[1].count_why에 「일부가 먼저 오름 [저작] · 19:41」을 더함.
  - 62세 근거 → 프로젝트 연대로 셈, 13:23 등은 통치 후반 정황으로 한정.
  - 바르실래가 순간에 강가에 있음 → S5.verse·same_time 19:31에 [추론] 표기.
  - _regions_why 시바 일행 35 → 36.
  - 모두 근거·표기 칸만 고쳤고, 그림 문구는 그대로다.
- **2차**(고친 칸만): 틀림 0 · 약함 0.
- 참고(2차 지적, 고치지 않음): same_time 19:32·moment.why의 바르실래 목록에는 [추론] 표기가 따로 없다. 바로 위 19:31 칸이 표기해 두어 모순은 아니다.

판정표: 틀림 0 · 약함 0
