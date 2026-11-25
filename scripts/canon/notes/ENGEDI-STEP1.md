# ENGEDI-STEP1 — 엔게디 굴(다윗과 사울, 삼상 24:1-5) 단계 ① 명세 · ② 파생

장면 `authored-david-en-gedi-saul` · task 687(동굴 유형 개척 1/2) · 2026-11-25 · GPU 0.
정한 것(plan 687): 순간 = 24:4 굴 안 · 다윗은 겉옷자락을 **「자르는 중」**(사람 결정 2026-11-25 — 옛 「방금 벤 조각을 듦」을 바꿈) · 사울은 어귀 쪽을 보며 다윗에게 등을 두고 웅크림(옛 사람 결정 2026-10-14) · 몸 방향은 뼈대 가이드로.

## 시도 1 — 걸린 규칙 (2026-11-25, 옛 판 명세)

| 규칙 | 걸린 까닭 |
|---|---|
| `spec.verse-elements` | `verse_elements` 없음 |
| `spec.scene-all-verses` | `situation` 칸 없음 |
| `spec.lexicon-link` | 요소 목록이 없어 못 잼 |
| `spec.stage-from-scripture` | david·saul-elder `stage_why` 없음 |
| `spec.action-place-on-figure` | 요소 목록이 없어 못 잼 |
| `generate.figure-scale`·`height-ratio`·`eye-level-perspective` | `guide`가 없어 못 잼 |
| `spec.crowd-era-dress` | 무리(다윗의 사람들) 옷 문구 없음 |

## 장면 구절 — 같은 때의 절만

`verses.range` 「삼상 24:1-22」 → **「삼상 24:1-5」**(스킬 단계 ① 1 — 같은 때의 절만, 기브온 선례). 옛 인용 24:10·24:11(굴 밖에서 한 말)은 빼고 situation 근거로만 씀.

| 절 | same_time |
|---|---|
| 24:1 | 순간 앞 — 블레셋 추격에서 돌아와 다윗이 엔게디 황무지에 있다는 말을 들음 · 자리가 남음 |
| 24:2 | 순간 앞 — 택한 사람 삼천을 거느리고 들염소 바위로 감 · 바위 지대가 남고 삼천은 굴 밖 |
| 24:3 | 순간 바로 앞 — 사울이 굴에 들어감 · 다윗과 그의 사람들이 굴 깊은 곳에 있음(순간에 남음) |
| 24:4 | **고정한 순간** — 사람들의 말 바로 뒤, 다윗이 일어나 사울의 겉옷자락을 가만히 벰(베는 중) |
| 24:5 | 바로 뒤 — 「그리한 후에」 마음이 찔림(순간 밖) |

지리: 엔게디 황무지(24:1)의 들염소 바위 지대(24:2) · 길 가 양의 우리 곁의 굴(24:3). 화면은 굴 깊은 곳 안쪽에서 본 굴 안 — 어귀는 오른쪽 멀리 작은 밝은 구멍(그 바로 바깥에 양의 우리 낮은 돌담 — 1차 검토 뒤), 사울은 가운데 오른쪽, 다윗은 왼쪽에서 무릎으로 다가옴, 다윗의 사람들은 왼쪽 깊은 어둠(좌우·자리 저작 — 2026-10-14 사람 결정).

## 낱말 사전 — 새 항목 셋 (`data/scripture_words/words.json`)

