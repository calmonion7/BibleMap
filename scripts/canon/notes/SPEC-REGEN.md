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

## 2/3 결과 — 무인 재생성·예측·후보 화면 (2026-10-20, task 379)

- 생성: `run_night.py all --set spec-regen` 한 번, 재시작 0 — 56장(7장면 × 8시드) wall 3683.6초. 시험 1장(기브온 s11 92.5초)은 본 실행이 건너뜀.
- 예측: J1·J1-prop·이상한 점(O1) 각 56장, 답 없음 0, 200초.
- 후보 화면 `spec-regen-cand.html` 11.37MB(1216px q84) · **9화면**(2 × (7 − 5) + 5) · 되돌림 5장면.
- 비공개 Artifact(폰): https://claude.ai/artifact/VREVMECmakaEExbaeddTVr
- `check_cand_page.py 379`: 360px·1280px 화면 9 · 가로 넘침 0 · 쉼 뺀 타이머(가짜 시계 60초 + 3분 멈춤) 쉼 뺀 1.0분·벽시계 4.0분 — 통과.
- 생성 검사 한 줄(C4): `python3 -c "import json,sys;sys.path.insert(0,'batch');import judge_items as J;m=json.load(open('samples/spec-regen/metrics.json'));j=J.load()['t379'];assert sum(len(s['seeds']) for s in m['scenes'].values())==7*8;assert all(len(j[k]['answers'])==56 and all(r.get('answers') for r in j[k]['answers'].values()) for k in ('J1','J1-prop','O1'));print('ok')"`

### J1 장면별 후보·되돌림 (`judge_learn.py cand 379`, 결합 끔)

| 장면 | 기계 | 틀림 칸(시드별) | J1 장면 뜻 이유(예) |
|---|---|---|---|
| 기브온 | 되돌림 | s11:5 s42:7 s7:7 s23:3 s5:5 s101:3 s202:2 s303:6 | 「소년들이 전부 앉아만 있고 짝지어 맞서 머리를 잡는 장면이 없다」 |
| 마하나임 | 후보 s101 · 표본 s23 | s11:5 s42:5 s7:5 s23:3 s5:4 s101:2 s202:5 s303:4 | (틀린 장) 「다윗이 행렬 중간·맨 앞에 다른 인물」 |
| 요단 귀환 | 되돌림 | s11:5 s42:4 s7:4 s23:4 s5:4 s101:3 s202:5 s303:4 | 「유다 사람들이 등을 보이고 강 쪽을 향해 섬, 배는 강 한가운데」 |
| 베들레헴 | 후보 s11 · 표본 s23 | s11:3 s42:3 s7:7 s23:3 s5:3 s101:4 s202:5 s303:3 | (틀린 장) 「이새의 장대 끝이 뿔처럼 생김」 |
| 시온 산성 | 되돌림 | s11:4 s42:4 s7:3 s23:6 s5:3 s101:4 s202:4 s303:4 | 「종자들이 성벽 아래 멀리 줄지어 섬」(376과 같음) |
| 엔돌 | 되돌림 | s11:3 s42:6 s7:4 s23:7 s5:8 s101:6 s202:11 s303:4 | 「사무엘이 전신으로 서 있음 · 문 가 둘 중 하나가 수염 난 노인」 |
| 길보아 | 되돌림 | s11:6 s42:4 s7:4 s23:6 s5:3 s101:3 s202:3 s303:3 | 「사울과 병기 든 자 모두 칼을 뽑아 듦」(376과 같음) |

- 이상한 점(O1, 기록만): 7장면 모두 7~8/8 「있음」 — 378 교정과 같은 과잉 경향.
- 관찰(이번엔 명세를 다시 고치지 않음 — 계획): 명세 문구를 고친 5장면 중 4장면(기브온·시온·엔돌·길보아)에서 J1이 짚는 결함이 376과 같은 축으로 남았다. 문구로 바꾼 배치·상태(앉음↔맞붙음, 원경↔바로 뒤, 칼집, 허리 위만)가 그림으로 옮겨지지 않는 PROMPTING 24(문구 경로로 안 움직이는 축)와 같은 양상으로 보인다. 확정은 3/3의 사람 판정에서.
