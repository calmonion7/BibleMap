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
원장 판 `e58559424efd` · 토큰 검사 venv314 · 명세 37

| 규칙 | 층 | 원래 범위 | 통과 | 실패 | 못 잼 | 통과율 |
|---|---|---|---|---|---|---|
| `spec.required-fields` | spec | all | 37 | 0 | 0 | 100% |
| `spec.whole-fields` | spec | list | 17 | 20 | 0 | 46% |
| `spec.verse-elements` | spec | list | 18 | 19 | 0 | 49% |
| `spec.no-compromise-words` | spec | list | 37 | 0 | 0 | 100% |
| `spec.scene-all-verses` | spec | one | 7 | 30 | 0 | 19% |
| `spec.cast-card-v2` | spec | all | 37 | 0 | 0 | 100% |
| `spec.lexicon-link` | spec | all | 15 | 3 | 19 | 83% |
| `derive.no-hand-prompt` | derive | all | 37 | 0 | 0 | 100% |
| `derive.no-bare-head` | derive | all | 37 | 0 | 0 | 100% |
| `derive.prop-in-prompt` | derive | all | 30 | 7 | 0 | 81% |
| `derive.512-tokens` | derive | list | 37 | 0 | 0 | 100% |
| `spec.stage-from-scripture` | spec | all | 4 | 33 | 0 | 11% |
| `spec.action-place-on-figure` | spec | all | 18 | 0 | 19 | 100% |
| `generate.thrown-guide` | generate | all | 37 | 0 | 0 | 100% |
| `generate.guide-backdrop` | generate | all | 37 | 0 | 0 | 100% |
| `generate.guide-body-build` | generate | all | 36 | 1 | 0 | 97% |
| `generate.dodge-clear` | generate | all | 37 | 0 | 0 | 100% |
| `generate.guide-costume-legs` | generate | all | 37 | 0 | 0 | 100% |
| `derive.youth-noun` | derive | all | 35 | 2 | 0 | 95% |
| `generate.pose-skeleton` | generate | all | 37 | 0 | 0 | 100% |
| `generate.figure-scale` | generate | all | 5 | 0 | 32 | 100% |
| `derive.no-second-point` | derive | all | 37 | 0 | 0 | 100% |
| `generate.youth-height` | generate | all | 35 | 0 | 2 | 100% |
| `generate.height-ratio` | generate | all | 18 | 0 | 19 | 100% |
| `generate.seated-height` | generate | all | 37 | 0 | 0 | 100% |
| `generate.split-control` | generate | all | 37 | 0 | 0 | 100% |
| `derive.prop-size-relative` | derive | all | 34 | 3 | 0 | 92% |
| `generate.flight-position` | generate | all | 37 | 0 | 0 | 100% |
| `generate.flight-height` | generate | all | 37 | 0 | 0 | 100% |
| `derive.empty-hand-open` | derive | all | 37 | 0 | 0 | 100% |
| `derive.wall-material` | derive | all | 37 | 0 | 0 | 100% |
| `derive.no-inflating-build` | derive | all | 28 | 9 | 0 | 76% |
| `derive.prop-size-coverage` | derive | all | 37 | 0 | 0 | 100% |
| `derive.held-hold` | derive | all | 37 | 0 | 0 | 100% |
| `derive.crowd-stage` | derive | all | 36 | 1 | 0 | 97% |
| `generate.eye-level-perspective` | generate | all | 17 | 0 | 20 | 100% |

