# 규칙 원장 재검 (task 392)

목표(2026-10-22 사용자): 장면 승인 수가 목표가 아니다 — 시험으로 무인화 규칙을 세우고, **규칙이 바뀌면 이전 명세·그림이 지금 규칙에 맞는지 다시 잰다.** 지표 = 지금 규칙집 통과율.

- 원장: `scripts/canon/rules.json` — 규칙마다 층(spec·derive·generate·edit·judge·human)·원래 적용 범위·검사(함수 | `test:` 코드 가드 | human | todo)·출처·도입. `version` = 규칙 내용 해시(`recheck.py ledger`).
- 승인 그림 `approved.final`에 `spec_hash`(명세 해시, approved·_format 제외)·`prompt_hash`(생성 프롬프트)·`rules_version`(원장 판). 앞으로 `approve.night_pick`·`local_edit`·`confirm_pick`이 자동으로 적는다(`run_night record`는 생성 프롬프트도 넘김).
- 명령: `recheck.py specs`(GPU 0 · 토큰 검사는 venv314 자동) · `recheck.py images`(Sonnet 구독 `claude -p` — J1 장당 2호출 + 상식 걸린 장면만 3회).
- 재검은 **표시만** 한다 — 승인 취소는 사람 결정(ADR 260905-104910). 아래 표는 명령이 다시 쓴다(손 집계 금지).
- 명세 규칙은 **원래 범위가 일부였어도 전 명세에** 건다 — 그게 이 장치의 뜻이다. 그래서 일부에만 걸던 규칙의 통과율이 낮게 나오는 것이 정상이며, 그 실패 목록이 곧 재저작 대상이다.
- 그림 판정의 「낡음」 = 그 그림의 명세가 그 뒤 바뀌었거나, 지금 명세·파생 규칙을 어김(그 명세로 다시 그려야 규칙이 그림에 실린다).

## 명세 재검 — 전 명세 × 명세·파생 함수 규칙

<!-- recheck:specs:begin -->
원장 판 `9eafa400597b` · 토큰 검사 venv314 · 명세 37

| 규칙 | 층 | 원래 범위 | 통과 | 실패 | 못 잼 | 통과율 |
|---|---|---|---|---|---|---|
| `spec.required-fields` | spec | all | 37 | 0 | 0 | 100% |
| `spec.whole-fields` | spec | list | 15 | 22 | 0 | 41% |
| `spec.verse-elements` | spec | list | 15 | 22 | 0 | 41% |
| `spec.no-compromise-words` | spec | list | 37 | 0 | 0 | 100% |
| `spec.scene-all-verses` | spec | one | 4 | 33 | 0 | 11% |
| `spec.cast-card-v2` | spec | all | 37 | 0 | 0 | 100% |
| `spec.lexicon-link` | spec | all | 12 | 3 | 22 | 80% |
| `derive.no-hand-prompt` | derive | all | 37 | 0 | 0 | 100% |
| `derive.no-bare-head` | derive | all | 37 | 0 | 0 | 100% |
| `derive.prop-in-prompt` | derive | all | 29 | 8 | 0 | 78% |
| `derive.512-tokens` | derive | list | 37 | 0 | 0 | 100% |
| `spec.stage-from-scripture` | spec | all | 1 | 36 | 0 | 3% |
| `spec.action-place-on-figure` | spec | all | 15 | 0 | 22 | 100% |
| `generate.thrown-guide` | generate | all | 37 | 0 | 0 | 100% |
| `generate.guide-backdrop` | generate | all | 37 | 0 | 0 | 100% |
| `generate.guide-body-build` | generate | all | 36 | 1 | 0 | 97% |
| `generate.dodge-clear` | generate | all | 37 | 0 | 0 | 100% |
| `generate.guide-costume-legs` | generate | all | 37 | 0 | 0 | 100% |
| `derive.youth-noun` | derive | all | 34 | 3 | 0 | 92% |
| `generate.pose-skeleton` | generate | all | 37 | 0 | 0 | 100% |
| `generate.figure-scale` | generate | all | 37 | 0 | 0 | 100% |
| `derive.no-second-point` | derive | all | 37 | 0 | 0 | 100% |
| `generate.youth-height` | generate | all | 37 | 0 | 0 | 100% |

폐기 규칙(재검·통과율에서 뺌): `derive.clip-77-tokens` — 2026-10-22 사람 결정 — SDXL 단계별 경로 전용, 지금 생성 경로는 derive.512-tokens가 잼 · `generate.pose-throw-geometry` — 2026-10-23 d3 — 한 장(c14 s5) 근거로 만든 규칙: d1 「달리는 자세」·d2 「늘어진 팔」로 반증, c10 뼈대가 묶음 기록상 가장 좋음(던진 몸짓 3/8). 결함을 규칙으로 옮기기 전에 같은 조건에서 맞게 나온 적이 있는지 기록부터 볼 것

**전 규칙 통과 명세 1/37** · 칸 통과 679/807 (84%)