| id | 표제어 | look L1 en | 크기·쥠 | 결정 |
|---|---|---|---|---|
| `outer-robe` | 겉옷(forms 겉옷자락·겉옷을·겉옷만·겉옷과·겉옷으로) | `wool robe` | size 0.79 「reaching to the ankles」(L2에 있음) · held 없음 | 24:4·15:27·28:14가 같은 「겉옷」. **L1을 「wool robe」 두 낱말로 한 까닭**: 이 낱말은 이미 길갈(15:27 지물 요소 「겉옷자락」, 승인 장면)·엔돌(28:14)이 싣는다 — 새 항목이 생기면 spec.lexicon-link가 그 장면 프롬프트에도 L 문구를 요구하는데, 두 장면 문구(「a long dark brown wool robe」·「a long dark wool robe」) 안에 글자 그대로 있는 가장 짧은 구가 「wool robe」다(승인 장면 문구를 다시 쓰지 않게 · AUTHORING 「크기」 절 끝). spec.prop-size-relative도 길갈 요소를 따라 이 항목에 size를 요구해서 size를 넣음. 실측: 길갈 관문 그대로 `([], {})` · 엔돌 실패 목록 그대로(lexicon-link·prop-size 새 실패 없음) |
| `cave` | 굴(forms 굴이·굴에·굴에서·굴로·굴을·굴과·굴 깊은 곳·굴 어귀 · exclude 얼굴·굴복·굴레·굴려 등 22) | `a deep rock cave` | 없음(장소) | 장면 요소는 kind 장소라 lexicon-link 대상 밖이지만 whole_background에 L1을 실음 |
| `penknife` | 소도(forms 소도로 · exclude 처소도·아소도·양도 소도 등) | `a small iron knife` | size 0.12 「about as long as a hand」 · held 「a small knife」 · hold hand | **본문에 칼 낱말이 없다** — 날붙이는 [추론] 24:4 「베니라」, 작은 칼은 본문 밖 · 저작자 정함(사람 결정 2026-11-25). 사전 표제어는 본문 낱말이어야 refs 용례 검증을 지나서 렘 36:23 「왕이 소도로 그것을 연하여 베어」(KJV penknife)의 「소도」로. 사전 `sword`(칼, 0.35)와 따로 둠 |

- `scripts/canon/scale.json` `held_exclude`의 「a small knife」(재검 줄 — 「정하면 이 줄을 지움」)를 지움 → 이제 사전 penknife held가 크기를 맡음(spec 통과 그대로). `notes/SCALE.md` 재검 2에 해소 한 줄.
- 사전 검증기 `backend/scripts/validate_scripture_words.py`: 위반 5건 그대로(전부 옛 항목 — oil-horn·precious-stones·gold·sacrifice) · 새 항목 위반 0.

## 보완 — 걸린 규칙마다

| 규칙 | 보완 | 결과 |
|---|---|---|
| `spec.scene-all-verses` | `situation`(text · same_time 24:1~24:5 · 지리 · 다윗의 사람들·삼천·도구의 근거 단계) | 통과 |
| `spec.verse-elements` | 요소 20개(실음 14 · 제외 6 — 1차 검토 뒤 양의 우리를 실음으로 · 「일어나서」를 제외로 바꿔 수는 같음). 실음 en은 칸 영문에 글자 그대로 | 통과 |
| `spec.lexicon-link` | 지물 요소 24:4 「사울의 겉옷자락」 → 사울 costume 「a long dark wool robe」(L1 「wool robe」 포함) | 통과 |
| `spec.stage-from-scripture` | david: [추론] 삼상 23:29 · 삼하 5:4 · 삼상 18:13·18:27 · 23:13 + 연대 정본(출생 BC 1040 · 엔게디 BC 1011) → 약 29 → id david · saul-elder: [추론] 삼상 13:1 · 행 13:21 + 연대(선출 BC 1050) → 약 79 · 삼상 24:2 「택한 사람 삼천을 거느리고」(기력) → 28:20 이전 → saul-elder | 통과 |
| `spec.action-place-on-figure` | 자리 요소 24:3 「그 굴 깊은 곳」 → `figures[0].gesture`(「out of the dark depths of the cave」) | 통과 |
| `spec.crowd-era-dress` | 무리 costume 「men in plain wool tunics and cloaks with leather belts」 → relation에 실음 · 무리 구역을 다윗 구역에서 떼어 `men`으로 | 통과 |
| `generate.figure-scale`·`height-ratio`·`eye-level-perspective` | `guide` 새로(아래) | 통과 |

