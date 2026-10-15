# 인물 LoRA 학습 시트 v2 — 사울·다윗·사무엘 (task 356, 인물 LoRA 1/2)

353 결론: 정의 문구만으로 그린 장면은 장면 사이 같은 인물 1/9(원인 수염 6·얼굴 5·나이대 4·체격 3 — 대부분 카드 층).
다음 수단은 정본에서 만든 인물 LoRA를 장면 전체 생성에 거는 것(2/2, task 357). 이 문서는 그 LoRA의 학습 시트를 정한다.

## 고정 절 (생성 전 작성 — 결과를 보고 바꾸지 않는다)

- 인물: `saul`·`david`·`samuel`. 트리거 낱말 `saul_bm`·`david_bm`·`samuel_bm`(`params.LORA_SHEET_TRIGGER`).
- **초상 6장** = 353 `~/.local/biblemap-imggen/cast-v2-pilot/face/<id>/s{11,42,7}-{front,34}.png` 그대로(시드 11이 현재 정본). 새로 그리지 않는다.
- **전신 후보 16장** = 시드 8(`[11, 42, 7, 23, 5, 101, 202, 303]`) × 자세 2묶음(`stand` 「standing still, full front view」 · `walk` 「walking, three-quarter side view」). 세로 768×1152, Z-Image-Turbo Q8(`batch/run_scene.gen_zimage`).
- 전신 문구 = 정본 화풍 낱말(`gen_face_canon.STYLE`) + 「full body, single figure, <자세>, plain light background」 + `gen_face_canon.look(cid)`(카드+얼굴 층, `head_text` 경유라 `bare head` 없음) + **카드 층 체격 `silhouette`·키 `heightRel`** + 「whole figure from head to feet」.
  - 계획과의 차이: `look()`은 머리 초상용이라 체격·키가 없다. 전신을 더하는 이유가 카드 층(체격)을 싣는 것이므로 두 낱말을 더했다.
- **거르기**: 사람이 인물마다 한 화면에서 「같은 사람으로 안 보이거나 정의와 안 맞는 그림」을 표시한다. 표시된 그림(초상 포함)을 뺀다.
- **남길 수**: 남은 전신이 8장 이상이면 시드 순(자세 번갈아)으로 10장까지. 8장 미만인 인물은 기록만 하고 다시 그리지 않는다 — 그 인물만 2/2에서 초상+남은 전신으로 학습할지 판단한다.
- **캡션** = `<트리거>, a man, <구도·자세·배경>`. 초상은 「close-up head portrait, facing forward / three-quarter view, plain cream background」, 전신은 「full body, single figure, <자세>, plain light background」. **수염·나이·체격 같은 정체성 낱말은 넣지 않는다** — 정체성이 트리거 낱말에 묶이게 한다.
- 위치: 후보 `~/.local/biblemap-imggen/lora-sheet-v2-src/<id>/<자세>-s<시드>.png`, 시트 `~/.local/biblemap-imggen/lora-sheet-v2/<id>/NN.png + NN.txt`(mflux 학습 데이터 형식) + `sheet.json`(인물별 남은 수·쓴 파일).
- 그림은 커밋하지 않는다(같은 문구·시드면 다시 그려진다 — 349 회고). 스크립트(`gen_lora_sheet.py`)·params·이 notes만 커밋.

## 시험 1~3장 확인 (일괄 생성 전)

- 인물당 `stand-s11` 1장(장당 약 69초). 사울·다윗: 짧은 검은 머리·곱슬이 머리를 덮음 — **대머리 없음**. 사무엘: 긴 흰 머리·가슴까지 흰 수염. 세 장 모두 **한 사람**, 머리부터 발끝까지 **잘리지 않음**, 미색 배경·연필 화풍.
- 체격: 사울은 어깨가 넓고 몸통이 두꺼움, 다윗은 마른 편, 사무엘은 좁은 어깨에 약간 굽음 — 카드 층 `silhouette`가 실린다.
- 이상 없음 → 나머지 45장 일괄 생성.

