# 정본 참조 편집 판정 — 2511 + Lightning 4스텝 (task 360)

359는 Qwen-Image-Edit-2511이 이 맥에서 장당 48~60분이라 「실행 불가」였다. 후속 시험(`REF-EDIT-2511.md` 「후속 시험」)에서 Lightning 4스텝 LoRA + guidance 1 래퍼로 장당 약 8분, **외형을 명시한 지시문이면** 인물이 실제로 바뀌는 것(상자 안 49.6 / 밖 16.3)을 확인했다. 이번에는 이 설정으로 358·359와 같은 32번 편집을 하고 같은 규칙으로 판정한다. 2511과 LoRA가 모두 apache-2.0이라 결과가 좋으면 영상 패키지에 쓸 수 있는 첫 경로다.

## 고정 절 (편집·판정 전 작성 — 결과를 보고 바꾸지 않는다)

### 모델과 「안 돔」

- **Qwen-Image-Edit-2511** + **Lightning LoRA** `lightx2v/Qwen-Image-Edit-2511-Lightning` `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors` 세기 1.0(`params.REF_EDIT_LIGHTNING_LORA`). 둘 다 apache-2.0.
- 실행: `mflux_qwen_edit_cfg1.py`(guidance 1일 때 부정 계산 건너뛰기, 설치 패키지 무수정) — 인자는 `mflux-generate-qwen-edit`와 같다. mflux 0.22.0, `~/.local/biblemap-imggen/.venv-mflux`.
- 4스텝, guidance 1. 스텝·LoRA 세기 미리보기 없이 고정.
- 양자화: q8 `--low-ram`. 「안 돔」 = **첫 1장** 장당 10분 초과(`REF_EDIT_LIGHTNING_MAX_SEC` 600) 또는 실행 오류·깨진 출력. 그러면 q6 한 번만 보고, 그래도 안 되면 판정 없이 `결론: 실행 불가`와 사유, `metrics.json` `stop`.
- 생성 프로세스는 한 번에 하나(겹치면 처리량이 무너진다). 시간 제한은 프로세스 그룹째 종료한다.

### 지시문 (지시문 하나로 고정 — 비교 없음)

- 「Change the man on the {side} in image 1 into the man shown in image 2 and image 3: {look}. Keep his pose, his position and size in the scene, and keep the pencil and watercolor drawing style and everything else in image 1 unchanged.」(`params.REF_EDIT_LIGHTNING_PROMPT`)
- `{side}`: 그 장면 정본 인물 둘의 머리 상자 x 중심 순서로 left/right(359 `gen_ref_edit_2511.side`와 같다).
- `{look}`: `derive_scene.cast_describe(derive_scene._cast_in_scene(figure))` — 정본 카드 층에 그 장면 `cast_override`를 얹은 것, **장면 문구와 같은 낱말**을 기계적으로 넣는다. 손으로 쓰지 않는다.
  - 길갈 사울: 「an ancient Israelite man, a king, in his 40s, deep forehead lines, tall of stature, close-trimmed dark beard, jawline visible, broad shoulders, thick barrel torso, short dark hair cut close, hair covering the whole head, no headwear, in a dark wool tunic with a leather belt」
  - 엔게디 사울(장면 덮어쓰기 `build: none` — 키 낱말 빠짐): 「an ancient Israelite man, a king, in his 40s, deep forehead lines, close-trimmed dark beard, jawline visible, broad shoulders, thick barrel torso, short dark hair cut close, hair covering the whole head, no headwear, in a dark wool tunic with a leather belt」
  - 엔게디·라마 다윗: 「an ancient Israelite man, a commander, in his 20s, lean angular face, close-trimmed dark beard, jawline visible, lean wiry shoulders, narrow waist, dark curls close to the skull, hair covering the whole head, no headwear, in a dark wool tunic with a leather belt」
- **사울 정의와 전신 그림의 어긋남은 기록만 한다.** 카드 층은 「통짜 몸통」, 참조 전신 `lora-sheet-v2/saul/07.png`은 마른 체격이다. 지시문은 정의(카드 층)를 따른다. 그림 쪽 서술로 바꾸는 것은 사람 결정이다.

### 바탕·대상·참조·되붙임 (359와 같다)