옛 판 칸 맞춤: `stages`(S1 굴 안 · S1c 어귀 · S2 무리 · S3 다윗 무릎 꿇고 베는 중 · S4 사울 웅크림 — 옛 S3·S4는 24:8 굴 밖 엎드림·돌아봄이었음, 옛 S1b 절벽은 굴 안 화면에 없어 뺌) · `regions`(cliff·cave → mouth·men·hem) · `judge.gap_bands`(무리와 다윗 사이 0.19~0.33 · 사울과 어귀 사이 0.74~0.84) · `background` · `moment.why`(「자르는 중」 결정).

문구에서 바꾼 것(옛 명세 → 새):
- 다윗 몸짓 「holding up the corner piece he has just cut」 → 「one hand lifting a corner of the robe slightly off the ground, the other hand slicing through the cloth with a small iron knife」 · 시선 「looking down at the cut-off piece」 → 「looking down at his hands and the cloth」.
- 사울 몸짓 「his back to the man on the left」는 그대로(task 365 B 마주 봄 0/8 문구) · 시선 예약값 `ahead`(「toward the right edge」 — 몸 방향 구절과 「right edge」 두 번, 스킬 함정 192)를 문구 객체 「looking toward the far cave mouth, unaware」로.
- `screen_light` 「… lights only these two men」 그대로(task 364 — 빼면 자세가 무너짐).
- 지명(엔게디)은 영문에 없음 — 굴 밖 황무지는 「a small bright opening」(어귀의 낮빛)으로만(1차 검토 뒤 저작 「bright bare rocky hills」를 빼고 본문의 양의 우리를 실음).

## 구도 가이드 (`guide`)

- 무리 단계 small(사람 8 → 초점 0.45~0.60). 다윗이 가장 앞·가장 큰 초점(구역 0.59 · 발 0.96) → 지평선 0.411. 사울은 한 걸음 뒤(발 0.86) · 카드 tall → 구역 0.5814. 같은 발 y면 다윗이 0.49로 작아져 숙인 뼈대 보이는 키(0.61 × 키)가 하한 0.3375에 못 미쳐서 다윗을 앞으로.
- 자리 낱말: 무리가 있어 3등분 규칙 — 다윗 가운데 x 0.37(「On the left」) · 사울 0.62(「On the right」), 「In the center」 인물 없음.
- **새 뼈대 둘**(`batch/make_guide.py` POSES — task 687 주석): `crouch_away_right`(사울 — 화면 오른쪽을 보고 발뒤꿈치 위에 낮게 웅크림, 엉덩이 0.81, 두 아래팔을 무릎 위에, 옆얼굴 14·16) · `kneel_cut_right`(다윗 — 두 무릎 꿇고 위몸 약 50° 숙임, 고개를 숙여 손을 봄, 가까운 손 0.40·0.86 귀퉁이를 듦, 먼 손 0.44·0.82 그 너머에서 칼 — 먼 손을 더 앞에 두어 두 손 보임). 옛 뼈대는 바꾸지 않음.
- **새 꼴 둘**(SHAPES): `cloak_trail`(사울 엉덩이에서 다윗 손까지 땅에 끌린 겉옷 자락 — 왼쪽 끝 귀퉁이만 손 높이로 들림. 뼈대는 손 자리만 주고 천 자리는 못 줌) · `cave_mouth`(먼 어귀 — 깊이 0, 기준 ②). 웅크린 몸은 옛 꼴 `person` + 뼈대(pose_body)로 충분해서 새 몸 꼴은 만들지 않음.
- 실내 배경 문구(inside) → `backdrop: room`(generate.guide-backdrop) · `body: card` · `split: true`.
- 깊이: 어귀 0 · 무리 0.3 · 사울 0.8 · 자락 0.85 · 다윗 1.0.
- 다른 장면 가이드 화소 불변: engedi_checks C7 「다른 장면 가이드 바뀜 0/29」.

