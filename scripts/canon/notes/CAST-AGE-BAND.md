# 카드 나이 대표값 — 사다리·본문 연대 맞춤 (task 429, 2026-10-26)

후속 fu-df5f1c58b64d · fu-e325b633fcd4(task 426 scripture-reviewer 판정표 — notes/PLATE-CAST-TOKEN.md).

## 새 규칙 `spec.cast-age-band`

카드 `card.ageBand.text`의 나이 숫자가 `class` 범위 안이어야 한다(CAST.md 사다리 — child ~9 · youth 10대 · young 20대 · prime 30대 · middle 40~50대 · elder 60대~).

- 해석: `check_cast_v2.card_age` — 「about N」「around N」 → 한 점 · 「in his Ns」 → N0~N9 · early/mid-/late → N0~N3 · N3~N6 · N6~N9. 숫자를 못 읽으면 None(못 잼 — 통과 아님).
- 거는 곳(같은 함수 `check_cast_v2.age_band_errors` 하나):
  - 카드: `check_cast_v2.check` (j) — 그래서 `spec.cast-card-v2`도 함께 잡는다.
  - 장면 덮어쓰기: `check_scenes.check`가 `figures[].cast_override.card.ageBand`를 잰다.
  - 재검: `recheck.cast_age_band_errors` — 명세 인물마다 카드(장면 덮어쓰기 포함)를 잰다. 원장 판 76650c677a15(규칙 80).
- 시험: `test_scene_rules.CastAgeBand`(해석 · 범위 안/밖/못 읽음 · 장면 덮어쓰기).

적용 전 손 finder와 같은 결과: 카드 2장(david-prime · solomon-prime) 걸림, 장면 덮어쓰기 4개(헤브론·요단·기브온·기브아 사울)는 모두 맞음.

## 바꾼 값

| 대상 | 전 | 후 | 근거 |
|---|---|---|---|
| david-prime 카드 | prime 「in his 40s」 | prime 「late 30s」 | [추론] 삼하 5:4-5 — 정차지 나이 예루살렘 정복 37 · 궤 38 · 나단 약 40 |
| solomon-prime 카드 | prime 「in his 40s」 | **middle** 「in his 40s」 | [저작] 왕상 9:10 「이십 년 만에」 뒤 정차지 → 40대, class는 나이대로 |
| solomon-prime silhouette | average | lean 「lean build, straight shoulders, narrow waist」 | [저작] middle이 되며 nathan과 카드 층 차이 1개(전체 구별 (h)) → lean으로 가름. 원래 글이 「narrow waist」라 뜻 변화 가장 작음 · 키(heightRel)는 크기 계산에 쓰여 피함 |
| abner 카드 | prime 「in his 30s」 [저작] | elder 「in his 60s」 [추론] | 삼상 14:50 「그 군장의 이름은 아브넬이니 사울의 숙부 넬의 아들이며」(사울 치세 초기 군장 · 사울과 같은 항렬) + 삼하 2:10 이스보셋 40세 즉위 |
| 솔로몬 출생 장면 david-prime | (덮어쓰기 없음 — 카드 40대) | `cast_override.card` middle 「about 50, fuller face with lines at the eyes and brow」 | [추론] 삼하 5:4-5 · 출생(12:24)은 예루살렘 재위 중 암몬 전쟁(11:1) 뒤 → 약 50세 |
| 기브온 장면 abner | `cast_override.card` elder 60대 | 카드 덮어쓰기 뺌(차림만) | 카드 정본과 같아짐 |
| 헤브론 장면 근거 글 | 「카드 대표값 in his 40s 대신」 | 「late 30s 대신」 | 카드 변경으로 낡은 문구 |

CAST.md: 9줄 id 이름 규칙에 「`-prime` id는 장년(30~40대) 생애 단계 이름이고 카드 class는 나이대로」 단서 · ageBand 행에 새 규칙 표시.

`age`(v1) 칸(abner 「middle-aged commander」 등)은 cast-vocab-2 파생 문구(`cast_describe`)가 쓰지 않아 그대로 두었다.

## 재검