| 명세 | required-fields | whole-fields | verse-elements | no-compromise-words | scene-all-verses | cast-card-v2 | lexicon-link | no-hand-prompt | no-bare-head | prop-in-prompt | 512-tokens | stage-from-scripture | action-place-on-figure | thrown-guide | guide-backdrop | guide-body-build | dodge-clear | guide-costume-legs | youth-noun | pose-skeleton | figure-scale | no-second-point | youth-height |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| david-adullam-cave | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| david-ark-jerusalem | ✅ | ✗ | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| david-en-gedi-saul | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| david-gath-achish | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| david-gibeah-harp | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ |
| david-gibeon-battle | ✅ | ✗ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| david-goliath-gath | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✗ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ |
| david-hebron-king-judah | ✅ | ✗ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| david-jerusalem-conquest | ✅ | ✗ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| david-mahanaim-exile | ✅ | ✗ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| david-nathan-covenant | ✅ | ✗ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| david-nob-priests | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| david-ramah-samuel | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| david-returns-jerusalem | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| david-ziklag-base | ✅ | ✗ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| samuel-bethlehem-david-anointing | ✅ | ✗ | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ |
| samuel-ramah-death | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| saul-endor-medium | ✅ | ✗ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| saul-gibeah-spear | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| saul-gilboa-death | ✅ | ✗ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| saul-gilgal-amalek | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| saul-gilgal-coronation | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| saul-jabesh-rescue | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| saul-michmash-battle | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| saul-mizpah-chosen | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| saul-nob-massacre | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| solomon-ezion-geber-fleet | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✗ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| solomon-gibeon-dream | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✗ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| solomon-gihon-anointing | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| solomon-jerusalem-apostasy | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| solomon-jerusalem-birth | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| solomon-jerusalem-david-charge | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✗ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| solomon-jerusalem-palace | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✗ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| solomon-jerusalem-sheba | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✗ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| solomon-jerusalem-temple-build | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| solomon-jerusalem-temple-dedication | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✗ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| solomon-jerusalem-two-mothers | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✗ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
<!-- recheck:specs:end -->

## 승인 그림 재검 — 승인 그림 × 그림 규칙

<!-- recheck:images:begin -->
원장 판 `e09949ef99e7` · 승인 그림 12 · ✅ 통과 · ✗ 실패 · 낡음 = 명세가 바뀌었거나 지금 규칙을 어김 · – 못 잼

| 규칙 | 통과 | 실패 | 낡음 | 못 잼 |
|---|---|---|---|---|
| `spec.required-fields` | 11 | 0 | 1 | 0 |
| `spec.whole-fields` | 8 | 0 | 4 | 0 |
| `spec.verse-elements` | 3 | 0 | 9 | 0 |
| `spec.no-compromise-words` | 11 | 0 | 1 | 0 |
| `spec.scene-all-verses` | 1 | 0 | 11 | 0 |
| `spec.cast-card-v2` | 11 | 0 | 1 | 0 |
| `derive.no-hand-prompt` | 9 | 0 | 3 | 0 |
| `derive.no-bare-head` | 11 | 0 | 1 | 0 |
| `derive.prop-in-prompt` | 11 | 0 | 1 | 0 |
| `derive.512-tokens` | 11 | 0 | 1 | 0 |
| `judge.j1-items` | 1 | 8 | 0 | 3 |
| `judge.style` | 0 | 0 | 0 | 12 |
| `judge.plausibility-adopted` | 11 | 1 | 0 | 0 |
| `human.face-matched-quality` | 0 | 0 | 0 | 12 |

**잰 규칙 모두 통과(실패·낡음 0) 0/12**

| 승인 그림 | 경로 | J1 요소 | 상식 | 낡음 규칙 |
|---|---|---|---|---|
| david-gath-achish | local-edit s5 | ✗ 틀림 figures[0].facing | ✅ 걸린 채택 문항 0 | scene-all-verses, no-hand-prompt |
| david-gibeah-harp | night-pick s11 | ✗ 틀림 figures[0].prop, figures[1].prop | ✅ 걸린 채택 문항 0 | verse-elements, scene-all-verses |
| david-returns-jerusalem | night-pick s101 | – restyle-r6 기록에 몸 크롭 상자가 없다(바탕과 다른 그림) — OWLv2 상자는 GPU 단계라 이번 | ✗ 틀림 p.boarding | 없음 |
| samuel-bethlehem-david-anointing | local-edit s42 | ✗ 틀림 background[0], crowds | ✅ 걸린 채택 문항 0 | whole-fields, scene-all-verses, no-hand-prompt |
| samuel-ramah-death | night-pick s42 | ✗ 틀림 crowds, figures[0].prop | ✅ 걸린 채택 문항 0 | verse-elements, scene-all-verses |
| saul-gibeah-spear | night-pick s5 | – 몸 크롭 상자 없음: ['david-boy'] | ✅ 걸린 채택 문항 0 | required-fields, whole-fields, verse-elements, no-compromise-words, scene-all-verses, cast-card-v2, no-hand-prompt, no-bare-head, prop-in-prompt, 512-tokens |
| saul-gilgal-amalek | night-pick s11 | ✅ 9문항 맞음 | ✅ 걸린 채택 문항 0 | verse-elements, scene-all-verses |
| saul-gilgal-coronation | attempt a005 s11 | – 단계 사다리 그림에 몸 크롭 상자 기록이 없다 — OWLv2 상자는 GPU 단계라 이번 범위 밖 | ✅ 걸린 채택 문항 0 | verse-elements, scene-all-verses |
| saul-jabesh-rescue | night-pick s42 | ✗ 틀림 background[0], crowds[0] | ✅ 걸린 채택 문항 0 | verse-elements, scene-all-verses |
| saul-michmash-battle | night-pick s202 | ✗ 틀림 crowds, figures[1].pose, figures[1].prop | ✅ 걸린 채택 문항 0 | whole-fields, verse-elements, scene-all-verses |
| saul-mizpah-chosen | night-pick s7 | ✗ 틀림 crowds, figures[0].pose, figures[0].prop, figures[1].faci | ✅ 걸린 채택 문항 0 | whole-fields, verse-elements, scene-all-verses |
| saul-nob-massacre | night-pick s303 | ✗ 틀림 figures[0].pose, figures[1].prop, figures[2].prop | ✅ 걸린 채택 문항 0 | verse-elements, scene-all-verses |
<!-- recheck:images:end -->