폐기 규칙(재검·통과율에서 뺌): `derive.clip-77-tokens` — 2026-10-22 사람 결정 — SDXL 단계별 경로 전용, 지금 생성 경로는 derive.512-tokens가 잼 · `generate.pose-throw-geometry` — 2026-10-23 d3 — 한 장(c14 s5) 근거로 만든 규칙: d1 「달리는 자세」·d2 「늘어진 팔」로 반증, c10 뼈대가 묶음 기록상 가장 좋음(던진 몸짓 3/8). 결함을 규칙으로 옮기기 전에 같은 조건에서 맞게 나온 적이 있는지 기록부터 볼 것 · `generate.pose-hold` — 2026-10-23 f5 — f4e 5표: 수금 쥠 5→1로 고쳤으나 벽 앞·피함·순간 0→5/5로 무너짐(다윗이 벽에서 떨어져 선 채) · 다윗 깊이 꼴 유지, 손 자리는 다른 수단 · `generate.pose-only-control` — 2026-10-23 g2e — 진단은 맞음(뼈대만이면 몸짓이 살아 다윗 숙임·사울 기욺)이나 맞바꿈: 몸 덩어리·벽 자리·수금 모양을 잃고 액자(g1e 다수결 틀림 6 · g2e 15 vs 섞은 f6e3 2). 깊이+뼈대 섞기 유지, make_pose_only·duck_low는 남김 · `generate.spear-two-thirds` — 2026-10-23 m5 — generate.flight-position(명세 칸 guide.flight + 사전 크기)로 일반화(사람 「지적한거 그대로 일회성으로 쓰지말고 규칙화」)

**전 규칙 통과 명세 4/37** · 칸 통과 1093/1221 (90%)

| 명세 | required-fields | whole-fields | verse-elements | no-compromise-words | scene-all-verses | cast-card-v2 | lexicon-link | no-hand-prompt | no-bare-head | prop-in-prompt | 512-tokens | stage-from-scripture | action-place-on-figure | thrown-guide | guide-backdrop | guide-body-build | dodge-clear | guide-costume-legs | youth-noun | pose-skeleton | figure-scale | no-second-point | youth-height | height-ratio | seated-height | split-control | prop-size-relative | flight-position | flight-height | empty-hand-open | wall-material | no-inflating-build | prop-size-coverage | held-hold | crowd-stage | eye-level-perspective |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| david-adullam-cave | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | – |
| david-ark-jerusalem | ✅ | ✗ | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – |
| david-en-gedi-saul | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | – |
| david-gath-achish | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| david-gibeah-harp | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| david-gibeon-battle | ✅ | ✗ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – |
| david-goliath-gath | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✗ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | – | ✅ | – | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – |
| david-hebron-king-judah | ✅ | ✗ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – |
| david-jerusalem-conquest | ✅ | ✗ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | – |
| david-mahanaim-exile | ✅ | ✗ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – |
| david-nathan-covenant | ✅ | ✗ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| david-nob-priests | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | – | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ |
| david-ramah-samuel | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| david-returns-jerusalem | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| david-ziklag-base | ✅ | ✗ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| samuel-bethlehem-david-anointing | ✅ | ✗ | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | – | ✅ | – | – | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – |
| samuel-ramah-death | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – |
| saul-endor-medium | ✅ | ✗ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – |
| saul-gibeah-spear | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| saul-gilboa-death | ✅ | ✗ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – |
| saul-gilgal-amalek | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ |
| saul-gilgal-coronation | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | – |
| saul-jabesh-rescue | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | – |
| saul-michmash-battle | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | – |
| saul-mizpah-chosen | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | – |
| saul-nob-massacre | ✅ | ✅ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ |
| solomon-ezion-geber-fleet | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✗ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| solomon-gibeon-dream | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✗ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| solomon-gihon-anointing | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – |
| solomon-jerusalem-apostasy | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – |
| solomon-jerusalem-birth | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| solomon-jerusalem-david-charge | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✗ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| solomon-jerusalem-palace | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✗ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| solomon-jerusalem-sheba | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✗ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| solomon-jerusalem-temple-build | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – |
| solomon-jerusalem-temple-dedication | ✅ | ✗ | ✗ | ✅ | ✗ | ✅ | – | ✅ | ✅ | ✗ | ✅ | ✗ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – |
| solomon-jerusalem-two-mothers | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
<!-- recheck:specs:end -->

## 승인 그림 재검 — 승인 그림 × 그림 규칙

