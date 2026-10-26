# 장면 1 기브아 창 · 단계 ① 명세 (task 399)

무인화 규칙을 **장면 × 단계 누적**으로 쌓는 첫 칸(사용자 2026-10-22 「하나씩 스텝별로 … 누적으로 보완」·「가 -> 나 둘다 적용」). 단계 = ① 명세 → ② 그림 문구·구도 가이드 → ③ 생성·기계 거르기 → ④ 사람 승인. 한 단계가 통과할 때까지 「시도 → 실패 원인 → 규칙 추가(검사 함수까지) → 재시도」, 통과하면 다음 단계. 새 규칙은 앞서 끝낸 장면·단계를 다시 재 회귀를 본다.

**단계 ① 통과** = ⓐ `recheck.spec_failures(sid)` 빈 목록(그 명세에 걸리는 명세·파생 함수 규칙 0, 못 잼도 통과 아님) ⓑ scripture-reviewer 실질 틀림 0.

## 시도 기록

- **시도 1** (지금 명세, 394 재저작본): `spec_failures` = `spec.verse-elements`(구절 시각 요소 목록 없음). 397 사람 메모 중 명세 단계 원인 ③ 「다윗은 벽에 붙어서 창을 피하는 모습이어야함」(18:11 「벽에 박으리라」 — 명세엔 배경 `a bare wall behind David`뿐, 다윗 자리·몸짓에 벽 없음) · ④ 「다윗의 나이가 청소년기 — 15~20 정도, 유추 가능」(명세 `david-boy` 14 — 근거가 17:33 「소년」 한 낱말 · `david` 카드 근거엔 이미 「기브아 창~시글락은 20대」라 카드끼리도 어긋남).
  - 더한 규칙: **`generate.spec-gate`**(생성 관문 — 397은 verse-elements ✗ 명세로 그려졌다. 규칙은 있었는데 그리기 전에 막는 장치가 없었다) · **`spec.stage-from-scripture`**(인물마다 `stage_why` = `[직접]|[추론]` + 「인용」 + 장:절, 호칭 하나가 아니라 직무·연대 단서 · 비어 있는 단계면 카드 신설) · **`spec.action-place-on-figure`**(요소 종류 `자리` = 행동이 겨누는 곳·인물이 있어야 할 곳 → 인물 칸이 나름).
- **시도 2** (새 규칙 셋을 건 같은 명세): `spec_failures` = verse-elements · stage-from-scripture(saul·david-boy 근거 없음) · action-place-on-figure(목록 없어 못 잼).
  - 재저작: 구절 시각 요소 12(실음 9 · 제외 3 — 18:6·18:7 전날 일, 18:11 「두 번」 중 다른 한 번) · 18:11 「내가 다윗을 벽에 박으리라」 = `자리` → 다윗 몸짓 `standing with his back against the stone wall` · 사울 몸짓 빈손 `his empty throwing hand stretched out toward David`(「던졌으나」 — 던졌으니 손이 빔) · relation에 「다윗과 그 뒤 벽 쪽으로」 · 다윗 cast `david-youth`(새 카드, 15~20 — 17:56 「청년」·18:5 「군대의 장」·18:13 「천부장」·18:27 혼인·삼하 5:4 「삼십 세에 위에」) · 사울 `stage_why`(13:1 「사십 세」 + 재위 중 → 장년 saul).
  - 결과: `spec_failures` = `[]`(ⓐ 통과) → 성경 검토 1차.
- **시도 3** (검토 1차 실질 3): ① 판 단계 S2·S3가 18:10 시점(사울 「gripping one spear upright」·neg throwing / 다윗 「sitting … playing」·neg standing·fleeing — 순간을 neg가 막음) ② 사울 지물 `a spear` — 판정자에게 「지물: a spear」로 넘어가 「창이 손에 남은」 그림이 맞음으로 지나갈 수 있음 ③ 사울 「40대」 — 프로젝트 연대(선출 BC 1050 → 이 사건 BC 1020)와 13:1 「사십 세」면 약 70세. 경미 6(18:8 처리 · 때 · 인물 요소 · 자리 표기 · 구역 설명 · 제목).
  - 고침: S2·S3 순간으로·다윗 구역 세로 0.50 · 사울 prop `none`(창은 relation이 나름) · 사울 `stage_why` 연대로 + `cast_override` 이 장면 카드 「about 70」·회색 수염·머리(정본 saul 카드는 9장면에 걸려 그 장면 차례) · 18:8 제외(전날) · 인물 요소 둘 · 제목 「창을 던지다」.
  - 결과: `spec_failures` `[]` → 검토 2차.