- 바탕: 353 문구 Z-Image 1216×640. 시드 `[11, 42, 7, 23, 5, 101, 202, 303]` — 11·42·7은 `cast-v2-pilot/scene/`, 나머지는 `ref-edit/base/`.
- 처치: 길갈 사울 · 엔게디 사울 → 다윗(사울을 되붙인 결과 위에 다윗 편집) · 라마 다윗. 편집 수 32.
- 참조(`--image-paths` 순서): 입력 그림 · 정본 초상 `frozen/<id>.png` · 정본 전신 `lora-sheet-v2/<id>/07.png`.
- 되붙임: 전체 편집 원본에서 358 몸 상자(`gen_ref_edit.make_mask`) 안만 입력 그림에 얹는다. 경계는 가우시안 8px 알파.
- 산출: 원본 `~/.local/biblemap-imggen/ref-edit-lightning/raw/<장면>/s<시드>-<인물>.png`, 되붙인 최종 `edit/<장면>/s<시드>.png`(엔게디 사울 중간본 `s<시드>-saul.png`). 목록 `samples/ref-edit-lightning/metrics.json`.

### 조작 확인 (359 결함 수정)

- `targeted` = **전체 편집 원본**과 **그 편집의 입력 그림**(엔게디 다윗은 사울 되붙인 결과, 나머지는 바탕)의 픽셀 차(RGB 평균 0~255)를 **몸 상자 안 평균 − 상자 밖 평균**으로 잰다. 359 「mask_diff ≥ 10」은 재렌더 잡음(상자 밖 약 15)만으로 통과해서 무처치를 걸러내지 못했다. 이 식은 후속 시험 두 장을 재현한다(고정 절 지시문 12.53 − 15.18 = −2.65, 외형 명시 49.61 − 16.26 = 33.35).
- 참고값으로 359식 `mask_diff`(되붙인 결과의 상자 안 차)도 같이 적는다.
- **S0 첫 1장 targeted ≥ 10**(`REF_EDIT_LIGHTNING_MIN_TARGETED`)이고 눈으로 봐서 정본 쪽으로 바뀌었어야 본 편집으로 간다. **32장 평균 `targeted_mean` ≥ 10**이어야 판정 페이지를 게시한다. 미달이면 그 자리에서 멈추고 사용자에게 묻는다.

### 판정 규칙 (358 `REF-EDIT.md` 「판정 규칙」과 같다 — 섞기 시드만 360)

- 보기 방식: 카드 폭 356 CSS px(DPR 3), 확대·크롭 없음, 대상 머리 위 ▼, 두 장면 위/아래, 한 화면 한 질문, 폰용 비공개 Artifact.
- 화면 A 2(사울 길갈↔엔게디, 다윗 엔게디↔라마): 처치 8쌍 + 대조 3쌍(353 s11·42·7 바탕끼리), 고정 시드 360으로 섞는다. 「두 ▼가 같은 사람으로 읽히는 쌍을 누르기」.
- 화면 B 1: 엔게디 처치 8장 「두 ▼ 인물이 서로 닮아 구별이 안 되는 그림을 누르기」.
- 화면 C 3: 장면마다 기준(345 승인본, 라마는 353 s11) + 처치 8 + 대조 3, 시드 360으로 섞음. 「연필 화풍이나 장면 뜻이 기준보다 크게 무너진 그림을 누르기」.
- 분해능: 화면 A 대조 「읽힌다」 합 ≤ 2/6. 넘으면 `판정: 보류`.
- **채택** = 분해능 충족 + 사울·다윗 모두 「읽힌다」 ≥ 5/8. (처치 무너짐 비율 − 대조 무너짐 비율) > 0.5면 조건부로 내린다(세 장면 합산). **조건부** = 한 명만 ≥ 5/8 또는 화풍 감점. **다른 길** = 그 밖.
- 결론 줄 끝: 「영상 패키지 사용: 가능(apache-2.0 — 2511·Lightning LoRA)」.
- 판정 결과 표에 `targeted_mean`과 장면별 평균을 같이 적는다.
- 쌍·그림 번호 ↔ 처치/대조·시드 대응은 **게시 전에** `samples/ref-edit-lightning/metrics.json` `screens`에 적는다.
- 채택이면 ADR `260904-055320`을 뒤집는 새 ADR(실측표 포함). 조건부·다른 길이면 그 ADR 개정 메모에 결과 한 줄.

## S0 첫 장 (2026-10-17)

q8 `--low-ram`, 시드 11. 산출 `~/.local/biblemap-imggen/ref-edit-lightning/try/`, 기록 `samples/ref-edit-lightning/metrics.json` `try`.