## 지금 규칙집 통과율과 다음 과제 (2026-10-22 task 396, 원장 판 `e09949ef99e7`)

- **원장 바뀜(task 396)**: `derive.clip-77-tokens` 폐기(사람 결정 — SDXL 단계별 경로 전용, 재검·통과율에서 뺌) · `derive.prop-in-prompt` 추가(지물이 한 장 프롬프트에 실림, 전 명세). 이제 CLIP 77을 뺀 숫자가 기본이다.
- **명세: 전 규칙 통과 1/37(요단) · 칸 통과 77%(284/370).** 규칙별: 장면 구절 상황 칸 4/37 · 구절 시각 요소 14/37 · 한 장 모드 칸 15/37 · **지물 실림 29/37** · 나머지 6규칙 37/37(타협 금지 낱말 포함 — task 394).
- **지물 실림 실패 8명세 = 다음 재저작 대상**(14지물, 모두 prop 칸이 한국어뿐 → 「영문 없음」): 골리앗 가드(창·방패·물매) · 솔로몬 7(에시온게벨·기브온 꿈·다윗 유언·궁전·스바·성전 봉헌·두 어머니 — 겉옷자락·왕홀·이불·허리띠·향품 상자·아기). 계획 때 어림값 14와 같다. 영문으로 실린 기브아 창(`a spear`·`a small wooden lyre`)은 통과.
- **승인 그림: 잰 규칙 모두 통과 0/12.** 명세·파생 규칙으로 낡지 않은 그림은 CLIP 77을 빼도 요단 1장뿐. J1 요소 판정(지금 명세 문항, 승인된 바로 그 그림)은 잰 10장 중 통과 1(길갈 아말렉) — 틀림 사유는 대부분 실제 결함으로 읽힌다(기브아 두 장 「작은 수금」이 켈트식 큰 하프 · 라마·놉 칼이 중세풍 직검 · 베들레헴 형 넷 · 야베스 천막 온전 · 믹마스 「겉옷자락 쥔 사람이 사울」). J1은 사람 앞 거르기 판정자(경계 합격)라 승인 취소 근거는 아니다 — 표시만. 상식 규칙은 요단 1장이 「배에 오름」 틀림(배 밖에 줄지어 선 사람) — 사람이 승인한 그림과 채택 규칙이 갈렸다.
- **출처 기록**: 승인 12장 중 생성 때 프롬프트 = 지금 파생 9장(요단 restyle 포함), 다름 2장(가드·베들레헴 국소 편집 — 바탕이 plain-words r2 사전 문구 회차라 명세 파생과 다름), 기록 없음 1장(길갈 대관식 단계 사다리). 앞으로 승인은 `approve`가 해시를 자동으로 적는다.
- **못 잰 것**: 요단 restyle·길갈 대관식 J1(몸 크롭 상자 없음 — OWLv2 상자 계산이 필요), 화풍(판정자 조건부), 얼굴(사람 판정 — task 393 화질 맞춤 화면).
- **다음 과제 후보(효과 순)**: ① 타협 금지 위반 3명세 재저작(task 394) → `recheck.py specs`로 확인 ② 장면 구절 상황 칸을 나머지 36명세에(문서 규칙 「단락 전체 읽기」와 함께 — 재저작 에이전트 + scripture-reviewer) ③ 승인 그림 중 J1 틀림 사유가 명세 칸과 맞는 장면(기브아 수금·칼 모양·베들레헴 형제)부터 바뀐 명세로 재생성 ④ 문서만 규칙을 검사로: 구도 가이드(주고받는 장면·배치) → 낱말 사전 연결 → 잘라붙이기 금지 ⑤ (끝남 — task 396에서 CLIP 77 폐기) 지물 실림 실패 8명세의 prop 영문화·몸짓 문구 ⑥ 몸 크롭 상자 없는 2장 OWLv2 상자 계산.
