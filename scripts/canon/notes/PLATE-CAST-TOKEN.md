# 판 경로 인물 단계는 카드 자리표로 (task 426, 2026-10-26)

후속 fu-7e2d(다윗 장년 판 문구 「lean young man」) · fu-59f9(요단 금관 근거). GPU 0 — 다시 그리기 없음.

## 무엇이 틀렸나

판(plate) 인물 단계 14개(9장면)가 `{cast:<구역>}` 자리표 없이 인물 문구를 손으로 적었다. 생애 단계 나눔(task 355) 뒤
카드가 david-prime(40대 왕)·david-elder(60 전후 왕)로 바뀌었는데 판 문구는 「an ancient Israelite lean young man」 그대로 —
ADR 260904-055320 1항(장면 판 프롬프트의 `{cast:<id>}`와 판 시트가 같은 문구) 위반. 재검 규칙이 이것을 재지 않았다.

## 고친 것

- 원장 새 규칙 `derive.plate-cast-token`(check `recheck.plate_cast_token_errors`) — 구역이 cast id인 판 단계 문구에 `{cast:<구역>}`.
- 14단계를 `{cast:<구역>}, <자세·지물·방향>` 꼴로. 카드에 있는 정체·차림 낱말(나이·수염·갑옷 등)은 단계 문구에서 뺌.
- 구절 요소 검사(`check_scenes.verse_element_errors`)는 칸 원문을 **자리표를 채운 뒤** 대조 — 정체 요소(「다윗」「나단」「아브넬」)의 en이 카드 문구(`an ancient Israelite man, a king` 등)로 짝지어진다.
- 궤(삼하 6:14): david-prime `cast_override` costume "" — 카드 왕의 겉옷을 빼고 단계 문구 「wearing a linen ephod」만.
- 요단 귀환 금관: 근거를 삼하 12:30([추론] 「보석 있는 면류관 … 다윗이 머리에 쓰니라」)으로, 문구 「a thin gold circlet」 → 「a gold crown set with a precious stone」.

## 수치 (DoD)

| 항목 | 전 | 뒤 |
|---|---|---|
| 자리표 없는 판 인물 단계 | 14 | 0 |
| 원장 `derive.plate-cast-token` | 없음 | 있음(원장 79규칙) |
| recheck specs `derive.plate-cast-token` 실패 | — | 0/38 |
| `derive.512-tokens` 실패 | 0 | 0 (요단 505 · 골리앗 508 · 판 경로 7장면 183~360) |
| 전 규칙 통과 | 5/38 | 5/38 |
| `spec.verse-elements` 실패 | 19 | 19 (실패 집합 같음 — 골리앗·기혼은 요소 목록 없음) |
| unittest test_scene_rules test_recheck test_judge_crop | 172 OK | 174 OK |

## 승인 그림 재검 (recheck images — 표시만, 승인 취소 없음)

- 새로 낡음이 된 승인 그림 0장. 바뀐 9장면 중 승인 그림이 있는 것은 요단 귀환(r6 s101)뿐이고, 이미 「그림 뒤 명세가 바뀜」으로 전 규칙 낡음이었다(새 규칙 칸만 더해짐 39 → 40).
- 「명세 바뀜」 8장(기브아 수금·요단 귀환·베들레헴·라마·길갈 즉위·야베스·믹마스·미스바) 모두 새 칸 낡음 — 같은 사유.
- 통과하던 4장(가드·기브아 창·길갈 아말렉·놉)은 새 규칙도 통과. 잰 규칙 모두 통과 1/12 그대로.

## 본문 검토 (scripture-reviewer)

1차 판정: 9장면 × 인물 — 틀림 4 · 보류 4 · 나머지 맞음.

| 틀림 | 고침 |
|---|---|
| 헤브론 david-prime 나이 「in his 40s」 — 2:4 기름부음은 즉위 순간(삼하 5:4 「삼십 세에 위에 나아가서」) | 장면 `cast_override.card.ageBand` 「about 30」([추론] 5:4) |
| 기브온 아브넬 「in his 30s」 — 삼상 14:50 사울 치세 초기부터 군장 · 삼하 2:10 이스보셋 40세 즉위 | 장면 `cast_override.card.ageBand` elder 「in his 60s」([추론]) |
| 골리앗 david-boy 「young man, about 14」 — 삼상 17:33 「너는 소년이요」 | 이 작업 밖 — task 419 사람 결정(`_who` youth→young man, boy 금지는 15세 이상만). 한 장 경로는 전부터 같은 문구 → 후속 |
| 요단 12:30 인용 「금 한 달란트」 — 개역한글 원문 「한 금 달란트」 | 원문대로(why·verse_elements ko 두 곳) |

함께 고친 것: 기브온 두 지휘관 차림 — 판 문구에 있던 376 사람 메모 무장(「두 지휘관 옷이 시대를 반영하지 못함」)이 자리표로 바뀌며 카드 차림(아브넬 가죽 흉갑·요압 붉은 튜닉)에 덮였다 → 장면 `cast_override.costume` = 장면 `figures.costume` en으로 되살림. 궤 `_why`의 카드 인용을 원문대로.

보류(본문 모순 아님 — 카드 정차지 대표값 한계): 헤브론 즉위 순간의 왕 겉옷(카드 근거 「즉위 뒤」) · 예루살렘 정복 약 37세·궤 약 38세에 「in his 40s」. 요단 금관 모양 「a gold crown set with a precious stone」·[추론] 표기는 맞음.

재판정(고친 뒤): **틀림 0** — 헤브론 30세 · 아브넬 60대(14:50·2:10 원문 인용 일치) · 두 지휘관 무장 · 12:30 「한 금 달란트」 · 궤 인용 모두 맞음. david-boy는 검토자가 틀림을 철회해 보류(14세 boy는 허용일 뿐 필수 아님 — 다만 「young man」과 「about 14 … boyish torso」가 한 문장에 섞이는 품질 문제는 카드 후속).

## 후속

- david-prime 카드 ageBand 「in his 40s」 하나가 정차지 30(헤브론)~50(솔로몬 출생)을 못 덮음 — 카드 「late 30s」로 낮추거나 정차지별 override(카드 고치기는 이 작업 밖).
- abner 카드 ageBand 「in his 30s」 ↔ 삼상 14:50·삼하 2:10(60대) — 카드 정본 고침(지금은 기브온 장면 override).
- david-boy 「an ancient Israelite young man … about 14 … thin boyish torso」 혼선 — 14세 이하 youth의 명사(`_who`) 또는 카드 class(사람 결정, task 419 후속).
