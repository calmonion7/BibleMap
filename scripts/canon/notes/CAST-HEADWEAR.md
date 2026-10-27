# 카드 v1 `headwear` — 카드 머리 윤곽과 맞춤 (task 440, 2026-10-27)

후속 fu-16d6cf9daa2a(task 438 scripture-reviewer 1차 주의 — 참 어머니 카드가 머리 윤곽은 숄인데 v1 `headwear`는 `none`).

## 새 규칙 `spec.cast-headwear`

카드 v1 `headwear` 칸이 `card.headOutline`과 맞아야 한다.

- (가) `headwear` == `none` ⟺ class == `bare`
- (나) class가 머리 윤곽 어휘 안 — `bare` · `headwrap` · `turban` · `veil` · `shawl` · `diadem` · `helmet` · **`crown`(이번에 더함)**. `crown`은 삼하 12:30 금 면류관(다윗 귀환 장면 덮어쓰기) — 스바 여왕의 머리띠 `diadem`과 다른 것. 어휘 정본 `cast/CAST.md` 필드 표도 같이 고침.

이 칸은 장면 프롬프트에 나가지 않는다(카드 v2 문구는 `headOutline.text`만 씀 — `derive_scene.cast_describe`). 나가는 곳은 둘:

- 판 시트 부정 낱말 `gen_cast_plate.neg_for` — `none`이면 helmet·crown·turban을 뺀다. 아각은 「dark wound desert turban」을 그리라면서 turban을 빼고, 방패든 자는 가죽 모자(class helmet)인데 helmet을 뺐다.
- 판정 설명 `judge_face_canon.vocab`(44행) · `batch/judge_vlm._cast_lines` — 숄 쓴 참 어머니를 판정자에게 「headwear: none」이라고 말했다.

거는 곳(같은 함수 `check_cast_v2.headwear_errors` 하나, 431 `spec.cast-age-word`와 같은 모양):

- 카드: `check_cast_v2.check` (l) — 그래서 `spec.cast-card-v2`도 함께 잡는다.
- 재검: `recheck.cast_headwear_errors` — 명세 인물마다 `_cast_in_scene`(장면 `cast_override` 포함). `check_scenes`에는 따로 안 건다. 원장 판 826e3c0c066d(규칙 83).
- 시험: `test_scene_rules.CastHeadwear`(가·나 걸림·통과 · 장면 덮어쓰기 · `neg_for`가 쓰개 인물에 helmet·crown·turban을 덧붙이지 않음).

적용 전 손 finder와 같은 결과: 카드 35장 중 5장(아래) · 반대쪽(class bare인데 headwear 있음) 0 · 장면 덮어쓰기 머리 윤곽 6건 중 1건(다윗 귀환 david-elder).

## 바꾼 값

| 대상 | 전 | 후 | 카드 머리 윤곽 |
|---|---|---|---|
| mother-a `headwear` | `none` | 「plain brown shawl」 | shawl 「plain brown shawl over a dark braid」 |
| achish `headwear` | `none` | 「striped cloth headwrap」 | headwrap |
| agag `headwear` | `none` | 「dark wound turban」 | turban |
| david-old `headwear` | `none` | 「soft white linen head-cloth」 | headwrap |
| shieldman `headwear` | `none` | 「plain round leather cap」 | helmet |
| 다윗 귀환 david-elder 덮어쓰기 | (없음 → 카드 `none`) | `headwear` 「gold crown」 | crown(삼하 12:30) |

- `_why.headwear`는 「맨머리 기본값」을 지우고 `card.headOutline` 근거(시대 고증 [저작])를 따름 + 「카드 머리 윤곽과 맞춤 — task 440」. 귀환 장면은 `cast_override_why` 끝에 같은 한 마디.
- 참 어머니는 숄 쪽으로 정함: 문구가 이미 숄이고(`head_text`) 카드 근거가 「성인 여성 머리 가림은 시대 고증」. 맨머리로 바꾸면 두 여인 문구·그림이 바뀌어 단계 ④ 화면 그림이 낡는다.
- 프롬프트 지문 그대로: 두 여인 한 장 `2643380bac5e` · 다윗 귀환 한 장 `265b036f74e5`(전후 같음).

## 판 시트 — 표시만

`neg_for`가 바뀐 4장 판(mother-a·achish·agag·david-old 승인 · shieldman 보류)은 옛 부정 낱말(쓰개 낱말을 뺀 채)로 그린 판이다. 이 작업은 다시 그리지 않고 승인도 취소하지 않는다 — 다음에 이 인물 판을 다시 만들 때 고친 부정 낱말이 쓰인다.

## 재검

- 명세(`recheck.py specs`): `spec.cast-headwear` 38/38 통과 · `spec.cast-card-v2` 실패 0 · 전 규칙 통과 5/38 그대로.
- 승인 그림(`recheck.py images`): 승인 그림 14 · 잰 규칙 모두 통과 3/14 그대로. 새 칸이 `stale`인 8장(기브아 수금·다윗 귀환·베들레헴·라마 죽음·길갈 즉위·야베스·믹마스·미스바)은 모두 이전부터 「그림 뒤 명세가 바뀜」(`cast-card-v2`도 같은 8장 낡음) — **이 규칙 때문에 새로 낡은 승인 그림 0장**. 다시 그리기·승인 취소 없음.
