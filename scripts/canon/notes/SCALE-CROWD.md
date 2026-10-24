# 크기 기준표 ② — 무리 단계·눈높이 원근 (task 409)

ADR 261024-083947 2항 ③④ · part 1(task 408, `notes/SCALE.md`)의 `scale.json`·`scale.py` 위에 얹음. GPU 0 — 그림 생성 없음.

## 무엇을 바꿨나

- **장면 사람 수** = `figures` 수 + `crowds[].count`. 20장면 28항목에 `count`·`count_why`(근거 단계 `[직접]`·`[추론]`·`[저작](이유)`)를 적음(data-author).
  **아둘람 1항목은 비워 둠** — `scenes/authored-david-adullam-cave.json`은 사용자 미커밋 파일(보존 해시 DoD 7 · 계획 「하지 않을 것」). 넣을 값: `400` · `[직접] 22:2 「그와 함께 한 자가 사백 명 가량이었더라」` → 큰 무리. 사람이 그 파일 변경을 커밋한 뒤 넣을 것.
- **표 `scale.json`** 새 층: `crowd_stage`(독대 1~2 → 0.60~0.70 · 작은 무리 3~20 → 0.45~0.60 · 큰 무리 21~999 → 0.35~0.50 · 군중 1000+ → 0.30~0.45 — 독대만 사람 조정 값, 나머지는 `[저작]` 첫 그림 판정에서 사람이 고칠 칸) · `perspective`(`eye` 0.93 · `horizon_default` 0.26 · `pose_seen` 0.75). 지킴 이름에 `FIGURE_MAX_H`·`FIGURE_MIN_H`·`FIGURE_MIN_SEEN`·`HORIZON` 더함.
- **`scale.py`**: `crowd_stage(n)` · `people_count(spec)` · `horizon(발 y, 화면 키, 키 등급)` · `screen_height(발 y, 지평선, 키 등급)` · `standing(spec)` · `scene_horizon(spec)`(화면 키가 가장 큰 서 있는 인물이 초점).
- **`recheck.py`**: `figure_scale_errors` 한도 = 무리 단계 범위(무리 꼴이 있으면 건너뛰던 것 없앰, 뼈대 인물 하한 = 단계 하한 × `pose_seen`) · `height_ratio_errors` = 지평선에서 계산한 화면 키와 비교(같은 발 y면 옛 「같은 깊이 키 비」와 같음 — depth 꼬리표가 아니라 발 y가 거리) · 새 `crowd_count_errors`(규칙 `derive.crowd-stage`) · `perspective_errors`(규칙 `generate.eye-level-perspective` — 무리 구역이 그 자리 어른 화면 키를 담는지).
- **`make_guide.py`**: 지평선 = `S.scene_horizon(spec)`(옛 고정 0.26) · 무리 꼴 두 줄 높이 = 발 y에서(발이 지평선 위인 둑·언덕 줄은 옛 상자 비).
- 원장 판 `80ede77c7dea` → `c7126d877734`(69규칙).

### 값이 바뀐 곳(전 → 후)

| 무엇 | 전 | 후 | 근거 |
|---|---|---|---|
| 기브아 지평선(방 바닥선) | 0.26 | 0.455 | 사울 발 0.98 · 화면 키 0.68 · tall 1.205 → 0.98 − 0.93 × 0.68 ÷ 1.205 |
| 요단 지평선 | 0.26 | 0.343 | 다윗 발 0.92 · 0.62 · average |
| 요단 시바 무리 사람 키(앞줄) | 0.25(상자 0.40 × 0.62) | 0.51 | 발 0.82 — 상자보다 큼(아래 재검) |
| 요단 유다 몇 사람 키(앞줄) | 0.17 | 0.47 | 발 0.78 — 상자보다 큼(아래 재검) |
| 요단 베냐민 일천 앞줄 | 0.07 | 0.04 | 발 0.38 — 지평선 바로 아래, 멀리 작게(387 메모 「조금멀리 원근감」과 같은 쪽) |
| 기브아 크기·키 비 검사 | 통과 | 통과(값 같음) | 독대 단계 = 옛 한도 · 같은 발 y |

기브아 가이드 그림은 방 바닥선이 0.26 → 0.455로 내려감(인물·창·뼈대는 그대로). 기브아 루프를 다시 돌릴 때 바탕 벽·바닥 비가 바뀐 가이드로 그려진다는 점을 먼저 볼 것.

## 장면별 무리 단계(37명세)

- 독대(0.60~0.70) 15: david-adullam-cave(1 — 수 비움, 넣으면 401 큰 무리) · david-gath-achish(2) · david-gibeah-harp(2) · david-nathan-covenant(2) · david-nob-priests(2) · david-ramah-samuel(2) · david-ziklag-base(2) · saul-gibeah-spear(2) · saul-gilgal-amalek(2) · solomon-ezion-geber-fleet(1) · solomon-gibeon-dream(1) · solomon-jerusalem-birth(1) · solomon-jerusalem-david-charge(2) · solomon-jerusalem-palace(1) · solomon-jerusalem-sheba(2)
- 작은 무리(0.45~0.60) 7: david-en-gedi-saul(8) · samuel-bethlehem-david-anointing(10) · saul-endor-medium(5) · saul-gilboa-death(10) · saul-nob-massacre(3) · solomon-jerusalem-apostasy(6) · solomon-jerusalem-two-mothers(3)
- 큰 무리(0.35~0.50) 3: david-gibeon-battle(86) · david-hebron-king-judah(51) · saul-michmash-battle(102)
- 군중(0.30~0.45) 12: david-ark-jerusalem(1001) · david-goliath-gath(6003) · david-jerusalem-conquest(1001) · david-mahanaim-exile(1001) · david-returns-jerusalem(2055) · samuel-ramah-death(1001) · saul-gilgal-coronation(330002) · saul-jabesh-rescue(330201) · saul-mizpah-chosen(1002) · solomon-gihon-anointing(1002) · solomon-jerusalem-temple-build(73301) · solomon-jerusalem-temple-dedication(10001)