- **시도 4** (검토 2차 실질 1): 사울 `stage_why`의 삼하 2:10 인용에 「비로소」가 빠짐 — 그 낱말이 하한 추론을 흔듦. 경미 2(「그 이튿날」 제외 사유가 규칙 밖 · 9:2 인용이 본문 꼴 아님).
  - 더한 규칙(보강): **`spec.stage-from-scripture`에 인용 대조** — `stage_why`의 「인용」마다 책 이름·장:절이 붙어야 하고 본문 글자 그대로(띄어쓰기 무시, `…`로 끊음 — `check_cast_v2` (c2)와 같은 대조). 보강하자마자 같은 틀림을 기계가 잡음(삼하 2:10 + 책 이름 없는 인용 4). 「」는 본문 인용에만, 본문 아닌 낱말·사용자 말은 ‘ ’·“ ”.
  - 고침: 인용 글자 그대로·하한은 가정을 드러내 약하게 · 「그 이튿날」 요소 뺌 · 9:2 본문 꼴.
  - 결과: `spec_failures` `[]` → 검토 3차 **틀림 0**(경미 2 — `cast_override_why` 표기, 바로 맞춤).

## 더한 것 (코드·데이터)

- `recheck.spec_failures(sid)` · `recheck.require_pass(sid)` — 관문. 정본 생성 명령 `gibeah_redraw gen` · `run_night one|all|edit-pick` · `restyle_try gen`이 첫 GPU 호출 전에 부름. `plain_words` 사다리는 명세 **사본** 실험이라 뺌(사본의 토큰 검사는 venv 왕복이 하나 더 필요 — 사본이 정본이 되면 관문을 지난다).
- `recheck.stage_why_errors` · `check_scenes.place_on_figure_errors` · `params.VERSE_ELEMENT_KINDS`에 `자리`.
- `cast/david-youth.json`(얼굴 층 = david-boy와 같음, 정본 그림 없음) · `check_cast_v2.STAGES` 다윗 단계 묶음 · `CAST.md` 표·분할 문장 · `APPEARANCE-VERSES.md` 5줄 · `david-boy` 정차지에서 기브아 창 뺌 · 판정 화면 이름표 `청년 다윗`(기존 시험 `test_every_cast_named`가 빈칸을 잡음).
- `rules.json` 3항목(규칙 34) · `test_scene_rules.py` 14개(관문 4 · 생애 단계 6 · 자리 4).

## 재검 (전 명세, `recheck.py specs`)

- 전 규칙 통과 1/37 = **기브아 창**(전에는 요단 — 요단은 새 `stage-from-scripture`에 걸림: 새 규칙 칸이라 회귀 아님, 그 장면 차례에 채움).
- 새 규칙: `stage-from-scripture` 1/37 · `action-place-on-figure` 15/37(못 잼 22 = 요소 목록 없는 명세).
- 기존 규칙 칸 통과→실패 0(9b29989 대비, 아둘람 제외).

## 성경 검토 (ⓑ)

| 차수 | 실질 틀림 | 내용 | 경미 |
|---|---|---|---|
| 1차 | 3 | 판 단계 S2·S3 18:10 시점 · 사울 지물 a spear · 사울 나이 40대(연대상 약 70) | 6 |
| 2차 | 1 | 삼하 2:10 인용 「비로소」 빠짐 → 인용 대조 규칙 보강 | 2 |
| 3차 | 0 | — | 2(표기, 맞춤) |

판정표: 틀림 0

## 단계 ① 통과 (2026-10-22)

- ⓐ `spec_failures('authored-saul-gibeah-spear')` = `[]` · ⓑ 성경 검토 3차 틀림 0.
- 누적 규칙(장면 1 단계 ①): `generate.spec-gate` · `spec.stage-from-scripture`(+ 인용 본문 대조) · `spec.action-place-on-figure`.
- 다음 단계 ②③ 재료(검토 「참고」): 파생 문구가 `youth` 대를 「boy」로 씀(`derive_scene._who` — 15~20 청년을 어리게 끌 수 있음) · 악기 낱말이 셋으로 갈림(figure `a small wooden lyre` / S3 같음 / david-youth 카드 propCandidates `a small harp`) — 메모 ② 「하프가 아님」과 함께 낱말 사전에서 정함.
- 기록만(다른 장면 차례): 정본 saul 카드 ‘in his 40s’·saul-old ‘60s’가 프로젝트 연대(사울 사망 BC 1010경 약 80세)와 어긋남 · 판 경로 `plate_whole_prompt`는 `cast_override`를 적용하지 않음(지금 생성 경로 밖) · 새 규칙에 걸린 다른 명세 = 재검 표(`stage-from-scripture` 36 · `action-place-on-figure` 못 잼 22).
