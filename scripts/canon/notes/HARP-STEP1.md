# 장면 2 기브아 수금(삼상 16:14-23) — 단계 ① 명세 (task 414)

본보기: `notes/GIBEAH-STEP1.md`(task 399). 관문 = `recheck.spec_failures('authored-david-gibeah-harp') == []` + scripture-reviewer 틀림 0.

## 시도 1 — 지금 명세(2026-10-19 승인 s11의 명세)

`spec_failures` 10개:

| 규칙 | 상세 | 원인 | 기존 규칙이 덮나 |
|---|---|---|---|
| spec.verse-elements | verse_elements 없음 | 구절 시각 요소 목록 미작성 | 덮음 — 재저작 |
| spec.scene-all-verses | situation 없음 | 16:23 한 절로 씀(16:14-22 문맥 없음) | 덮음 — 재저작 |
| spec.lexicon-link | 못 잼 | 요소 목록 없음 → 수금 사전 문구 대조 못 함 | 덮음 — 요소 목록 + 사전 L2 |
| spec.stage-from-scripture | 다윗·사울 stage_why 없음 | 생애 단계를 본문으로 유추 안 함 | 덮음 — 재저작 |
| spec.action-place-on-figure | 못 잼 | 요소 목록 없음 | 덮음 — 요소 목록 |
| derive.youth-noun | 파생 문구 「boy」 | 명세가 `david-boy`(약 14세) — 그러나 cast가 boy면 이 규칙은 원래 안 걸려야 함: meaning·relation 「boy」가 cast 바뀌기 전 글 | 덮음 — 단계 유추 뒤 문구 |
| derive.no-inflating-build | 「barrel」 | 정본 saul 카드 silhouette 「thick barrel torso」 | 덮음 — 기브아 창처럼 cast_override |
| generate.figure-scale | 못 잼 | guide 없음 | 덮음 — guide 사람 구역 |
| generate.youth-height | 못 잼 | guide 없음 | 덮음 — guide 사람 구역 |
| generate.height-ratio | 못 잼 | guide 없음 | **일부만** — 아래 |

### 새 원인 — 앉은 사람의 화면 크기를 재는 규칙이 없다

본문으로 자세를 정하면: 다윗은 16:21 「그 앞에 모셔 서매」·16:22 「내 앞에 모셔 서게 하라」 → 서서 탐(지금 명세의 「앉아서 탄다」는 본문과 어긋남). 사울은 19:9 「사울이 손에 단창을 가지고 그 집에 앉았을 때에 … 다윗이 손으로 수금을 탈 때에」 → 수금을 들을 때 앉음([추론] — 다른 날이나 같은 자리의 평소 모습).

그런데 크기 규칙(figure-scale·youth-height·height-ratio)은 **서 있는** 사람 구역만 잰다(`S.standing` — 앉음 꼴은 빠짐). 앉은 사울을 넣으면 사울 화면 크기는 어느 규칙에도 걸리지 않는 **빈 통과**가 된다(task 413이 막은 꼴). → 새 규칙 `generate.seated-height`: 앉은 꼴(guide.shape `sit`) 인물의 구역 높이 = 눈높이 지평선에서 그 발 y의 화면 키 × 카드 키 등급 × 크기 기준표 `body.seated` ± 초점 키의 0.04. 서 있는 초점이 없으면 못 잼.

### 다윗 생애 단계

16:18 「호기와 무용과 구변이 있는 준수한 자」·16:21 「자기의 병기 든 자를 삼고」 — 무용 있는 자·병기 든 자는 아이가 아님. 17:33 「너는 소년이요」·17:42 「젊고」 — 아직 젊음. 다윗 즉위 30세(삼하 5:4)는 한참 뒤 → david-youth(15~20). 「소년」 한 낱말로 david-boy를 고르지 않음(기브아 창 399와 같은 근거 방식).

## 시도 2 — 장면 구절 전부(16:14-23)로 재저작 + 새 규칙 generate.seated-height