가이드 그림: `samples/engedi-step1/guide-1.png`(뼈대 단계) · `samples/engedi-step1/guide-2.png`(깊이 단계).
본 것: 사울은 화면 오른쪽에서 몸을 오른쪽(먼 어귀 — 오른쪽 위 검은 작은 구멍)으로 숙여 웅크리고 등이 왼쪽을 향함. 다윗은 왼쪽 가운데에서 두 무릎을 땅에 대고 위몸을 오른쪽으로 숙였고, 두 손목이 사울 엉덩이에서 내려온 밝은 자락 덩어리의 왼쪽 끝(들린 귀퉁이)에 함께 모임. 두 사람 얼굴은 같은 쪽(오른쪽·오른쪽 아래)을 향해 마주 보지 않음. 무리는 왼쪽 먼 곳 어두운 실루엣 4~5. 남은 걱정(2/2에서 볼 것): 깊이 단계의 사울 몸 덩어리가 웅크림보다 「숙여 선 사람」처럼 위로 길어 보임 · 무리 꼴은 사람 수를 6으로 맞추지 않음(함정 166).
- 가이드 눈 확인: 통과 — 사울 등이 다윗 쪽 · 다윗 두 손이 겉옷 귀퉁이 자리 (samples/engedi-step1/guide-1.png · guide-2.png)

## 단계 ② 파생

- `derive_scene.py --check --figures whole` → 「whole 통과」 · 한 장 프롬프트 **484토큰**(≤ 512).
- 눈으로 본 것: 머리 낱말 「On the left:」(다윗)·「On the right:」(사울) 하나씩 · 지물 「small iron knife」가 다윗 몸짓에 · 겉옷 「a long dark wool robe」가 사울 차림에 · 무리 옷 문구가 관계 문장에 · 지명 없음 · 「right edge」는 배경 1 · 인물마다 방향 구절 1(같은 인물 절 안 두 번 없음).

## 회귀

- 관문 `spec_failures` → `([], {})`.
- `recheck.py specs` → 전 규칙 통과 **27/41**(26 → 27).
- 시험 4모듈: 250개 중 **1 실패**(→ 뒤에 코디네이터가 시험을 고정 사본 `samples/engedi-aftercut/spec.json`으로 바꿔 250 OK — 아래 1차 반영 검증) — `test_whole_prompt.GazeObject.test_engedi_matches_adopted_C`. 이 시험은 엔게디 명세의 파생 프롬프트가 옛 채택 C(`samples/engedi-aftercut/metrics.json` 「막 자른 뒤」)와 글자까지 같아야 한다고 묶는다 — 사람 결정 2026-11-25(「자르는 중」)로 명세가 C를 대신하니 명세 쪽은 고칠 수 없다(스킬 함정 114 「시험이 실제 명세를 본보기로 씀」). 시험 코드 손질은 이 작업 권한 밖이라 **멈춰 보고함** — 고칠 길: 그 시험이 파생 코드 회귀 가드(task 365 「기존 파생은 한 글자도 바뀌지 않는다」)이므로 옛 명세를 고정 사본(예: `samples/engedi-aftercut/spec.json`, git HEAD의 옛 명세)으로 두고 그 사본을 파생하게 바꾸면 뜻이 그대로 남는다.

## 단계 ③ 문항 등급 표 (초안 — 고정 절은 2/2에서)

본문 직접·추론 = 거르기 · 본문 밖 세부 = 기록. 10-18 사람 기준 셋은 행마다 한 가지만 묻도록 나눔. 가드 문항은 따로 묻는 축(마주 봄·손·칼·어둠)을 빼고 정의(retro 261018-083532).

