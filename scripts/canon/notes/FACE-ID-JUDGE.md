# FACE-ID-JUDGE — 얼굴 인식 판정자(ArcFace)가 `.identity` 문항을 사람처럼 답하는가 (task 350)

J1(Sonnet)은 `.identity`(정본과 다른 사람으로 보이나) 문항을 빼고 판정한다(`batch/judge_items.py` items). 이 문항은 지금도 사람만 본다. 이번에는 사람이 368~372 한 장 생성 그림에 단 `.identity` 라벨 192개로 ArcFace를 교정하고 검증한다. 새 그림 생성(GPU)도, 새 사람 판정도 없다.

## 고정 절 (실행 전, 2026-10-22 — 기계 점수를 보기 전에 적음)

- **문항·라벨** = 사람이 본 판정 페이지(`~/.local/biblemap-imggen/pages/{night,whole-fix,whole-wide,jabesh-crowd}-pick.html`) `SCENES`의 `.identity` 문항, 라벨은 metrics `items`. 사람이 그 시드를 「틀림」으로 눌렀으면 **「다른 사람」**, 아니면 **「같은 사람」**. `unsure`·`skipped`·`auto`와 판 묶음(`grp: plate`)은 뺀다(J1 `items()`와 같은 규칙, 해당 0개).
- **그림** = 사람이 본 그림. 368은 편집본(`edits[who[-1]]`), 나머지는 바탕(J1과 같음).
- **머리** = 페이지 문항의 `crop[시드]`(사람이 본 머리 크롭 — `make_night_page.fit(head, 1, W, H, 0.5)`로 이미 넓힌 비율 상자) 그대로 자름. **정본** = 문항 `canon` → `frozen/<canon>.png`.
- **판정자** = InsightFace `buffalo_l`(검출 + 5점 정렬 + ArcFace `w600k_r50`). 머리 크롭이 작으니 긴 변 512px로 키운 뒤 검출한다. 여러 얼굴이면 가장 큰 얼굴. insightface 설치가 실패하면 `onnxruntime` + `w600k_r50.onnx`를 정렬 없이 112px로 키운 크롭에 직접 쓴다. 어느 쪽인지 metrics `embedder`에 남긴다.
  - 덧붙임(라벨 점수 보기 전, 검출 시험에서): 정본 대부분이 168~229px 얼굴 크롭이라 그대로는 검출이 안 됨(nahash 194px → 0개). **정본·대조 그림도 같은 전처리**(긴 변 512px로 맞춤)를 쓴다. 양성 대조 「48px로 줄였다가 다시 키움」은 정본 그림을 검출된 얼굴 높이가 48px가 되게 줄였다가 원래 크기로 되돌린 것이다.
- **점수** = 정본 임베딩과 머리 임베딩의 코사인. **얼굴을 못 찾으면 점수 없음 = 기계 답 「다른 사람」**(무인에서 「모름」은 버리는 쪽이 안전). 검출 실패 수는 따로 적는다.
- **τ** = 다듬기 묶음에서 min(잡기, 통과)이 가장 큰 값(후보 = 다듬기 점수 사이의 중간점들). 같으면 잡기가 큰 쪽. 기계 「다른 사람」 = 점수 < τ 또는 점수 없음.
- **잡기** = 사람 「다른 사람」 라벨 중 기계도 「다른 사람」 · **통과** = 사람 「같은 사람」 라벨 중 기계도 「같은 사람」(JUDGE-ITEMS와 같은 정의).
- **음성 대조** = 라벨에 나오는 정본(saul·samuel·david·david-boy·achish·ahimelech·doeg·nahash) 각각 대 나머지 `frozen/*.png` 전원(같은 인물 나이 변형 `saul`↔`saul-old`, `david`↔`david-boy`↔`david-old`, `solomon`↔`solomon-old` 뺌). 얼굴 못 찾으면 점수 없음 = 「다른 사람」(음성으로는 맞음).
- **양성 대조** = 정본 대 자기 변형(좌우 반전 · 밝기 +20% · 밝기 −20% · 장면 머리 크기 48px로 줄였다가 다시 키움). 얼굴 못 찾으면 점수 없음 = 실패.
- **go 조건(전부)**: ① 양성 대조 전부 ≥ τ ② 음성 대조 전부 < τ(또는 점수 없음) ③ 검증 잡기 ≥ 80% ④ 검증 통과 ≥ 80%. 하나라도 어기면 no-go.
- **참고값(결론에 쓰지 않음)**: 다듬기 AUC · 검증 잡기·통과의 Wilson 95% 하한(믿음 관문 0.8과 견줌) · 인물별 잡기·통과 · 검출 실패 수 · 「전부 한쪽으로 예측했는가」(기계 「다른 사람」 비율).
- 상수는 `params.py` `FACE_ID_*`. 집계는 손으로 하지 않는다 — `judge_face_id.py`가 metrics와 아래 결과 절을 쓴다.