<!-- recheck:images:begin -->
원장 판 `cb0b1f5f7371` · 승인 그림 12 · ✅ 통과 · ✗ 실패 · 낡음 = 명세가 바뀌었거나 지금 규칙을 어김 · – 못 잼

| 규칙 | 통과 | 실패 | 낡음 | 못 잼 |
|---|---|---|---|---|
| `spec.required-fields` | 5 | 0 | 7 | 0 |
| `spec.whole-fields` | 5 | 0 | 7 | 0 |
| `spec.verse-elements` | 2 | 0 | 10 | 0 |
| `spec.no-compromise-words` | 5 | 0 | 7 | 0 |
| `spec.scene-all-verses` | 1 | 0 | 11 | 0 |
| `spec.cast-card-v2` | 5 | 0 | 7 | 0 |
| `spec.lexicon-link` | 2 | 0 | 7 | 3 |
| `derive.no-hand-prompt` | 4 | 0 | 8 | 0 |
| `derive.no-bare-head` | 5 | 0 | 7 | 0 |
| `derive.prop-in-prompt` | 5 | 0 | 7 | 0 |
| `derive.512-tokens` | 5 | 0 | 7 | 0 |
| `judge.j1-items` | 1 | 8 | 0 | 3 |
| `judge.style` | 0 | 0 | 0 | 12 |
| `judge.plausibility-adopted` | 11 | 1 | 0 | 0 |
| `human.face-matched-quality` | 0 | 0 | 0 | 12 |
| `spec.stage-from-scripture` | 1 | 0 | 11 | 0 |
| `spec.action-place-on-figure` | 2 | 0 | 7 | 3 |
| `generate.thrown-guide` | 5 | 0 | 7 | 0 |
| `generate.guide-backdrop` | 5 | 0 | 7 | 0 |
| `generate.guide-body-build` | 5 | 0 | 7 | 0 |
| `generate.dodge-clear` | 5 | 0 | 7 | 0 |
| `generate.guide-costume-legs` | 5 | 0 | 7 | 0 |
| `derive.youth-noun` | 4 | 0 | 8 | 0 |
| `generate.pose-skeleton` | 5 | 0 | 7 | 0 |
| `generate.figure-scale` | 1 | 0 | 7 | 4 |
| `derive.no-second-point` | 5 | 0 | 7 | 0 |
| `generate.youth-height` | 4 | 0 | 7 | 1 |
| `generate.height-ratio` | 1 | 0 | 7 | 4 |
| `generate.split-control` | 5 | 0 | 7 | 0 |
| `derive.prop-size-relative` | 5 | 0 | 7 | 0 |
| `generate.flight-position` | 5 | 0 | 7 | 0 |
| `generate.flight-height` | 5 | 0 | 7 | 0 |
| `derive.empty-hand-open` | 5 | 0 | 7 | 0 |
| `derive.wall-material` | 5 | 0 | 7 | 0 |
| `derive.no-inflating-build` | 2 | 0 | 10 | 0 |
| `derive.prop-size-coverage` | 5 | 0 | 7 | 0 |
| `derive.held-hold` | 5 | 0 | 7 | 0 |
| `derive.crowd-stage` | 5 | 0 | 7 | 0 |
| `generate.eye-level-perspective` | 5 | 0 | 7 | 0 |

**잰 규칙 모두 통과(실패·낡음 0) 1/12**