| 문항 | 묻는 것 | 근거 | 등급 |
|---|---|---|---|
| t.not-facing | 두 사람이 서로 얼굴을 마주 보고 있지 않나? | 사람 10-18 기준 ① 「사울·다윗 마주 봄이 제일 문제」 · [추론] 24:4 「가만히」(사울이 모름) | 거르기 |
| t.saul-back | 다윗이 사울의 등 뒤 쪽(사울이 등을 둔 쪽)에 있나? | [추론] 24:4 「가만히」 · 사람 결정 2026-10-14 | 거르기 |
| t.cave-inside | 바위 굴 안인가(지은 방·건물 안이 아님)? | [직접] 24:3 「굴이 있는지라 … 들어가니라」 | 거르기 |
| t.cave-dark | 굴 안이 어둡나(화면 대부분이 어두운 바위 그늘)? | 사람 10-18 기준 ② · 사전 cave(빛은 [저작]) | 거르기 |
| t.mouth-far | 굴 어귀가 멀리 작게 보이나? | 사람 10-18 기준 ② · [추론] 24:3 「그 굴 깊은 곳」 | 거르기 |
| t.david-gaze-down | 다윗이 아래(자기 손과 천)를 보고 있나? | 사람 10-18 기준 ③ 「시선은 아래」 | 거르기 |
| t.david-lift-corner | 다윗의 한 손이 땅에 끌린 겉옷 귀퉁이를 쥐어 살짝 들고 있나? | [직접] 24:4 「사울의 겉옷자락」 · 사람 결정 2026-11-25 · 기준 ③ 「양손 위치」 | 거르기 |
| t.david-knife-cut | 다윗의 다른 손에 칼이 있고 그 날이 천에 닿아 가르고 있나? | [추론] 24:4 「베니라」(날붙이) · 기준 ③ 「칼 위치」 | 거르기 |
| t.cloth-owner | 베는 천이 사울이 입은 겉옷의 자락인가(다윗 자기 옷·바닥의 다른 천이 아님)? | [직접] 24:4 「사울의 겉옷자락」 · 길갈 함정(찢기는 천의 주인) | 거르기 |
| t.cut-in-progress | 자락이 아직 베어지는 중인가(잘라 낸 조각을 들어 보이지 않음)? | [직접] 24:4 「베니라」 · 사람 결정 2026-11-25 「자르는 중」 | 거르기 |
| t.saul-old | 오른쪽 웅크린 남자가 회색 섞인 수염의 늙은 남자인가? | [추론] stage_why(삼상 13:1 · 행 13:21) · 카드 | 거르기 |
| t.david-young | 왼쪽 무릎 꿇은 남자가 짧은 검은 수염의 젊은 남자인가? | [추론] stage_why(삼상 23:29 · 삼하 5:4) · 카드 | 거르기 |
| t.men-in-dark | 굴 깊은 어둠 속에 다른 남자들이 희미하게 있나? | [직접] 24:3 「다윗과 그의 사람들이 그 굴 깊은 곳에 있더니」 | 거르기 |
| t.men-left-six | 그 남자들이 왼쪽에 여섯쯤인가? | 수·자리 [저작] | 기록 |
| t.knife-small | 다윗의 칼이 작은 칼인가(허리에 차는 긴 칼이 아님)? | 작은 칼 본문 밖 — 더 가까운 추론(칼 sword, 삼상 21:9 · 25:13)에서 벗어난 사람 결정 2026-11-25 · 사전 penknife | 기록 |
| t.david-kneel | 다윗이 두 무릎을 꿇고 있나? | 무릎 걸음 본문 밖 · 저작 | 기록 |
| t.saul-crouch | 사울이 웅크려 앉아 있나(서 있지 않음)? | 24:3 「발을 가리우러」 저작 해석 · 본문 밖 | 기록 |
| t.hem-on-ground | 사울 겉옷 자락이 땅에 끌려 다윗 손까지 이어지나? | 본문 밖 · 저작자 정함(24:4 「가만히」와 맞는 구도 — 입은 사람이 모르게 닿을 자리) | 기록 |
| t.sheepfold | 굴 어귀 바로 바깥에 낮은 돌담(양의 우리)이 보이나? | 양의 우리 [직접] 24:3 「길 가 양의 우리」 · 어귀 바로 바깥 자리 [추론] · 돌담 꼴 저작 — 어귀가 작고 멀어 2/2 첫 판에서 통과율을 먼저 볼 것 | 거르기 |
| t.no-sheep | 양이 그려지지 않았나? | 본문에 없음(「sheepfold」 낱말이 양을 부를 위험 — 저작) | 기록 |
| t.robe-long | 사울 겉옷이 발목까지 오는 긴 겉옷인가? | 길이 [저작](사전 outer-robe size) | 기록 |
| t.no-crown | 사울이 관을 쓰지 않았나? | 본문 밖 · 저작 | 기록 |
| t.light-two | 어귀 빛이 두 사람에게만 떨어지나? | 본문 밖 · 저작(task 364 문장) | 기록 |