### 라벨 표 (페이지·metrics에서 센 값 — 계획의 미리 센 값 다듬기 96/22·검증 96/27과 같음)

| 묶음 | 과제 | 장면 | 문항 | 정본 | 라벨 | 다른 사람 |
|---|---|---|---|---|---|---|
| 다듬기 | 368 | saul-gibeah-spear | figures[0] | saul | 8 | 1 |
| 다듬기 | 368 | saul-gibeah-spear | figures[1] | david | 8 | 6 |
| 다듬기 | 368 | saul-mizpah-chosen | figures[0] | samuel | 8 | 0 |
| 다듬기 | 368 | saul-mizpah-chosen | figures[1] | saul | 8 | 3 |
| 다듬기 | 368 | saul-michmash-battle | figures[0] | saul | 8 | 0 |
| 다듬기 | 368 | saul-michmash-battle | figures[1] | samuel | 8 | 3 |
| 다듬기 | 368 | saul-gilgal-amalek | figures[0] | saul | 8 | 3 |
| 다듬기 | 368 | saul-gilgal-amalek | figures[1] | samuel | 8 | 3 |
| 다듬기 | 368 | samuel-ramah-death | figures[0] | david | 8 | 2 |
| 다듬기 | 369 | saul-gilgal-amalek | figures[0] | saul | 8 | 1 |
| 다듬기 | 369 | saul-gilgal-amalek | figures[1] | samuel | 8 | 0 |
| 다듬기 | 369 | samuel-ramah-death | figures[0] | david | 8 | 0 |
| 검증 | 370 | david-gibeah-harp | figures[0] | david-boy | 8 | 0 |
| 검증 | 370 | david-gibeah-harp | figures[1] | saul | 8 | 1 |
| 검증 | 370 | david-nob-priests | figures[0] | ahimelech | 8 | 3 |
| 검증 | 370 | david-nob-priests | figures[1] | david | 8 | 3 |
| 검증 | 370 | david-gath-achish | figures[0] | david | 8 | 4 |
| 검증 | 370 | david-gath-achish | figures[1] | achish | 8 | 0 |
| 검증 | 370 | saul-jabesh-rescue | figures[0] | saul | 8 | 6 |
| 검증 | 370 | saul-jabesh-rescue | figures[1] | nahash | 8 | 6 |
| 검증 | 370 | saul-nob-massacre | figures[0] | saul | 8 | 0 |
| 검증 | 370 | saul-nob-massacre | figures[1] | doeg | 8 | 3 |
| 검증 | 370 | saul-nob-massacre | figures[2] | ahimelech | 8 | 0 |
| 검증 | 372 | saul-jabesh-rescue | figures[0] | saul | 8 | 1 |
| **다듬기 계** | | | | | **96** | **22** |
| **검증 계** | | | | | **96** | **27** |