## 판정 페이지

- https://claude.ai/artifact/SKHmH2aXaekSuvG3YdP7za (비공개, 폰용 — 인물마다 한 화면: 기준 정본 s11 정면 + 초상 6 + 전신 16, 「빼야 할 그림을 누르기」). 생성기 `make_lora_sheet_page.py`.
- 전신 48장(시험 3 + 일괄 45, 일괄 3104초 ≈ 장당 69초)을 거르지 않고 전부 보였다. 생성 직후 눈으로 본 바: 48장 모두 한 사람·머리부터 발끝까지·대머리 없음.

## 사람 판정 (원문)

```
task 356 사람 판정
- 사울 · 빼야 할 그림을 누르세요 → 뺌: stand-s11, stand-s42, stand-s7, stand-s23, stand-s5, stand-s101, stand-s202, stand-s303, walk-s11, walk-s42, walk-s7, walk-s5, walk-s101, walk-s202, walk-s303
- 다윗 · 빼야 할 그림을 누르세요 → 뺌: stand-s11, stand-s42, stand-s7, stand-s23, stand-s5, stand-s101, stand-s202, stand-s303, walk-s11, walk-s42, walk-s7, walk-s5, walk-s101, walk-s202, walk-s303
- 사무엘 · 빼야 할 그림을 누르세요 → 뺌: stand-s42, stand-s23, stand-s5, stand-s101, stand-s202, walk-s42, walk-s23, walk-s202
(보여 준 그림: 인물마다 353 정본 초상 시드 [11, 42, 7] × 정면·3/4 + 전신 자세 ['stand', 'walk'] × 시드 [11, 42, 7, 23, 5, 101, 202, 303] — 거르지 않고 전부)
```

## 결과 — 인물별 남은 전신 수와 처리

| 인물 | 초상(뺌 0) | 전신 남음/16 | 시트(캡션 쌍) | 8장 미만 |
|---|---|---|---|---|
| 사울 | 6 | **1** (`walk-s23`) | 7 | 예 |
| 다윗 | 6 | **1** (`walk-s23`) | 7 | 예 |
| 사무엘 | 6 | 8 | 14 | 아니오 |

- 초상 18장은 하나도 빠지지 않았다. 빠진 것은 전부 전신이다.
- 고정 절 규칙대로 다시 그리지 않았다. 시트는 남은 것으로 썼다(`lora-sheet-v2/<id>/`, `sheet.json`). 사울·다윗은 「8장 미만 — 2/2에서 초상+남은 전신으로 학습할지 판단」 대상이다.
- **DoD 1(인물마다 캡션 쌍 12개 이상)은 사울·다윗에서 못 미친다(7).** DoD 1은 전신이 6장 이상 남는다고 본 값이고, 고정 절의 「8장 미만이면 기록만, 다시 그리지 않음」과 부딪힌다. 어느 쪽을 따를지는 사람 결정으로 넘긴다(검사를 낮추거나 다시 그리는 것 모두 이 계획 밖).

### 관찰 — 왜 사울·다윗 전신이 빠졌나 (참고, 판정 아님)

- 정본 초상과 전신 머리를 나란히 놓으면, 전신 크기에서는 사울·다윗 얼굴이 **만화체로 무너진다** — 동그란 점 눈, 붉은 볼, 웃는 입(다윗이 특히 심함). 살아남은 사울 `walk-s23`만 정본처럼 사실적인 눈·얼굴이었다.
- 사무엘은 노인 얼굴(주름·흰 수염·긴 흰 머리)이라 전신에서도 사실체가 유지됐고, 그래서 절반이 남았다.
- 짐작: 얼굴이 작아지면 「storybook illustration」 화풍 낱말이 얼굴을 만화 쪽으로 끈다(젊은 얼굴일수록). 353 장면에서 「얼굴 5」가 갈린 것과 같은 원인일 수 있다. 확인은 안 했다.