장면 공통(스킬 목록 원문에서 — 이 장면 인물로): 화풍 `s.style` · 덩어리 `s.no-blob` · 후광 `t.no-halo` · 교회 도상 `t.no-church` · 가드 `t.guard`(화풍 · 인물이나 겉옷 자락이 사라짐 — 마주 봄·손·칼·어둠은 빼고) · 몸 꼴 · 몸 비율 · 팔 모양(주어: 「무릎 꿇은 젊은 남자와 웅크린 늙은 남자의」) · 시대 옷차림 `t.era-dress` · 시대 용기 `t.era-vessels`(그릇 없으면 맞음) · 두 손 보임 `t.hands-visible`(웅크린 사울 두 손 무릎 앞 · 다윗 두 손 자락 위) · 팔 길이 `t.arm-length`(내린 팔 없으면 맞음) · 현실성 `p.no-floating`(칼·들린 자락) · 손 또렷함 `t.hands-clear-david`·`t.hands-clear-saul`. 무리 앞줄 손 `t.hands-crowd`는 기록(무리가 어둠 속 희미한 그림자 — 손이 안 보이는 것이 구도, 저작). 예물 없음 → `p.royal-gifts` 뺌.

## scripture-reviewer에게 볼 점 (저작 결정 · 불확실 — 1차 전에 적은 것, 1·2·3·4·5·6은 아래 1차 반영으로 고침)

1. **작은 칼** — 본문에 도구 낱말 없음. 날붙이 [추론] · 작은 칼은 사람 결정(본문 밖). 칼(sword)일 가능성(삼상 25:13 「다윗도 자기 칼을 차고」 — 뒤의 일)을 situation에 적음. 사전 표제어를 렘 36:23 「소도」로 잡은 것이 맞는지.
2. **사전 outer-robe** — 24:4·15:27·28:14의 「겉옷」을 한 항목으로 묶음(옷감 양모·발목 길이는 [저작], 출 28:4 「겉옷과 반포 속옷과」로 속옷 위 [추론]). L1을 「wool robe」로 짧게 잡은 까닭(위 표).
3. **「일어나서」**(24:4)를 「행동에 나섬」으로 읽고 무릎 걸음으로 그림 — 옛 명세 해석 그대로. 요소 24:4 「다윗이 일어나서」의 en은 「having crept on his knees」.
4. **양의 우리(24:3)를 제외 요소로** — 굴 바깥이라 굴 안쪽 화면에 넣지 않음(구도 결정). 「타협 금지」에 걸리는지.
5. **겉옷 자락이 땅에 끌림** — [추론](모르게 벨 만큼 자락이 몸에서 떨어짐)으로 적었으나 약함 — 문항은 기록으로 둠.
6. **엔게디 황무지(24:1)를 어귀 너머 「bright bare rocky hills」로 실음** — 어귀 너머 모습은 저작.
7. 무리 수 6(옛 count_why 그대로 + 삼상 23:13 육백 가량 보탬) · 서 있는 무리(가이드 원근 규칙이 서 있는 무리 꼴만 잼 — 앉음 여부는 본문에 없음).
8. 사울 나이 약 79(연대 정본) — 카드 about 70(대표값)과의 차.

## 본문 검토 1차 — 틀림 3 · 약함 11 → 고침 (2026-11-25)

같은 말을 다루는 칸(situation · verse_elements · figures[].verse/gesture/costume · meaning · relation · background · stages · 사전 근거)을 함께 고침.

