# SPEC-REGEN — 두 겹 판정 2/3·3/3: 고친 명세로 재생성 → 예측 → 후보 화면 → 사람 판정 (task 379·380)

## 고정 절 (2026-10-20 — 생성·예측 전에 적음)

task 378이 사람 메모 6건과 되돌림 3장면의 원인을 명세로 고쳤다(`notes/SPEC-JUDGE.md`). 두 판정자는 모두 미채택이라 후보 규칙은 376 그대로다(이상한 점 결합 끔 — 이상한 점 답은 기록만).

### 기본값
- 장면 = `params.SPEC_REGEN_SCENES` 7개 = SPEC-JUDGE.md ```json regen(파생 프롬프트가 바뀐 장면). 가드는 파생 문구가 같아 뺐고, 놉은 고치지 않았다.
- 경로·시드 = 376과 같다: `derive_scene.route_prompt`, `VERSE_REGEN_SEEDS` 8개(11·42·7·23·5·101·202·303), 후보 편집 끔. `run_night.py all --set spec-regen` 한 번에 생성 → 문항 페이지(J1용) → 예측(J1·J1-prop·O1) → 후보 화면.
- 후보·되돌림·블라인드 표본 규칙 = notes/VERSE-REGEN.md 고정 절 그대로(`judge_learn.pick_candidates`, 결합 끔).
- 사람 화면 = 폰 360px 비공개 Artifact. 시간은 벽시계(`human_minutes`)와 **쉼 뺀 시간**(`active_minutes` — 입력 없이 2분 넘은 간격을 뺌, 376 회고)을 함께 적는다.

| 장면 | 고친 것(378) | 376 사람 답 |
|---|---|---|
| authored-david-gibeon-battle | 순간 2:15-16 전반 · 소년 열둘씩 가까이 · 신복 못가 · 지휘관 차림 | 없음 |
| authored-david-mahanaim-exile | 함께한 백성 행렬 | 없음 |
| authored-david-returns-jerusalem | 유다 사람들 강가에서 맞음 · 나룻배 | 없음 |
| authored-samuel-bethlehem-david-anointing | 형제들 · 뿔은 사무엘만 | 없음 |
| authored-david-jerusalem-conquest | 종자들 다윗 바로 뒤 | 되돌림 동의 |
| authored-saul-endor-medium | 동행 젊은 종 · 사무엘 허리 위만 | 되돌림 동의 |
| authored-saul-gilboa-death | 칼은 칼집에 | 되돌림 동의 |

### `판정:` 규칙 (3/3에서 — 셋 다면 `판정: 두 겹 판정 채택`, 하나라도 어기면 `판정: 보류 (어긴 규칙 …)`)
1. **사람 메모 재발 ≤ 1** — 아래 `recur` 항목마다 「재발」 = 그 장면 사람 답이 「없음」이고 장면 메모가 `words`에 맞음, **또는** 사람이 본 후보 시드에서 `qids` 중 하나를 「틀림」으로 표시함. 되돌림에 동의한 장면은 그 장면 항목 전부를 재발로 센다(그림이 나오지 않았다). 가드(침이 수염에)는 재생성하지 않아 항목에서 뺀다.
2. **「쓸 만함」 ≥ 5** — 재생성 7장면 중. 376 기준선은 이 7장면에서 0.
3. **되돌림 살림 = 0** — 기계 되돌림을 사람이 뒤집어 시드를 살린 수.
- 측정만(규칙 아님): 블라인드 칸 J1 잡기·통과, 이상한 점(O1)의 블라인드 칸 대비 잡기·통과(가드 칸 라벨 기준), 사람 화면 수·벽시계 분·쉼 뺀 분, 믿음 관문·학습 곡선 전후.

```json fixed
{
  "recur": [
    {"id": "g1", "scene": "authored-david-gibeon-battle", "what": "기브온 — 겨루는 몸짓", "qids": ["moment", "crowds[2]"], "words": "제스처|몸짓|싸우|겨루"},
    {"id": "g2", "scene": "authored-david-gibeon-battle", "what": "기브온 — 지휘관 차림 시대감", "qids": [], "words": "옷|차림|시대|갑옷"},
    {"id": "g3", "scene": "authored-david-gibeon-battle", "what": "기브온 — 열둘 대 열둘이 가까이", "qids": ["crowds[2]"], "words": "멀리|먼|12|열둘"},
    {"id": "m1", "scene": "authored-david-mahanaim-exile", "what": "마하나임 — 함께한 백성", "qids": ["crowds"], "words": "혼자|무리|백성"},
    {"id": "r1", "scene": "authored-david-returns-jerusalem", "what": "요단 귀환 — 유다 사람들의 도움·나룻배", "qids": ["crowds"], "words": "나룻배|배|돕|도와|건네|맞"},
    {"id": "b1", "scene": "authored-samuel-bethlehem-david-anointing", "what": "베들레헴 — 형제들", "qids": ["crowds"], "words": "형제"},
    {"id": "b2", "scene": "authored-samuel-bethlehem-david-anointing", "what": "베들레헴 — 기름 붓는 이는 사무엘", "qids": ["figures[0].pose", "figures[0].prop"], "words": "누구|붓"}
  ],
  "rules": {"recur_max": 1, "usable_min": 5, "revive_max": 0}
}
```