- 대조 검출 기록(라벨 점수 보기 전): 정본 4장(david-old·endor-medium·jesse·nahash — 옆얼굴·눈 감고 숙임·얼굴이 그림 끝에 붙음)에서 얼굴을 못 찾음. 사방 20% 여백을 덧대 **한 번** 다시 시험했으나 4장 그대로 → 되돌리고 고정 절 전처리 유지. nahash는 검증 라벨 정본이라 규칙대로 그 양성 대조 4개·머리 점수는 「점수 없음」이다.
- 위험(측정 전 기록): 사람 문항은 「얼굴·머리·수염·나이대」를 본다. ArcFace는 얼굴만 본다. 머리카락·수염 차이로 누른 「다른 사람」은 ArcFace가 놓칠 수 있다.

## 결과

- 판정자: insightface buffalo_l (det_10g + 5점 정렬 + w600k_r50 ArcFace), 긴 변 512px로 맞춘 뒤 검출, 가장 큰 얼굴
- **τ = 0.2446** (다듬기 묶음 min(잡기, 통과) 최대)

| 묶음 | 잡기 | 통과 | 기계 「다른 사람」 비율 | AUC | 검출 실패 |
|---|---|---|---|---|---|
| 다듬기 | 11/22 50.0% | 40/74 54.0% | 46.9% | 0.5246 | 0 |
| 검증 | 18/27 66.7% | 31/69 44.9% | 58.3% | 0.6409 | 11 |

go 조건:
- ① 양성 대조 전부 ≥ τ — ❌ (양성 최소 0.8629, τ 밑: nahash flip None, nahash bright+20 None, nahash bright-20 None, nahash down48 None)
- ② 음성 대조 전부 < τ — ❌ (음성 최대 0.7924, τ 이상 19쌍: achish~abner 0.5437, achish~agag 0.379, achish~doeg 0.3707, achish~joab 0.3279, achish~nathan 0.4091, ahimelech~abner 0.2873, ahimelech~solomon-old 0.2746, ahimelech~zadok 0.2869)
- ③ 검증 잡기 ≥ 80% — ❌ (18/27 66.7%)
- ④ 검증 통과 ≥ 80% — ❌ (31/69 44.9%)

참고값(결론에 쓰지 않음):
- 검증 Wilson 95% 하한: 잡기 47.8% · 통과 33.8% (믿음 관문 80%)
- 한쪽 예측 확인: 기계 「다른 사람」 비율 다듬기 46.9% · 검증 58.3% (사람 비율 다듬기 22/96 22.9% · 검증 27/96 28.1%) — 양쪽 모두 예측함
- 정본 검출 실패: david-old, endor-medium, jesse, nahash · 양성 검출 실패 4
- 인물별(검증): achish 잡기 0/0 통과 7/8 · ahimelech 잡기 0/3 통과 13/13 · david 잡기 1/7 통과 6/9 · david-boy 잡기 0/0 통과 5/8 · doeg 잡기 3/3 통과 0/5 · nahash 잡기 6/6 통과 0/2 · saul 잡기 8/8 통과 0/24
- 인물별(다듬기): david 잡기 6/8 통과 1/16 · samuel 잡기 1/6 통과 26/26 · saul 잡기 4/8 통과 13/32

판정: no-go
### 해석 (2026-10-22, 판정 뒤)

- 측정 확인: 머리 크롭 12장을 정본과 나란히 눈으로 봤다 — 크롭은 사람이 본 머리를 정확히 잡는다(측정 버그 아님).
- 왜 안 되나: 장면 인물은 대개 **옆얼굴·고개 돌림**이고 정본은 정면이다. ArcFace 코사인이 같은 사람이어도 0.1~0.3에 몰려(사울 통과 0/24 검증) 사람 라벨과 상관이 거의 없다(AUC 0.52·0.64). 반대로 **같은 화풍의 서로 다른 정본**끼리는 0.79까지 올라(음성 τ 이상 19쌍) 얼굴 인식 모델이 그림체를 사람으로 읽는다. nahash 등 옆얼굴 정본 4장은 검출조차 안 된다.
- 즉 문턱을 어디에 두어도 ①②와 ③④를 함께 만족할 수 없다 — 문턱 조정으로 고칠 일이 아니다.

다음 과제: 얼굴은 사람 판정으로 남김, 생성기 쪽 얼굴 고정은 외부 조사부터.