- `recheck.py specs`: 명세 38 × 규칙 41 · `spec.cast-age-band` 38/38 통과 · `spec.cast-card-v2` 38/38 통과 · 전 규칙 통과 5/38(그대로).
- `recheck.py images`: 승인 그림 12 · 잰 규칙 모두 통과 1/12(그대로). **새로 낡음이 된 승인 그림 0장** — 바뀐 세 카드가 나오는 장면(헤브론·정복·궤·나단·솔로몬 출생·기브온·궁전·에시온게벨·스바)에 승인 그림이 없다. 새 규칙 칸은 이미 명세가 바뀐 8장에서 「낡음」, 나머지 4장(가드·기브아 창·길갈 아말렉·놉)에서 통과.

## 본문 검토 (scripture-reviewer, 1회차 — 틀림 0)

인용 글자 대조 전부 일치(삼하 5:4·5:5·2:10, 삼상 14:50, 왕상 9:10). 연대 환산 기준 = 다윗 30세 즉위 BC 1010.

| 정차지 × 인물 | 값 | 판정 | 요지 |
|---|---|---|---|
| 헤브론 × david-prime | 덮어쓰기 about 30 · prime | 맞음 | 삼하 2:4 기름부음 = 즉위 순간, 5:4 |
| 예루살렘 정복 × david-prime | late 30s · prime | 맞음 | 30 + 7년 6개월 ≈ 37 |
| 궤 × david-prime | late 30s · prime | 맞음 | 5:7 정복·5:17 블레셋 뒤, 약 38은 추정이나 모순 없음 |
| 나단 언약 × david-prime | late 30s · prime | 맞음 | 7:1 궁에 평안 · 7:12 미래형 → 솔로몬 출생 전, 약 35~40 |
| 솔로몬 출생 × david-prime | 덮어쓰기 about 50 · middle | 맞음 | 11:1 암몬 전쟁 뒤, 즉위 뒤 약 20년 |
| 기브온 × abner | elder · 60s | 맞음 | 14:50 치세 초기 군장 · 같은 항렬 · 2:10 |
| 궁전 × solomon-prime | middle · 40s | 맞음 | 왕상 6:1·6:38·7:1 → 재위 약 24년 준공 |
| 에시온게벨 × solomon-prime | middle · 40s | 맞음 | 9:10 「이십 년」 뒤 9:26 |
| 스바 × solomon-prime | middle · 40s | 맞음 | 10:4 「그 건축한 궁」 = 7:1 준공 뒤 |
| solomon-prime silhouette lean | — | 맞음 | 체형 본문 없음 |

보류 5건(모순 아님) 처리:
1. 솔로몬 출생 `cast_override_why` — 「약 20년」이 인용만으로 안 나옴 → 보수 연대 추정(즉위 BC 1010 · 출생 약 BC 990)임을 근거 글에 밝힘. **고침.**
2. abner 근거 「사울의 아들이 40세 → 60대」 논증 비약 → 「치세(약 40년) 초기에 이미 군장 · 같은 항렬」을 앞에, 2:10을 뒤 보조로 순서를 바꿈. **고침.**
3. abner v1 `age` 「middle-aged commander」·`_why.age` [저작]이 새 카드(60대)와 어긋남 — `derive_scene.whole_prompt` 시선 대상 문구(「looking toward the <age> …」)가 이 칸을 쓴다. 지금 그 문구로 abner를 보는 명세는 없지만(전 명세 파생 문구에 없음 확인) → `age` 「older commander」 · `_why.age` [추론] 삼상 14:50. **고침.**
4. david-prime 근거에 정복 37의 직접 근거 「헤브론에서 칠 년 육 개월」 인용이 빠짐 → 삼하 5:5 인용을 그 구절까지 넓히고 궤·나단 나이는 「보수 연대 추정」으로 표시. **고침.**
5. solomon-prime 40대는 즉위 약 20세 가정 — 근거가 이미 [저작]으로 정직하게 적혀 있어 그대로.

고친 뒤: `check_cast_v2` 34/34 · 재검 specs 두 규칙 38/38 · 전 규칙 통과 5/38 · images 1/12 그대로 · 단위 시험 OK.
