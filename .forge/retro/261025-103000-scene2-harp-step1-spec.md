# 2026-10-25 — 장면 2 기브아 수금 단계 ① 명세: 규칙 실패 10→0 · 본문 검토 틀림 0 · 새 규칙 seated-height

## 계획 대비 실제
- 계획대로 된 것: 시도 1 원인 분류 → 장면 구절 전부(16:14-23)로 재저작 → 규칙 실패 10→0. 덮지 못하는 원인 하나만 새 규칙으로 만들었음(앉은 사울이 크기 규칙에 빈 통과 → `generate.seated-height` + `sit` 꼴 + 기준표 `body.seated` + 시험 4). 기브아 창 회귀 0, 미커밋 파일 그대로. fg-loop가 한 바퀴에 목표를 달성함(재계획 0/3).
- 벗어남:
  - 계획은 16:18 「호기와 무용」으로 boy/youth를 가르게 했고, 처음엔 david-youth 「약 18세」로 썼음. 그런데 본문 검토 1차에서 틀림이 나옴: 연대 파일(david.json 출생 BC 1040 · 수금 BC 1026)로 셈하면 약 14세이고, 다음 골리앗 장면은 david-boy임. 청년 근거(17:56·18:5)는 골리앗 뒤의 일임 → david-boy로 바꿈.
  - david-boy로 바꾸자 derive.youth-noun이 다시 걸림. 주어 명사는 young man인데 **시선 문구**는 카드 `age` 「shepherd boy」를 그대로 이음 → 이 장면만 cast_override로 덮음. 같은 결함이 골리앗 gath·베들레헴 기름부음 장면에도 있음.
  - 기계 관문은 통과했지만 검토 2차에서 「주의」 7건이 나옴. 대부분 [추론] 표시가 한 칸에만 있고 같은 진술을 담은 다른 칸(meaning·relation·요소)에는 없는 것이었음.

## 배운 것
- 다음엔 다르게:
  - **생애 단계는 연대 파일 셈부터.** stage_why를 쓰기 전에 data/person_events/<인물>.json에서 출생 연도와 이 사건 연도를 빼서 나이를 내고, 앞뒤 장면의 cast id와 맞춰 볼 것. 호칭 구절(「무용」·「병기 든 자」)만 보고 정하지 말 것. 「약 N세」라고 쓸 때는 셈한 숫자만 씀(이번엔 기브아 창 장면의 「약 18세」를 그대로 옮겨 틀림).
  - **[추론]·본문 밖 표시는 진술이 실린 모든 칸에.** gesture.verse에만 붙이고 meaning·relation·verse_elements에는 안 붙이는 일이 되풀이됨. 진술 하나에 칸 여럿이면 다 붙임.
  - **cast_override는 한 장 경로만 탐.** 판(plate·inscene) 경로 stages에는 덮어쓰기가 적용되지 않아 사울이 「40대 · thick barrel torso」로 파생됨. 단계 ② 전에 확인할 것(후속 등록).
  - **파생 문구에는 카드 원문 낱말이 새는 길이 여럿 있음.** _who가 명사를 고쳐도 시선 구절(`looking toward the {age}`)은 카드 낱말을 그대로 씀. 규칙 하나를 고치면 같은 카드 칸을 읽는 다른 파생 자리도 볼 것.
  - **도구:** run.md 후속 표지는 `fu-<12 hex> | source | task | date | status | taken` 꼴만 받음. 자유 이름을 쓰면 봉인이 exit 6으로 멈춤.

## 문서 갱신
- CONTEXT.md 승급: 없음 — 후보 「생애 단계 근거 = 연대 파일 셈 우선」은 사용자 미커밋 파일이라 이번엔 손대지 않음(사람이 정함)
- ADR 추가: 없음
- 판정 기준(eval): 작업 안에서 이미 넣음 — `test_scene_rules.SeatedHeight` 4개(새 규칙 generate.seated-height)

## 후속 후보
<!-- followup: fu-d9aa58668ba9 | source: scene2-harp-step1-spec | task: 414 | date: 2026-10-25 | status: open | taken: - -->
- 판(plate·inscene) 경로 stages S3에 cast_override가 적용되지 않음 — 사울이 「in his 40s · thick barrel torso」로 파생(수금·기브아 창 둘 다 확인 필요). 단계 ② 전에.
<!-- followup: fu-e7d0aba54fd7 | source: scene2-harp-step1-spec | task: 414 | date: 2026-10-25 | status: open | taken: - -->
- david-boy 카드 age 「shepherd boy」가 시선 문구로 이어져 youth-noun 실패 — 골리앗 gath·베들레헴 기름부음 장면 남음. 카드 고침 또는 derive 시선 명사를 _who와 맞춤(사람 결정).
<!-- followup: fu-c2aa43cca3f8 | source: scene2-harp-step1-spec | task: 414 | date: 2026-10-25 | status: open | taken: - -->
- CAST.md ageBand youth(10대) ↔ 원장 youth-noun 설명(15~20) 정의 하나로.