| 편집 | 장당 | 피크 | 상자 안 / 밖 | targeted | 눈으로 |
|---|---|---|---|---|---|
| 길갈 사울 | 515.9초 | 58.5GB | 36.84 / 14.89 | **21.94** | 정본 쪽으로 바뀜 — 짧게 깎은 머리·짧은 수염·두건 망토 → 허리띠 맨 짙은 튜닉. 든 손 자세·위치·뒤 군중 유지, 이음매 안 보임. 체격은 바탕의 통짜 몸통 그대로(카드 층 문구대로) |
| 엔게디 사울 | 512.8초 | 58.5GB | 28.97 / 15.97 | **13.0** | 바뀜 — 망토 벗겨지고 짙은 튜닉, 웅크린 자세 유지 |
| 엔게디 다윗(사울 결과 위) | 493.0초 | 58.5GB | 12.2 / 13.69 | **−1.49** | **사실상 무처치.** 지목(left)은 맞다. 바탕 다윗이 이미 서술(짙은 곱슬·짧은 수염·마른 체격·짙은 튜닉+가죽 허리띠)과 같아 바꿀 곳이 없었다 |
| 라마 다윗(확인용 1장 더) | 499.6초 | 58.5GB | 20.95 / 12.68 | **8.27** | **하한 미달, 정본에서 멀어짐.** 바탕 다윗은 정본 그림처럼 붉은 튜닉이었는데 카드 층 「dark wool tunic」대로 짙은 튜닉으로 바뀌었다. 얼굴·머리는 거의 그대로 |

- 「안 돔」 아님: 장당 약 8.4분(하한 10분 안), q8 그대로.
- **관찰: 외형 명시 지시문은 참조 그림이 아니라 문구 쪽으로 끈다.** 바탕이 같은 카드 층 문구로 그려졌으므로, 문구와 다른 곳(사울의 망토·덥수룩한 수염)만 바뀌고 이미 문구와 같은 인물(다윗)은 그대로다. 다윗은 정본 그림(붉은 튜닉)과 카드 층(짙은 튜닉)이 어긋나서, 바꾸면 오히려 정본 그림에서 멀어진다 — 사울의 체격 어긋남과 같은 종류다.
- 첫 장(길갈) 기준은 통과지만, 다윗 2장이 모두 하한 미달이라 32장 평균(사울 약 17, 다윗 약 3)이 하한 10 언저리이고 다윗 처치는 대조와 구별되지 않을 것이다. 고정 절 「조작 확인에 걸리면 멈추고 묻는다 · 그림 쪽 서술로 바꾸기는 사람 결정」에 따라 **본 편집(S1) 전에 멈췄다.**

## 개정 절 — 지시문 외형을 정본 그림 쪽으로 (2026-10-17, S0 뒤 · 사람 결정)

- 사용자 결정 「권장진행」(1안): `{look}`을 카드 층 문구 대신 **정본 그림**(초상 `frozen/<id>.png` + 전신 `lora-sheet-v2/<id>/07.png`) 쪽 서술로 바꾼다. 그림을 보고 손으로 썼다(`params.REF_EDIT_LIGHTNING_LOOK_IMAGE`, `REF_EDIT_LIGHTNING_LOOK_SRC = "image"`). 사울·다윗 모두 장면과 상관없이 같은 서술이다.
  - 사울: 「an ancient Israelite man in his 40s, short dark hair cropped close, short full dark beard, angular face, lean average build, in a plain brown short-sleeved tunic reaching the shins with a brown leather belt」
  - 다윗: 「an ancient Israelite young man in his 20s, thick tight dark curly hair, short full dark beard, rosy cheeks, slender build, in a plain red short-sleeved knee-length tunic with a brown leather belt」
- 카드 층과 달라지는 곳: 사울 체격(통짜 몸통 → 보통·마른)·옷 색(짙은 → 갈색), 다윗 머리(두피에 붙은 곱슬 → 숱 많은 곱슬)·옷 색(짙은 → 붉은). 정의(cast)는 고치지 않는다 — 어긋남은 이번 결과와 함께 기록만 한다.
- 그대로인 것: 지시문 틀·모델·스텝·양자화·되붙임·조작 확인 하한(targeted ≥ 10)·판정 규칙.
- S0을 길갈 사울·엔게디 사울→다윗·라마 다윗(시드 11)으로 다시 한다. 산출 `try-image/`(첫 시도 `try/`는 남김), metrics `try` 항목은 `look_src`로 구분한다.

