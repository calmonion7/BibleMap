# 카드 v1 `age` 나이 낱말 — ageBand class와 맞춤 (task 431, 2026-10-26)

후속 fu-3a6978704178(task 429 scripture-reviewer 보류 ③ — abner 「middle-aged commander」가 60대 카드와 어긋남, 429에서 abner만 고침).

## 새 규칙 `spec.cast-age-word`

카드 v1 `age` 칸의 나이 낱말이 `card.ageBand.class`와 맞아야 한다. 이 칸은 프롬프트로 두 군데 나간다 — 한 장 프롬프트의 시선 대상 문구(`derive_scene.whole_prompt` 「looking toward the <age> …」) · 장면 안 경로 그룹 단계(`cast_describe_compact`).

| 낱말 | 허용 class |
|---|---|
| boy · girl | child · youth |
| youth | youth |
| young | youth · young |
| prime · mature | prime · middle (`-prime` id는 장년 30~40대 — CAST.md) |
| middle-aged | middle |
| aging · old · elderly | elder |

- 나이 낱말이 없는 글(「tall king」「warrior」「a queen」「older commander」)은 **통과** — 나이를 주장하지 않는다. 못 잼으로 두면 생성 관문(require_pass)이 사울 장면들을 막는다.
- 낱말은 통째로만 셈(앞뒤가 글자·`-`이면 안 셈) — 「older」는 「old」 아님, 「middle-aged」 안의 「middle」은 따로 안 셈.
- 거는 곳(같은 함수 `check_cast_v2.age_word_errors` 하나):
  - 카드: `check_cast_v2.check` (k) — 그래서 `spec.cast-card-v2`도 함께 잡는다.
  - 재검: `recheck.cast_age_word_errors` — 명세 인물마다 `_cast_in_scene`(장면 `cast_override` 포함). `check_scenes`에는 따로 안 건다. 원장 판 6575283711cc(규칙 81).
- 시험: `test_scene_rules.CastAgeWord`(낱말별 허용·걸림 · 낱말 없음 통과 · 장면 덮어쓰기).

적용 전 손 finder와 같은 결과: 카드 34장 중 joab 1장 · 장면 덮어쓰기 8개 모두 맞음(기브아 수금 david-boy 「young shepherd」는 youth라 통과).

## 바꾼 값

| 대상 | 전 | 후 | 근거 |
|---|---|---|---|
| joab `age` | 「young commander」(young ↔ 카드 prime 30대) | 「commander in his prime」 | [저작] 그대로 · `_why.age`에 「카드 ageBand 30대와 맞춤 — task 431」 |

abner(「older commander」 60대)와는 시선 문구로 여전히 갈린다. 기브온은 판 경로이고 joab은 시선 대상이 아니라 지금 프롬프트에 나가지 않았다 → 이번 규칙은 앞으로를 막는 가드.

## 재검

- 명세(`recheck.py specs`): `spec.cast-age-word` 38/38 통과 · `spec.cast-card-v2` 실패 0 · 전 규칙 통과 5/38 그대로.
- 승인 그림(`recheck.py images`): 잰 규칙 모두 통과 1/12 그대로. 새 칸이 `stale`인 8장(기브아 수금·요단·베들레헴·라마 죽음·길갈 즉위·야베스·믹마스·미스바)은 모두 이전부터 「그림 뒤 명세가 바뀜」 — **이 규칙 때문에 새로 낡은 승인 그림 0장**. 다시 그리기·승인 취소 없음.