| 승인 그림 | 경로 | J1 요소 | 상식 | 낡음 규칙 |
|---|---|---|---|---|
| david-gath-achish | local-edit s5 | ✗ 틀림 figures[0].facing | ✅ 걸린 채택 문항 0 | scene-all-verses, no-hand-prompt, stage-from-scripture |
| david-gibeah-harp | night-pick s11 | ✗ 틀림 figures[0].prop, figures[1].prop | ✅ 걸린 채택 문항 0 | verse-elements, scene-all-verses, stage-from-scripture, youth-noun, no-inflating-build |
| david-returns-jerusalem | night-pick s101 | – restyle-r6 기록에 몸 크롭 상자가 없다(바탕과 다른 그림) — OWLv2 상자는 GPU 단계라 이번 | ✗ 틀림 p.boarding | required-fields, whole-fields, verse-elements, no-compromise-words, scene-all-verses, cast-card-v2, lexicon-link, no-hand-prompt, no-bare-head, prop-in-prompt, 512-tokens, stage-from-scripture, action-place-on-figure, thrown-guide, guide-backdrop, guide-body-build, dodge-clear, guide-costume-legs, youth-noun, pose-skeleton, figure-scale, no-second-point, youth-height, height-ratio, split-control, prop-size-relative, flight-position, flight-height, empty-hand-open, wall-material, no-inflating-build, prop-size-coverage, held-hold, crowd-stage, eye-level-perspective |
| samuel-bethlehem-david-anointing | local-edit s42 | ✗ 틀림 background[0], crowds | ✅ 걸린 채택 문항 0 | required-fields, whole-fields, verse-elements, no-compromise-words, scene-all-verses, cast-card-v2, lexicon-link, no-hand-prompt, no-bare-head, prop-in-prompt, 512-tokens, stage-from-scripture, action-place-on-figure, thrown-guide, guide-backdrop, guide-body-build, dodge-clear, guide-costume-legs, youth-noun, pose-skeleton, figure-scale, no-second-point, youth-height, height-ratio, split-control, prop-size-relative, flight-position, flight-height, empty-hand-open, wall-material, no-inflating-build, prop-size-coverage, held-hold, crowd-stage, eye-level-perspective |
| samuel-ramah-death | night-pick s42 | ✗ 틀림 crowds, figures[0].prop | ✅ 걸린 채택 문항 0 | required-fields, whole-fields, verse-elements, no-compromise-words, scene-all-verses, cast-card-v2, lexicon-link, no-hand-prompt, no-bare-head, prop-in-prompt, 512-tokens, stage-from-scripture, action-place-on-figure, thrown-guide, guide-backdrop, guide-body-build, dodge-clear, guide-costume-legs, youth-noun, pose-skeleton, figure-scale, no-second-point, youth-height, height-ratio, split-control, prop-size-relative, flight-position, flight-height, empty-hand-open, wall-material, no-inflating-build, prop-size-coverage, held-hold, crowd-stage, eye-level-perspective |
| saul-gibeah-spear | local-edit s7 | – gibeah-step23 m15 기록에 몸 크롭 상자가 없다 — OWLv2 상자는 GPU 단계라 이번 범위  | ✅ 걸린 채택 문항 0 | 없음 |
| saul-gilgal-amalek | night-pick s11 | ✅ 9문항 맞음 | ✅ 걸린 채택 문항 0 | verse-elements, scene-all-verses, stage-from-scripture, no-inflating-build |
| saul-gilgal-coronation | attempt a005 s11 | – 단계 사다리 그림에 몸 크롭 상자 기록이 없다 — OWLv2 상자는 GPU 단계라 이번 범위 밖 | ✅ 걸린 채택 문항 0 | required-fields, whole-fields, verse-elements, no-compromise-words, scene-all-verses, cast-card-v2, lexicon-link, no-hand-prompt, no-bare-head, prop-in-prompt, 512-tokens, stage-from-scripture, action-place-on-figure, thrown-guide, guide-backdrop, guide-body-build, dodge-clear, guide-costume-legs, youth-noun, pose-skeleton, figure-scale, no-second-point, youth-height, height-ratio, split-control, prop-size-relative, flight-position, flight-height, empty-hand-open, wall-material, no-inflating-build, prop-size-coverage, held-hold, crowd-stage, eye-level-perspective |
| saul-jabesh-rescue | night-pick s42 | ✗ 틀림 background[0], crowds[0] | ✅ 걸린 채택 문항 0 | required-fields, whole-fields, verse-elements, no-compromise-words, scene-all-verses, cast-card-v2, lexicon-link, no-hand-prompt, no-bare-head, prop-in-prompt, 512-tokens, stage-from-scripture, action-place-on-figure, thrown-guide, guide-backdrop, guide-body-build, dodge-clear, guide-costume-legs, youth-noun, pose-skeleton, figure-scale, no-second-point, youth-height, height-ratio, split-control, prop-size-relative, flight-position, flight-height, empty-hand-open, wall-material, no-inflating-build, prop-size-coverage, held-hold, crowd-stage, eye-level-perspective |
| saul-michmash-battle | night-pick s202 | ✗ 틀림 crowds, figures[1].pose, figures[1].prop | ✅ 걸린 채택 문항 0 | required-fields, whole-fields, verse-elements, no-compromise-words, scene-all-verses, cast-card-v2, lexicon-link, no-hand-prompt, no-bare-head, prop-in-prompt, 512-tokens, stage-from-scripture, action-place-on-figure, thrown-guide, guide-backdrop, guide-body-build, dodge-clear, guide-costume-legs, youth-noun, pose-skeleton, figure-scale, no-second-point, youth-height, height-ratio, split-control, prop-size-relative, flight-position, flight-height, empty-hand-open, wall-material, no-inflating-build, prop-size-coverage, held-hold, crowd-stage, eye-level-perspective |
| saul-mizpah-chosen | night-pick s7 | ✗ 틀림 crowds, figures[0].pose, figures[0].prop, figures[1].faci | ✅ 걸린 채택 문항 0 | required-fields, whole-fields, verse-elements, no-compromise-words, scene-all-verses, cast-card-v2, lexicon-link, no-hand-prompt, no-bare-head, prop-in-prompt, 512-tokens, stage-from-scripture, action-place-on-figure, thrown-guide, guide-backdrop, guide-body-build, dodge-clear, guide-costume-legs, youth-noun, pose-skeleton, figure-scale, no-second-point, youth-height, height-ratio, split-control, prop-size-relative, flight-position, flight-height, empty-hand-open, wall-material, no-inflating-build, prop-size-coverage, held-hold, crowd-stage, eye-level-perspective |
| saul-nob-massacre | night-pick s303 | ✗ 틀림 figures[0].pose, figures[1].prop, figures[2].prop | ✅ 걸린 채택 문항 0 | verse-elements, scene-all-verses, stage-from-scripture, no-inflating-build |
<!-- recheck:images:end -->