## S0 다시 — 그림 쪽 서술 (2026-10-17)

q8 `--low-ram`, 시드 11, 산출 `try-image/`.

| 편집 | 장당 | 상자 안 / 밖 | targeted (첫 시도) | 눈으로 |
|---|---|---|---|---|
| 길갈 사울 | 490.5초 | 48.67 / 16.01 | **32.65** (21.94) | 통과 — 짧게 깎은 머리·짧은 수염·마른 체격·갈색 튜닉, 정본 전신 07 차림. 든 손 자세·위치·뒤 군중 유지, 이음매 안 보임, 붓질은 바탕보다 매끈 |
| 엔게디 사울 | 501.1초 | 33.89 / 17.03 | **16.86** (13.0) | 바뀜 |
| 엔게디 다윗 | 494.2초 | 18.91 / 14.47 | **4.44** (−1.49) | **눈으로는 분명히 바뀜** — 짙은 민소매 → 붉은 반소매 튜닉, 풍성한 곱슬, 홍조, 맨발. 자세·칼·망토 자락 유지. 수치가 낮은 것은 몸 상자(386×548)가 어두운 동굴 배경을 크게 품어 인물 변화가 상자 평균에서 묽어진 탓으로 본다 |
| 라마 다윗 | 481.2초 | 28.3 / 13.13 | **15.16** (8.27) | 바뀜 — 선명한 붉은 튜닉·촘촘한 곱슬·홍조, 칼 쥔 자세 유지 |

- 고정 절 S0 관문(첫 장 = 길갈 사울 targeted ≥ 10 + 눈 확인) 통과 → S1로 간다. 조작 확인 지표는 결과를 보고 바꾸지 않는다 — 32장 평균 ≥ 10 관문은 그대로다(엔게디 다윗처럼 상자가 큰 장은 수치가 낮게 나온다는 것을 판정 결과와 함께 적는다).
- 358 판정 페이지 바이트 동일 확인: 옛 코드(HEAD)와 일반화한 코드의 `judge` 출력 HTML·metrics sha256 일치(metrics 임시 사본으로 실행, 358 기록 무변경).

## S1 본 편집 32번 (2026-10-17)

q8 `--low-ram`, 그림 쪽 서술, 32/32 `ok`. 장당 평균 505.8초(약 4.5시간), 피크 58.5GB(적재 스왑 — 편집 중 감시 셸 하나가 메모리 부족으로 Claude Code에 의해 정리됐고 생성 프로세스는 무사).

| 편집 | targeted 8장 | 평균 | 10 미만 |
|---|---|---|---|
| 길갈 사울 | 32.6 · 32.1 · 26.1 · 31.2 · 31.5 · 28.3 · 39.2 · 39.8 | 32.6 | 0 |
| 엔게디 사울 | 16.9 · 12.7 · 14.9 · 10.3 · 5.4 · 2.7 · 17.5 · 17.9 | 12.3 | 2 |
| 엔게디 다윗 | 4.4 · 3.9 · 3.5 · −2.0 · −1.0 · 6.8 · 8.1 · −1.8 | 2.7 | 8 |
| 라마 다윗 | 15.2 · 15.1 · 18.9 · 9.0 · 14.0 · 16.6 · 10.1 · 6.2 | 13.1 | 2 |

(시드 순서 11·42·7·23·5·101·202·303.) **`targeted_mean` 15.19 ≥ 10 → 게시 관문 통과.** 장면별 평균: 길갈 32.61 · 엔게디 7.51 · 라마 13.12. 359식 `mask_diff_mean` 32.93(참고).

