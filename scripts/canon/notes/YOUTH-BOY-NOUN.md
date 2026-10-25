# 14세 이하 youth는 「boy」 — david-boy 파생 명사 (task 430, 2026-10-26)

후속 fu-d1a466474adc(task 426 scripture-reviewer 재판정 — 보류: 본문 모순은 아니고 품질 문제).

## 바꾼 것

- `derive_scene._who`: 카드 ageBand class youth 중 카드 나이 **15세 미만**이면 성별 명사를 boy·girl로. 15세 이상과 숫자를 못 읽는 글은 그대로 young man·young woman(task 403 r4 근거는 15세 이상에만 있다).
  - david-boy: 「an ancient Israelite young man, a shepherd, about 14 … thin boyish torso」 → 「an ancient Israelite boy, a shepherd, about 14 …」 — 명사와 몸 서술이 한 문장에서 맞음.
  - david-youth(about 18): 그대로 young man.
- 나이 해석은 한 군데: `check_cast_v2.card_age`(task 429 spec.cast-age-band와 같은 함수) → `derive_scene.youth_age`(위 끝 나이). `recheck.youth_noun_errors`도 이 함수를 쓴다(전에는 「about N」만 읽던 따로 된 정규식). 문턱 `derive_scene.YOUTH_NOUN_MIN_AGE = 15`(recheck에서 옮김).
- 원장 derive.youth-noun note만 고침(기준은 그대로 — 15세 이상 youth가 있으면 boy 금지): 판 28e03cda2a89.
- 시험: `test_scene_rules.YouthNoun.test_who_under_15_youth_is_boy`(14 → boy · 18 → young man · 숫자 없음 → young man · 여성 14 → girl · david-boy 카드).

## 재검

- 세 장면(골리앗·베들레헴·기브아 수금) 파생 문구 「young man, a shepherd」 4 → 0.
- `recheck.py specs`: derive.youth-noun 38/38 · derive.512-tokens 38/38 · 전 규칙 통과 5/38(그대로).
- `recheck.py images`: 1/12 그대로 · 표 변화 없음. 낡음 판정은 명세 해시만 보는데 이번 변경은 파생 코드라 명세가 안 바뀜.
  - 실제 영향 받는 승인 그림(15세 미만 youth가 나오는 장면) 2장 — **둘 다 이미 명세가 바뀌어 낡음**이던 그림이라 새로 낡음 0장:
    - authored-david-gibeah-harp(david-boy) — 생성 때 프롬프트가 지금 파생과 다름
    - authored-samuel-bethlehem-david-anointing(david-boy) — 생성 때 프롬프트가 지금 파생과 다름

## 위험(그림으로는 확인 안 함 — GPU 0)

「boy」가 14세보다 어리게 그려질 수 있다(task 403 r4: 20세를 boy로 옮기자 열두 살로 그려짐). 다음에 이 장면들을 그릴 때(기브아 수금 단계 ② 등) 나이 문항이 잡는다.