| # | 지적 | 고친 칸 | 무엇을 |
|---|---|---|---|
| 1 틀림 | 양의 우리를 「화면 밖」으로 뺀 것이 구도(어귀가 화면 안 · 그 너머에 저작 언덕)와 어긋남 | 요소 24:3 「길 가 양의 우리에 이른즉」(out → 실음, field whole_background, en 「a low rough stone sheepfold wall just outside the mouth」) · whole_background ko/en/verse · situation(지리·화면 문장) · background[1] · S1·S1c 문구(S1c neg에 sheep) · 요소 24:1 en 「a glimpse of bright bare rocky hills」 → 「a small bright opening」 | 양의 우리 [직접] 24:3 · 어귀 바로 바깥 자리 [추론](「이른즉 굴이 있는지라」) · 막돌 담 꼴 저작(시대 고증) · 양 없음. 저작 언덕 문구는 모두 뺌. 가이드에는 담 꼴을 넣지 않음(어귀가 작고 멀어 덩어리를 주면 어귀가 커질 위험) — 가이드 그림 그대로 |
| 2 틀림 | 「자락이 땅에 끌림」을 [추론] 24:4로 적은 칸과 본문 밖으로 적은 칸이 갈림 | 요소 24:4 「사울의 겉옷자락」·「사울의 겉옷자락을」 ko · figures[1].costume.verse · figures[0].gesture.verse · meaning.verse · relation.verse · situation · moment.why · 사전 outer-robe look.grounds·size.grounds·criteria(24:4에서 길이를 끌어낸 근거를 빼고 15:27만) | 모두 「땅에 끌린 자락은 본문 밖 · 저작자 정함(24:4 「가만히」와 맞는 구도 — 입은 사람이 모르게 닿을 자리)」 |
| 3 틀림 | 사전 penknife L3 「cutting cloth or leather」가 엔게디 장면을 사전에 들임 | words.json penknife look.L3 ko/en | 「두루마리 같은 것을 베어 내는 데 써요 / used for cutting a scroll」([직접] 렘 36:23). 장면은 L1 「a small iron knife」를 싣는 그대로 — lexicon-link 통과 |
| 4 | 「일어나서 = 행동에 나섬 [추론]」 근거 없음 | 요소 24:4 「다윗이 일어나서」(실음 → out: 베기 바로 앞의 나섬) · situation · figures[0].verse | [추론] 삼상 23:13 「육백 명 가량이 일어나 그일라를 떠나서」 · 18:27 「다윗이 일어나서 그 종자와 함께 가서」 · 무릎 걸음은 본문 밖 · 사람 결정 2026-10-14로 따로 |
| 5 | 「한 귀퉁이」 근거 표시 없음 | situation · meaning.verse · relation.verse · 요소 「사울의 겉옷자락을」 ko | 「한 귀퉁이는 [추론] 24:4 「가만히」 · 24:11 「겉옷자락만」 — 모르게 벨 만큼 작은 조각 · 귀퉁이 꼴은 사람 결정 2026-11-25」 · situation 결과 문장은 「겉옷자락뿐」으로 |
| 6 | 23:29 책 이름 없음 | situation | 「삼상 23:29」 |
| 7 | 「칼을 찼으니」 근거 표시 없음 · S3 neg sword | situation · 요소 「베니라」 ko · figures[0].verse/gesture.verse · S3 verse | [추론] 삼상 21:9 · 25:13(뒤의 일) — 더 가까운 추론은 칼(sword), 작은 칼은 그 추론에서 벗어난 사람 결정 · 허리 칼 없음은 저작(작은 칼과 헷갈리지 않게) |
| 8 | 무리 띠 근거(25:13)가 간접·뒤의 일 · 서 있음 표시 없음 | crowds[0].costume.verse · relation.verse · crowds[0].verse | 띠는 [저작](시대 고증 — 삼상 18:4 「그 군복과 칼과 활과 띠도」 참고) · 서 있음은 본문 밖(가이드 원근 규칙이 서 있는 무리 꼴만 잼) |
| 9 | 사울 stage_why의 28:20 잘린 인용(기력이 다한 까닭은 굶음) | figures[1].stage_why | 28:20을 빼고 「id는 CAST 생애 단계 구분([저작] task 446) · 아직 군대를 거느림은 [추론] 삼상 24:2 「택한 사람 삼천을 거느리고」」 |
| 10 | 웅크림을 본문 밖으로만 | 요소 24:3 「사울이 그 발을 가리우러 들어가니라」 ko · figures[1].verse·gesture.verse · situation · meaning.verse | 「발을 가리우러」는 남이 보지 않는 데서 하는 일 [추론](삿 3:24 「왕이 필연 다락방에서 발을 가리우신다」) · 웅크린 자세·방향은 본문 밖(사람 결정 2026-10-14). 문항 등급 그대로 |
| 11 | penknife 「한 손으로」 근거 없음 | words.json penknife meaning.ko · look.grounds | 「[추론] 렘 36:23 「소도로 그것을 연하여 베어」 — 손에 쥐고 벰 · 작음은 낱말 「소도」 자체 · 한 손으로 쥠은 [저작]」 · meaning.ko 「한 손에」 → 「손에」 |
| 12 | outer-robe 「위에 걸침」 근거로 출 28:4(목록) | words.json outer-robe meaning.grounds · look.grounds · criteria[1] · refs | 레 8:7 「속옷을 입히며 띠를 띠우고 겉옷을 입히며」 · 삼상 18:4 「자기의 입었던 겉옷을 벗어」(refs에도 더함) |
| 13 | outer-robe L3 「앉거나 웅크리면 자락이 땅에 퍼져요」가 엔게디 웅크림을 사전에 들임 | words.json outer-robe look.L3 ko/en | 그 구를 뺌(「… with a wide lower hem.」) — 끌린 자락은 장면 명세 차림 문구에만 |
| 14 | cave forms가 짐승 굴(마 8:20 · 눅 9:58 · 단 6장 · 아 4:8 · 사 11:8 · 욥 37:8 · 38:40 · 나 2:11-12 · 암 3:4)에 걸림 | words.json cave exclude | 「여우도 굴이」「사자 굴」「사자의 굴」「독사의 굴」「시랑의 굴」「든 굴에」「굴에서 올리」「그 굴에 머물며」「굴에 엎드리며」「굴에서 소리를」「그 굴에 채웠고」「굴라」(렘 25:34 동사) 더함 — verses.json에서 하나씩 적중 확인, 남은 「굴」 적중은 모두 사람이 들어가는 굴(막벨라·막게다·아둘람·엘리야·계 6:15 등) |