## 기브아 규칙 넓힘 (2026-10-25 task 413, 원장 판 `cb0b1f5f7371`)

원장 판 `d63fb2faac26` → `cb0b1f5f7371`. 아래 칸 수는 `samples/recheck/specs.json`·`images.json`을 바꾸기 전 표와 견줘 뽑았다(손 집계 아님).

**무엇을 넓혔나** — ① 크기 기준표 규칙(figure-scale·youth-height·height-ratio·eye-level-perspective)은 걸릴 내용(사람·청년·두 사람·무리)이 있는데 guide 구역이 없으면 **빈 통과 → 못 잼**. 못 잼은 생성 관문(`require_pass`)에서 불통과다. ② 나는 물체(flight-position): 허공 물체 꼴이 있으면 던지는 뼈대 필수 — 꼴만 있는 창은 실패. ③ 새 규칙 `derive.held-hold`: 사전 `held` 15항목 모두 `look.hold`(쥔 꼴 — hand 11·hug 2·wear 1·touch 1), hug 항목을 쥔 장면은 파생 문구에 쥔 꼴 문구. 수금 hug 편집 지시는 사전에서 읽고 m17e 승인 s7 지시와 바이트 같음(시험 `HeldHold`).

**창 높이(flight-height)·나는 물체 자리는 다른 장면에 해당이 없다** — 순간 절에 던짐 동사가 있는 명세는 기브아뿐(골리앗은 던지기 전 순간, ADR 260903-154254). 그래서 바뀐 칸 0.

### 명세 — 바뀐 칸