- situation(16:14-23 + 지리 15:34 · 앉음 19:9) · verse_elements 15(실음 6 · 제외 9 — 앞선 날 의논·천거·예물, 병기 든 직분, 「모셔 서게 하라」는 16:21 요소가 실음) · 순간 16:23 「상쾌하여 낫고 … 떠나더라」.
- 다윗 `david-boy` → `david-youth`(stage_why [추론] 16:18·16:21·삼하 5:4) — 「boy」 문구 사라짐(derive.youth-noun 통과). 앉아서 탐 → 16:21 「모셔 서매」로 서서 탐(자리 요소 → figures[0].gesture).
- 사울: 19:9 [추론] 걸상에 앉음 · 단창은 19:9 그날 일이라 뺌 · 지물 「a plain traveling cloak」(본문 밖) 뺌 → prop none · cast_override 약 70세·「a strong solid chest」(no-inflating-build, 기브아 창과 같음).
- 수금: 사전 kinnor-lyre L2 문구(lexicon-link) · 쥔 꼴은 사전 hug add(바탕에서 빼고 편집으로 — held-hold ②는 add 제외).
- guide: room 바탕 · 카드 체격 · 무릎 다리 · 다윗 person(구역 높이 0.65, duo 0.60~0.70) · 사울 새 꼴 `sit`(make_guide) — 앉은 키 0.587 = 0.65 × tall 1.205 × body.seated 0.75(크기 기준표에 새 값, [저작] 인체 계측).
- 새 규칙 `generate.seated-height`(원장 판 bac0f1d2cb3c, 73규칙) — 검사 함수 `recheck.seated_height_errors` + 시험 `test_scene_rules.SeatedHeight` 4개(통과·앉았는데 선 키면 실패·서 있는 초점 없으면 못 잼·꼴 등록).

결과: `spec_failures` 10 → **0**. `recheck.py specs` 전 규칙 통과 2/37(기브아 창·수금). 기브아 창 회귀 0. 시험 138 → 142 OK. 승인 그림(s11, 옛 명세)은 spec_hash가 달라져 낡음 — 승인 취소는 사람(ADR 260905-104910).

## 검토 1차 — scripture-reviewer 틀림 1 · 주의 4

- **틀림 3-a**: 다윗 「약 18세 david-youth」 — 연대 파일(data/person_events/david.json 출생 BC 1040 · 수금 BC 1026 · 골리앗 BC 1025)로 약 14세, 다음 골리앗 장면은 david-boy → 나이가 거꾸로 됨. 청년 근거(17:56 「청년」·18:5 「군대의 장」)는 골리앗 뒤 일. → **david-boy**로(검토 제안 (가) — 연대·다음 장면과 맞음, 이 명세 안에서 닫힘).
- 주의 → 고침: moment.why 16:21/16:22 꼴 구분 · 서서 탐 = 16:21에서 [추론] · 걸상 「본문 밖」 · 사울 약 64세(13:1 + 수금 BC 1026, override 「in his mid-60s」).
- david-boy로 바꾸니 derive.youth-noun 다시 걸림: 주어 명사는 young man(카드 ageBand youth about 14 → 사람 결정 2026-10-23)인데 **시선 문구**가 카드 `age` 「shepherd boy」를 그대로 이음(looking toward the shepherd boy). 이 장면만 cast_override `age: "young shepherd"`. 카드·같은 실패를 가진 다른 david-boy 장면(골리앗 gath·베들레헴 기름부음)은 범위 밖 → 재검 목록.
- 다윗 키 등급 short(0.92)로 지평선이 바뀌어 사울 앉은 구역 위끝 0.363 → 0.311(작성 스크립트가 기준표로 셈).

결과: spec_failures 0 · 기브아 창 회귀 0 · 시험 142 OK.

## 검토 2차 — scripture-reviewer 틀림 0 · 주의 7

| 항목 | 판정 | 처리 |
|---|---|---|
| 틀림 3-a 다윗 나이 | 맞음(풀림) | david-boy · 연대 BC 1026 약 14세 |
| 시선 「young shepherd」 | 맞음(풀림) | — |
| 16:21/16:22 구분 · 걸상 본문 밖 | 맞음(풀림) | — |
| 서 있음 [추론] — meaning·relation·요소 16:21에 표시 없음 | 주의 | 세 곳에 [추론] 덧붙임 |
| 장소 기브아 · 사울 앉음 [추론] 표시 빠짐 | 주의 | situation·meaning·figures[1].verse에 [추론] |
| relation 눈 감음 본문 밖 표시 | 주의 | 덧붙임 |
| 다윗 차림 근거가 「david-youth 카드」 | 주의 | 「기브아 창과 같은 문구 — david-boy 카드 띠와 다름」 |
| 16:17 · 16:21 「크게 사랑하여」 요소 판단 없음 | 주의 | 둘 다 제외(out) 요소로 넣음 |
| 사울 나이·체격 cast_override가 판(plate·inscene) 경로 stages S3에 적용 안 됨 | 주의 | **후속** — 단계 ②에서 판 경로를 쓰면 먼저 고칠 것(기브아 창도 같은 동작일 수 있음) |
| CAST.md ageBand youth(10대) ↔ 원장 youth-noun 설명(15~20) | 주의(범위 밖) | **후속** — 정의 하나로 |

주의 처리는 표시(verse·ko·out 칸)만 바꿈 — 인용·연대·실음 판단은 2차 판정 그대로. 처리 뒤 spec_failures 0 · 기브아 창 0 · 시험 142 OK.

판정표: 틀림 0