가이드(`guide`)가 있는 장면은 둘뿐(기브아·요단) — 나머지는 가이드를 저작할 때 이 단계가 걸린다.

## 근거 검토

scripture-reviewer가 28항목 `count`·`count_why`를 개역한글(`data/bible/verses.json`)에 대조(인용 글자 대조는 스크립트).

- 1차: 틀림 1 · 약함 4
  - 틀림: 요단 「유다 사람 몇」 — 19:15(족속 전체 구절)를 근거로 달았고 「몇 사람」은 본문에 없는 말인데 인용부호 → 19:16 「급히 유다 사람과 함께 다윗 왕을 맞으려 내려올 때에」로.
  - 약함: 마하나임 300(같은 「모든 백성」을 다른 장면은 1000) → 1000 · 길갈 1000(같은 범위 11:8 계수가 있는데 「수 없음」, 야베스 칸과 모순) → `[추론]` 11:8 330000 · 솔로몬 배교(본문에 없는 「몇 사람」 인용) → 인용 빼고 본문 다수 vs 제단 앞 대표 소수 이유 명시 · 예루살렘 정복 200(근거 불분명).
- 2차: 틀림 0 · 약함 1 — 예루살렘 정복: `what`은 대상 11:4 「온 이스라엘」 평행을 같은 무리로 소개하는데 근거는 칸 밖이라 함 → 평행을 근거에 넣어 1000 `[저작]`(`what`은 그대로).
- 3차(최종): 28항목 모두 맞음.
- 헤브론 근거 인용은 「유다 사람들이 와서」 2:4로 줄임 — 「…기름을 부어」까지 실으면 돌연변이 시험(test_spec_judge m2 — 「기름」 요소를 지운 사본에 남으면 안 됨)이 새 칸에서 그 낱말을 찾음.
- 아둘람(판정 대상 밖): 넣는다면 `400` `[직접]` 22:2가 맞음.

판정표: 틀림 0 · 약함 0

## 재검 목록(장면별 수리는 따로 — 이 작업 범위 밖)

1. **요단 귀환 `generate.figure-scale` 통과 → 실패** — 사람 수 2055(베냐민 일천 [직접] · 유다 족속 1000 [저작] …) → 군중 단계 0.30~0.45인데 다윗 구역 0.62. 그러나 사람이 승인한 요단(restyle r6 s101)이 바로 이 구도다(387 메모 「다윗·시므이 일행(15+20) 포커스 · 베냐민 1천명은 조금멀리 원근감」).
   → 사람 결정: ① 군중 범위를 고친다 ② 사람 수를 「초점 곁 무리」만 센다(먼 무리는 원근이 줄이므로 단계에서 뺌) ③ 요단 구역을 군중 단계로 다시 저작. 기대값 약화로 맞추지 않음.
2. **요단 귀환 `generate.eye-level-perspective` 실패(새 규칙)** — 시바 무리(발 0.82, 어른 키 0.51 > 구역 0.40)·유다 몇 사람(발 0.78, 0.47 > 0.28): 가까운 무리 구역이 원근보다 낮게 저작됨. 가이드 무리 꼴은 이제 발 y에서 그려 구역 위로 솟고 한 줄에 한 사람만 들어감 → 요단 가이드 구역 재저작 필요(위 1과 함께 결정).
3. **아둘람 `derive.crowd-stage` 실패(새 규칙)** — 수 비움(위 「무엇을 바꿨나」). 사용자 미커밋 변경 커밋 뒤 400 [직접] 넣기.
4. **요단 유다 족속(gilgal) 구역은 지평선 위(둑)** — 평지 눈높이 셈 밖이라 무리 꼴·검사 모두 옛 상자 비. 둑 높이 칸이 생기면 셈에 넣을 것.
5. **기브아 가이드 바닥선 0.26 → 0.455** — 기브아 루프(task 407 파킹) 재개 때 가이드 바뀜. 실내 장면에서는 지평선과 뒷벽 밑선이 같지 않다(벽 밑선은 지평선 아래) — 벽 거리 칸이 없어 지금은 지평선 = 바닥선.
6. **기브아 루프 C8(기준 9b29989)** — task 408의 기브온·길보아 2칸에 더해 이번 요단 `generate.figure-scale` 1칸이 통과→실패. 루프 재개 전 사람 결정(C8 기준 커밋을 409 뒤로 옮길지).
7. **본문 파일 오탈자 의심** — `data/bible/verses.json` 삼상 17:21에 「블레섹」(장면 명세 quotes는 「블레셋」). data-author가 그 글자가 든 조각은 인용에서 뺌. 본문 파일 확인 필요(범위 밖).
8. **어림 단계 확인 칸** — 골리앗 양군 3000(군중) · 야베스 330000(11:8 계수 — 단계만 의미) · 성전 건축 73300(담군 + 관리, 건축자 셈 밖) · 기브온 신복 30씩. 단계가 그림 크기를 정하므로 첫 그림 판정 때 같이 볼 것.
