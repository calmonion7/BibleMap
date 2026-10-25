# 장면 3 두 여인의 재판(왕상 3:16-28) — 단계 ① 명세 (task 415)

본보기: `notes/GIBEAH-STEP1.md`(task 399) · `notes/HARP-STEP1.md`(task 414). 관문 = `recheck.spec_failures('authored-solomon-jerusalem-two-mothers') == []` + scripture-reviewer 틀림 0.

## 시도 1 — 지금 명세(task 332, 2026-09-04 판 경로 명세)

`spec_failures` 10개:

| 규칙 | 상세 | 원인 | 기존 규칙이 덮나 |
|---|---|---|---|
| spec.whole-fields | meaning·relation·whole_background 없음 | 판 경로 명세(한 장 모드 칸 없음) | 덮음 — 재저작 |
| spec.verse-elements | verse_elements 없음 | 구절 시각 요소 목록 미작성 | 덮음 — 재저작 |
| spec.scene-all-verses | situation 없음 | 인용 4절만 · 순간 3:16-22 | 덮음 — 재저작 |
| spec.lexicon-link | 못 잼 | 요소 목록 없음 → 3:24 「칼을」 사전 대조 못 함 | 덮음 — 요소 목록 + 사전 sword L1 |
| derive.prop-in-prompt | 「왕홀」·「아기」·「겉옷자락」 영문 없음 | 한국어 prop | 덮음 — 재저작 |
| spec.stage-from-scripture | 세 인물 stage_why 없음 | 생애 단계 근거 미작성 | 덮음 — 재저작 |
| spec.action-place-on-figure | 못 잼 | 요소 목록 없음 | 덮음 — 3:16 「그 앞에 서며」를 인물 칸에 |
| generate.figure-scale | 못 잼 | guide 없음 | 덮음 — guide 사람 구역 |
| generate.height-ratio | 못 잼 | guide 없음 | 덮음 — guide 사람 구역 |
| derive.held-hold | 참 어머니 「아기」 hug 문구 없음 | 쥔 꼴 문구 미작성 | 덮음 — 사전 baby hold.en |

새 원인 없음 — 규칙을 더하지 않는다(덮지 못하는 원인만 규칙).

### 본문 대조로 드러난 명세 결함(규칙 밖)

- **순간**: 옛 순간 3:16-22(다툼)는 task 332 계획의 순간 선택 지침 — 「모델 prior에 없는 동작은 순간으로 잡지 않는다」 — 을 따른 「브리프 지시」였다. 이는 뒤에 사람이 금지한 타협(메모리 「구절 묘사 타협 금지」, task 394 기브아 18:11)과 같은 꼴이라, 장면 구절 전부로 다시 고른다. 단락이 가장 크게 말하는 것은 3:28 「하나님의 지혜가 저의 속에 있어 판결함」 → 판결의 근거가 보이는 3:26(두 여인의 말이 갈림).
- **아기를 안은 사람**: 옛 명세는 참 어머니가 안음(근거 3:26) — 그러나 3:26은 안았다는 말이 없고, 3:20 「내 아들을 내 곁에서 가져다가 자기의 품에 누이고」로 산 아기는 다른 계집 품에 있었으며, 3:27 「산 아들을 저 계집에게 주고」로 참 어머니는 판결 **뒤에** 받는다. → 다른 계집(mother-b)이 안음([추론]).
- **왕홀**: 3:16-28 본문에 없음(사전 scepter 근거는 에 5:2 바사 왕) → 지물 없음.
- **알현실·보좌**: 7:7 재판하는 낭실·10:18 상아 보좌는 3:1 「자기의 궁 … 필역되기를 기다리니라」 뒤의 일 → 왕의 집 소박한 방 · 나무 자리(앉음은 2:19 [추론]).

## 시도 2 — 장면 구절 전부(3:16-28)로 재저작