| 규칙 | 바뀜 | 명세 |
|---|---|---|
| `derive.held-hold` | (새 규칙) → 실패 2 | solomon-jerusalem-birth, solomon-jerusalem-two-mothers |
| `derive.held-hold` | (새 규칙) → 통과 35 | 35개(아기 두 장면 밖 전부 — 기브아 포함) |
| `generate.eye-level-perspective` | 통과 → 못 잼 20 | 20개(가이드 없는 명세 전부 — 기브아·요단 밖) |
| `generate.figure-scale` | 통과 → 못 잼 35 | 35개(가이드 없는 명세 전부 — 기브아·요단 밖) |
| `generate.height-ratio` | 통과 → 못 잼 21 | 21개(가이드 없는 명세 전부 — 기브아·요단 밖) |
| `generate.youth-height` | 통과 → 못 잼 3 | david-gibeah-harp, david-goliath-gath, samuel-bethlehem-david-anointing |

새 규칙 실패 내용:
- solomon-jerusalem-birth: bathsheba: 손 지물 「an infant」(사전 baby hug)인데 파생 문구에 쥔 꼴 「cradled in both arms against the chest」 없음 — 손에 매단 꼴로 그려진다
- solomon-jerusalem-two-mothers: mother-a: 손 지물 「아기」(사전 baby hug)인데 파생 문구에 쥔 꼴 「cradled in both arms against the chest」 없음 — 손에 매단 꼴로 그려진다

### 승인 그림 — 바뀐 칸

| 규칙 | 바뀜 | 그림 |
|---|---|---|
| `derive.held-hold` | (새 규칙) → 통과 5 | david-gath-achish, david-gibeah-harp, saul-gibeah-spear, saul-gilgal-amalek, saul-nob-massacre |
| `derive.held-hold` | (새 규칙) → 낡음 7 | david-returns-jerusalem, samuel-bethlehem-david-anointing, samuel-ramah-death, saul-gilgal-coronation, saul-jabesh-rescue, saul-michmash-battle, saul-mizpah-chosen |
| `generate.figure-scale` | 통과 → 못 잼 4 | david-gath-achish, david-gibeah-harp, saul-gilgal-amalek, saul-nob-massacre |
| `generate.height-ratio` | 통과 → 못 잼 4 | david-gath-achish, david-gibeah-harp, saul-gilgal-amalek, saul-nob-massacre |
| `generate.youth-height` | 통과 → 못 잼 1 | david-gibeah-harp |

- 이번 넓힘으로 **새로 낡음이 된 승인 그림 0장**. `derive.held-hold` 낡음 7장은 이미 「그림 뒤 명세가 바뀜」으로 모든 명세 규칙이 낡음이던 그림(david-returns-jerusalem, samuel-bethlehem-david-anointing, samuel-ramah-death, saul-gilgal-coronation, saul-jabesh-rescue, saul-michmash-battle, saul-mizpah-chosen).
- 잰 규칙 모두 통과(못 잼 제외) 승인 그림 1/12 → 1/12 — 기브아 s7 그대로 통과.

### 재저작 후보 순서 (사람 결정용)

1. **아기 두 장면** — `derive.held-hold` 실패 2: 파생 문구에 「품에 안은」 꼴(사전 baby hold.en, 룻 4:16 [직접])을 싣는 명세 고침. 문구 하나라 가장 작다.
2. **승인 그림이 있는데 크기 못 잼인 장면** — david-gath-achish, david-gibeah-harp, samuel-bethlehem-david-anointing, samuel-ramah-death, saul-gilgal-amalek, saul-gilgal-coronation, saul-jabesh-rescue, saul-michmash-battle, saul-mizpah-chosen, saul-nob-massacre: guide 사람 구역 저작이 있어야 크기 기준표가 그림에 실린다. 그중 david-gibeah-harp가 기브아 규칙(청년 다윗·수금 hug)과 가장 가깝다.
3. **나머지 크기 못 잼 명세 25** — 무리 장면은 원근(eye-level-perspective) 못 잼도 함께 풀린다(guide 무리 꼴).