검증(고친 뒤):
- 관문 `spec_failures` → `([], {})` · 파생 「whole 통과」 · 486토큰 · 머리 낱말 「On the left:」·「On the right:」 하나씩 · 지명 없음.
- 시험 4모듈 250 OK(코디네이터가 `test_engedi_matches_adopted_C`를 고정 사본 `samples/engedi-aftercut/spec.json`으로 바꾼 뒤) · `recheck.py specs` 27/41 · 길갈 관문 그대로 통과 · 엔돌 실패 목록 그대로.
- 사전 검증기 위반 5건 그대로(옛 항목) · 새 항목 0.
- engedi_checks C1·C2·C6·C7(다른 장면 가이드 바뀜 0/29)·C8 통과. 가이드 칸·그림은 바뀌지 않음(양의 우리는 문구만).

## 본문 검토 2차 (scripture-reviewer, 2026-11-25)

- 본문 검토 2차: 틀림 0 · 약함 6 → 고침(figures[0].verse·gesture.verse·S3.verse에 한 귀퉁이 근거 「[추론] 24:4 「가만히」 · 24:11 「겉옷자락만」 · 귀퉁이 꼴은 사람 결정 2026-11-25」 · cave exclude에 「굴에서 올린」(단 6:23만 적중) · S2.verse 「수 6·서 있음·옷은 본문 밖 · 저작」 · S4.verse 「웅크림은 사람 결정 2026-10-14 · 땅에 끌린 자락은 본문 밖」 · same_time 24:4에서 「일어나 나섬」을 바로 앞으로 · outer-robe criteria[2] 근거를 [직접] 24:4(벨 자락)과 [추론] 15:27(늘어짐)로 가름 · outer-robe meaning.ko 「길고」 뺌 + meaning.grounds에 넉넉함 [추론] 15:27 — 영문 문구는 바꾸지 않음)