- situation(3:16-28 전부 + 자리 3:15·3:1 · 앉음 2:19) · verse_elements 20(실음 8 · 제외 12 — 검토 1차 뒤 24, 제외 16) · 순간 3:26.
- 인물: 솔로몬(앉음 · 지켜봄 · 지물 없음 · 약 21세 solomon — 연대 BC 990 출생 · BC 969 재판, 3:7·9:10) · 참 어머니(서서 빈손을 내밀어 애원 · 3:26 「마음이 불붙는 것 같아서」) · 다른 계집(서서 산 아기를 품에 안음 — 사전 baby L2 + hold.en · 굳은 얼굴 3:26 「나누게 하라」).
- 칼: 3:24 「칼을 왕의 앞으로 가져온지라」 → 배경 칸에 사전 sword L1 「a straight iron sword」, 왕 자리 앞 바닥에 놓임(놓임은 본문 밖 · 저작자 정함). 칼 가져온 사람은 3:24 앞선 일이라 순간 밖.
- guide: room 바탕 · 카드 체격 · 긴 겉옷이라 legs costume 아님 · 두 여인 person · 왕 sit. 구역은 크기 기준표로 셈 — 세 사람 무리 단계 small(0.45~0.60), 초점 다른 계집 0.55 · 발 y 0.92 · 지평선 0.408 · 참 어머니(short) 0.506 · 왕 앉은 키 0.412.
- 시험 `HeldHold.test_hug_prop_without_hold_phrase_fails`는 옛 명세의 실패를 기대로 삼았음 → 고친 명세 사본에서 품에 안은 꼴 문구를 지운 것으로 같은 실패를 잼(시험 의도 유지).

결과: `spec_failures` 10 → **0**(못 잼 0). 기브아 창·수금 회귀 0. 시험 142 OK.

## 검토 1차 — scripture-reviewer 틀림 0 · 주의 9

인용 전부(quotes 13 · 요소 20 · verse 칸 3:1·3:7·3:15·2:19·9:10) 본문 글자 그대로 · 연대 21세 맞음 · 순간 3:26·아기 mother-b·왕홀 뺌·솔로몬 단계·실음/제외 판단 맞음.

| 주의 | 처리 |
|---|---|
| 2 아기 — 3:20은 참 어머니의 아룀, 「누이고」→안음도 추론 | mother-b gesture.verse·meaning.verse·same_time에 「아룀 — 3:27 판결이 확증」·[추론] |
| 3 칼 가져온 사람들이 명세에 없음 · meaning에 칼 놓임 표시 없음 | 제외 요소 3:24 「가져온지라」 · meaning.verse 「칼이 바닥에 놓임은 본문 밖」 |
| 4b 「소박한 방」·「왕의 집」 표시 없음 · 3:1은 「짓기 전」이 아니라 「필역 전」 | whole_background·meaning·situation에 본문 밖 표시 · 「필역 전」으로 약화(삼하 7:2 다윗 궁 언급) |
| 4c 나무 자리 재질 표시 없음 | solomon gesture.verse 「자리 재질·모양은 본문 밖」 |
| 5b mother-a 「첫아이」 근거 없음 | 「아이를 갓 낳은」 |
| 6b 빠진 요소(3:18 · 3:28 두 곳 · 3:24 사람들) | 제외 요소 4개 추가(24개) |
| 6c 「a hard, cold face」 인격 단정 · 시선 표시 없음 | 「a set, unyielding face」(요소·relation·S5 같이) · relation.verse에 시선 근거(3:26 「네 것도 되게 말고」 [추론]·왕의 지켜봄 본문 밖) |
| 7a situation 3:19-20 대명사 모호 | 「아뢴 여인이 잠든 사이에 저 계집이 … 죽은 아들을 아뢴 여인의 품에」 |
| 7b same_time 3:20 아뢴 말 꼬리표 | 붙임 |
| (곁가지) cast/mother-a.json propCandidates `an infant`(3:26 근거) 옛 명세 잔재 | **후속** — 공유 카드라 이번 범위 밖 |

처리 뒤 spec_failures 0 · 기브아 창·수금 회귀 0 · 시험 142 OK.

## 검토 2차 — scripture-reviewer 틀림 0 · 주의 2

| 항목 | 판정 | 처리 |
|---|---|---|
| 새 제외 요소 4개 인용·사유 | 맞음 | — |
| 1차 7a·3·2·4b·4c·5b | 풀림 | — |
| 새 표정 「a set, unyielding face」 · 시선 [추론] 3:26 「네 것도 되게 말고」 | 맞음 | — |
| relation.verse·figures[2].pose의 「굳은 얼굴」 잔재 | 주의 | 「굽히지 않는 얼굴」로 맞춤(표시만) |
| cast/mother-a.json propCandidates `an infant` 잔재 | 주의(범위 밖) | **후속** |

주의 처리는 표시 문구만 바꿈 — 인용·판단은 2차 판정 그대로.

판정표: 틀림 0