- **엔게디 다윗 8장은 눈으로 전부 편집됐다** — 짙은 민소매 → 붉은 반소매 튜닉·풍성한 곱슬·홍조·맨발, 자세·칼·망토 유지. 음수 3장(s23·s5·s303)도 마찬가지다. 몸 상자가 어두운 동굴 배경을 크게 품고 상자 밖 재렌더 잡음이 14~17이라 targeted가 실제 변화를 낮게 잰다. 지표는 고치지 않고 기록만 한다(고정 절).
- 판정 페이지: `make_ref_edit_page.py judge-lightning` → 4.91MB, 화면 6(A-saul·A-david·B-engedi·C-gilgal·C-engedi·C-ramah), 그림 35. 쌍 대응은 게시 전에 metrics `screens`에 적었다. 게시 https://claude.ai/artifact/T8tbVKFxn1iKbr4acqY2SD (비공개).
- 판정 지시 보충(2026-10-17, 사람이 답하기 전 · 사용자 질문 「얼굴 및 몸집만 보나? 색깔도 보나?」에 답함): 화면 A(같은 인물)는 **얼굴·머리·수염·몸집(나이대)만 보고 옷 색깔은 빼고** 판단한다고 페이지 문구에 덧붙여 다시 게시했다(Version 2). 이유: 이번 편집은 옷 색을 정본 쪽으로 통일(다윗 붉은·사울 갈색)했고 대조 바탕은 장면마다 옷이 달라, 색을 보면 처치가 옷 덕분에 이긴다. 정체성 층(카드 층)에 옷 색은 없다. 화면 B·C 문구는 그대로(C는 색감이 화풍의 일부). 생성 코드(`make_ref_edit_page.py`)는 358 출력 바이트 동일 유지를 위해 고치지 않았다.

## 사람 판정 (2026-10-17, 원문)

```
task 360 사람 판정
- [A-saul] 사울 · 두 ▼가 같은 사람으로 읽히는 쌍을 누르세요 → 2, 3, 5, 6, 8, 10
- [A-david] 다윗 · 두 ▼가 같은 사람으로 읽히는 쌍을 누르세요 → 1, 2, 3, 4, 5, 6, 7, 8, 9, 11
- [B-engedi] 엔게디 · 두 ▼ 인물이 서로 닮아 구별이 안 되는 그림을 누르세요 → 없음
- [C-gilgal] 길갈 · 연필 화풍이나 장면 뜻이 기준보다 크게 무너진 그림을 누르세요 → 없음
- [C-engedi] 엔게디 · 연필 화풍이나 장면 뜻이 기준보다 크게 무너진 그림을 누르세요 → 1, 2, 3, 4, 5, 6, 8, 9, 10, 11
- [C-ramah] 라마 · 연필 화풍이나 장면 뜻이 기준보다 크게 무너진 그림을 누르세요 → 없음
(보여 준 그림: qwen-image-edit-2511 + Lightning 4스텝 참조 편집 · q8 · 외형 명시 지시문 · 전체 편집 → 몸 상자 되붙임 · 시드 [11, 42, 7, 23, 5, 101, 202, 303] · 카드 폭 356px · 기계 거르기 없음)
```

metrics `screens`(게시 전 기록)로 푼 결과:

| 화면 | 처치 | 대조 |
|---|---|---|
| A-saul 「같은 사람」 | **6/8** (s5·7·11·42·101·202, 빠짐 s23·303) | 0/3 |
| A-david 「같은 사람」 | **8/8** | 2/3 (s11·42) |
| B-engedi 「구별 안 됨」 | 0/8 | — |
| C-gilgal 「무너짐」 | 0/8 | 0/3 |
| C-engedi 「무너짐」 | **8/8** | 2/3 (s7·42) |
| C-ramah 「무너짐」 | 0/8 | 0/3 |

- 분해능: 대조 「같은 사람」 2/6 ≤ 2/6 → 충족(한계값).
- 채택 조건: 사울 6/8 · 다윗 8/8 모두 ≥ 5/8.
- 화풍 감점: 처치 무너짐 8/24 = 0.333 − 대조 2/9 = 0.222 → 0.111 ≤ 0.5 → 내리지 않음.
- targeted 평균 15.19(길갈 32.61 · 엔게디 7.51 · 라마 13.12).
- 남는 점:
  - **엔게디는 처치 8/8이 무너짐**이다(대조 2/3 — 358처럼 353 장면 문구 쪽 문제가 있고, 편집으로 더 나빠졌다).
  - **다윗 대조가 2/3**이라 8/8에 바탕끼리 비슷했던 몫이 섞여 있다.
  - 판정은 옷 색을 빼고 했다.

결론: 채택 — 사울 6/8 · 다윗 8/8 · 대조 2/6 · 화풍 감점 0.11(엔게디 처치 8/8 무너짐은 남는 위험) · ADR `261017-152627`이 `260904-055320`을 뒤집음 · 영상 패키지 사용: 가능(apache-2.0 — 2511·Lightning LoRA)
