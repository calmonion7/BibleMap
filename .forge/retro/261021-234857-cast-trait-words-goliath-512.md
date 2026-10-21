# 2026-10-21 — task 390 성품 낱말 calm·steady·composed 금지 + 골리앗 한 장 프롬프트 512 안 + 355 뒤처리 (fg-loop, 늦은 회고)

## 계획 대비 실제
- 대체로 계획대로. 정지 조건 C1~C11 첫 회에 모두 통과, 재계획 0/3(커밋 afdf8c8).
- 토큰 실측이 계획과 달랐다: 계획은 결정 2·3·4를 합쳐 501이라 했지만, 결정 2·3만으로는 515 → 결정 4의 몸짓 중복(`pressed right up against him`)까지 빼서 509.
- 「7명」은 사람 수였고 고칠 값은 10개(solomon·solomon-prime·zadok이 2값씩). 루프 검사 C9의 문턱을 처음엔 9로 잘못 셌다가 10으로 바로잡았다.
- 계획은 사독 카드 층 `calm`이 빠지면 기혼 장면 프롬프트가 한 낱말 바뀐다고 봤지만, 37장면을 기준 커밋과 견줘 보니 바뀐 장면은 골리앗뿐이었다(그 장면 경로는 카드 나이 문구를 안 씀).
- `{costume:david-boy}`를 풀려고 `_fill`에 두 줄을 더했다(SAMPLE_COSTUME에 없는 id는 cast 정본 costume).

## 배운 점
- **id를 나눈 뒤 장면 단계 자리표시자가 옛 id를 가리켜도 검사가 몰랐다.** `check_scenes`는 `{cast:}`·`{castc:}`만 「figures에 있나」를 보고 `{costume:}`은 안 봤다 — `{costume:david}`는 SAMPLE_COSTUME에 있어 문자열로는 멀쩡히 풀렸다. → eval로 승급(아래).
- **루프 검사 문턱은 사람 수가 아니라 고칠 값 수로 센다.** 계획의 「N명」을 그대로 쓰지 말고 바꿀 값을 먼저 뽑아 센다.
- **토큰 예상은 실제로 고친 상태에서 잰 값만 믿는다.** 계획서 실측(501)이 결정 묶음과 맞지 않았다 — 결정마다 따로 재 두면 「어디까지 빼야 512 안」이 바로 보인다.
- **512 검사는 관계 문장을 지워도 통과한다.** fg-loop 인터뷰에서 C10(relation.en이 기준 커밋과 같고 프롬프트에 있음)을 더해 막았다. 길이 상한 검사를 정지 조건으로 쓸 때는 「빼면 안 되는 문장」 보존 검사를 짝으로 단다.
- **「낱말만 빼기」는 기계로 잴 수 있다**: 기준 커밋 값과 새 값을 낱말로 나눠, 새 값이 옛 값의 부분열이고 빠진 낱말이 허용 목록 안인지 본다(.forge/scratch/loop-check-390.py c9). 비슷한 「빼기만」 과제에 다시 쓸 수 있다.
- 다음엔 다르게: 계획 단계에서 장면 프롬프트 영향 예측(「어느 장면이 바뀐다」)은 37장면 전후 비교로 확인한다 — 추측이 틀렸다(사독 기혼).

## 문서 갱신
- eval: `scripts/canon/check_scenes.py` — 단계 문구의 `{costume:<id>}`도 `{cast:}`와 같은 규칙(정본 있음·figures에 있음). 기준 커밋 골리앗 장면에서 `stages[S5] {costume:david}가 figures에 없음`으로 빨강, 지금 37/37 초록.
- CONTEXT.md·ADR: 없음(「근거 우선순위 — 성경 본문 > 사람 판단」은 이미 있음, 이번엔 적용만 함).
- 다음 과제 후보:
  - `make_night_page.NAME`에 장면 인물 11명 없음(bathsheba·david-old·goliath·mother-a·mother-b·sheba-queen·shieldman·shimei·solomon·solomon-old·zadok) → 판정 화면에 영어 id가 그대로 나온다. 채운 뒤 「figures의 cast가 모두 NAME에 있음」 eval.
  - `derive_scene.whole_prompt`의 바깥 `beardless` 분기는 이제 타는 장면이 없다(task 363 일반 규칙) — 남길지 지울지.
  - 방패 「large round bronze shield」의 `round`·`bronze`는 본문 밖(17:7은 「방패」만).