## 지금 규칙집 통과율과 다음 과제 (2026-10-22 task 396, 원장 판 `e09949ef99e7`)

- **원장 바뀜(task 396)**: `derive.clip-77-tokens` 폐기(사람 결정 — SDXL 단계별 경로 전용, 재검·통과율에서 뺌) · `derive.prop-in-prompt` 추가(지물이 한 장 프롬프트에 실림, 전 명세). 이제 CLIP 77을 뺀 숫자가 기본이다.
- **명세: 전 규칙 통과 1/37(요단) · 칸 통과 77%(284/370).** 규칙별: 장면 구절 상황 칸 4/37 · 구절 시각 요소 14/37 · 한 장 모드 칸 15/37 · **지물 실림 29/37** · 나머지 6규칙 37/37(타협 금지 낱말 포함 — task 394).
- **지물 실림 실패 8명세 = 다음 재저작 대상**(14지물, 모두 prop 칸이 한국어뿐 → 「영문 없음」): 골리앗 가드(창·방패·물매) · 솔로몬 7(에시온게벨·기브온 꿈·다윗 유언·궁전·스바·성전 봉헌·두 어머니 — 겉옷자락·왕홀·이불·허리띠·향품 상자·아기). 계획 때 어림값 14와 같다. 영문으로 실린 기브아 창(`a spear`·`a small wooden lyre`)은 통과.
- **승인 그림: 잰 규칙 모두 통과 0/12.** 명세·파생 규칙으로 낡지 않은 그림은 CLIP 77을 빼도 요단 1장뿐. J1 요소 판정(지금 명세 문항, 승인된 바로 그 그림)은 잰 10장 중 통과 1(길갈 아말렉) — 틀림 사유는 대부분 실제 결함으로 읽힌다(기브아 두 장 「작은 수금」이 켈트식 큰 하프 · 라마·놉 칼이 중세풍 직검 · 베들레헴 형 넷 · 야베스 천막 온전 · 믹마스 「겉옷자락 쥔 사람이 사울」). J1은 사람 앞 거르기 판정자(경계 합격)라 승인 취소 근거는 아니다 — 표시만. 상식 규칙은 요단 1장이 「배에 오름」 틀림(배 밖에 줄지어 선 사람) — 사람이 승인한 그림과 채택 규칙이 갈렸다.
- **출처 기록**: 승인 12장 중 생성 때 프롬프트 = 지금 파생 9장(요단 restyle 포함), 다름 2장(가드·베들레헴 국소 편집 — 바탕이 plain-words r2 사전 문구 회차라 명세 파생과 다름), 기록 없음 1장(길갈 대관식 단계 사다리). 앞으로 승인은 `approve`가 해시를 자동으로 적는다.
- **못 잰 것**: 요단 restyle·길갈 대관식 J1(몸 크롭 상자 없음 — OWLv2 상자 계산이 필요), 화풍(판정자 조건부), 얼굴(사람 판정 — task 393 화질 맞춤 화면).
- **다음 과제 후보(효과 순)**: ① 타협 금지 위반 3명세 재저작(task 394) → `recheck.py specs`로 확인 ② 장면 구절 상황 칸을 나머지 36명세에(문서 규칙 「단락 전체 읽기」와 함께 — 재저작 에이전트 + scripture-reviewer) ③ 승인 그림 중 J1 틀림 사유가 명세 칸과 맞는 장면(기브아 수금·칼 모양·베들레헴 형제)부터 바뀐 명세로 재생성 ④ 문서만 규칙을 검사로: 구도 가이드(주고받는 장면·배치) → 낱말 사전 연결 → 잘라붙이기 금지 ⑤ (끝남 — task 396에서 CLIP 77 폐기) 지물 실림 실패 8명세의 prop 영문화·몸짓 문구 ⑥ 몸 크롭 상자 없는 2장 OWLv2 상자 계산.
