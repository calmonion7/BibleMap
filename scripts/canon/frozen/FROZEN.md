# S1 — 얼굴 동결 (다윗 seed 11 · 골리앗 seed 42)

> **2026-09-04(task 331) 이후 정본은 아래 「판 경로」 항목들이다**(ADR `260904-055320`, `cast/<id>.json`의 `plate`와 짝). 이 머리 절의 david·goliath는
> 콘티 시절 구본 — `frozen/david.png`는 판 경로 david-boy(seed 11)로 교체됐고, `frozen/goliath.png`는 판 경로에서 **보류**(문구 3종 상한, 비늘갑 미출현)라
> 콘티 경로 스크립트(`judge_s1.py`·`judge_metrics.py`) 호환용으로만 남긴다. 판 경로 정본이 아니다.

## 크롭 공식

머리 중심의 분수 좌표 = `(0.5, top_margin/(top_margin+bottom_margin))` = `(0.5, 1.1/1.85)` ≈
`(0.5, 0.594595)` — `cond-meta.json`의 `top_margin`·`bottom_margin`에서 파생(D가 약분되어 다윗·골리앗이
같은 값을 공유). 이 프레임(`half_width=D`, `top=1.1D`, `bottom=0.75D`, 폭 `2D`×높이 `1.85D`)은
`cond_shoot_heads.py`의 클립 정의 그 자체이고, `prep_cond.py`는 이를 단순 리사이즈(레터박스 없음)해
`cond-*-ctrl.png` 1024×1024를 만들며, `gen_candidates.py`는 그 1024×1024를 같은 크기로 ControlNet에
먹여 `gen/*.png`를 픽셀 1:1로 생성한다. 즉 **gen 캔버스 전체가 이미 파생된 프레임이다** — 그보다 타이트한
크롭은 `cond-meta.json`에 없는 임의 배율이 되어 금지 사항("손으로 찍지 말 것")을 어긴다. 따라서 크롭
박스는 `(0, 0, 1024, 1024)`(캔버스 전체)이고, 머리 중심은 이미 그 분수 좌표에 와 있다.
재현 스크립트: `.forge/reports/canon-pilot/freeze_faces.py`.

## 선택 근거 — 5축 대조 (`cast/*.jsx`의 `AXES`)

### 다윗 seed 11 (`gen/david-s11.png` → `frozen/david.png`)

- `hair: 곱슬머리` — 정수리에 3봉우리 곱슬 텍스처가 실제로 촘촘히 나온다. 축값을 나른다.
- `beard: 없음` — 턱·볼에 수염선이 없고 매끈한 소년 피부로 그려졌다. 축값을 나른다.
- `headwear: 없음` — 투구·두건 없이 맨머리 곱슬만 있다. 축값을 나른다.
- `age: 소년/청년` — 4장 중 얼굴이 가장 마르고 골격(눈두덩·광대)이 읽히며 정면이라, S2에서 나이
  프롬프트를 얹기 유리하다(그릴링 Q4 결정 근거). 축값을 나른다.
- `sex: 남` — 눈썹·턱선이 소년 남성으로 그려졌다. 축값을 나른다.

### 골리앗 seed 42 (`gen/goliath-s42.png` → `frozen/goliath.png`)

- `hair: 없음` — 투구에 덮여 있으나 노출된 이마·구레나룻 자리에 머리카락이 그려지지 않았다.
  축값과 모순되지 않는다.
- `beard: 없음` — 턱·볼이 매끈하고 수염선이 없다. 축값을 나른다.
- `headwear: 투구` — 골리앗은 삼상 17장 1회 등장이라 생애 축이 없고, 4장 중 면갑·문양 없이
  투구와 얼굴이 온전히 함께 나온 유일한 후보다(그릴링 Q4 결정 근거). 축값을 가장 강하게 나른다.
- `age: 성인` — 굵은 턱선과 미간 주름이 성인 인상으로 그려졌다. 축값을 나른다.
- `sex: 남` — 각진 턱·짙은 눈썹이 성인 남성으로 그려졌다. 축값을 나른다.

## 눈 검증

두 크롭 모두 Read 도구로 열어 확인 — 다윗은 눈·코·입·양 귀·곱슬 전체가 프레임 안에 온전하고(정수리
잔머리 몇 가닥이 상단 여백 끝에 닿을 뿐 지장 없음), 골리앗은 투구·눈썹·눈·코·입·턱선이 상하좌우
여백과 함께 온전하다. 잘림 없음 — 공식 재조정 불필요.

### abner seed 11 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/abner/a-P1-s11.png` 머리 크롭(몸 bbox 위 20%) → `frozen/abner.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### absalom seed 11 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/absalom/a-P1-s11.png` 머리 크롭(몸 bbox 위 20%) → `frozen/absalom.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### achish seed 5 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/achish/a-P1-s5.png` 머리 크롭(몸 bbox 위 20%) → `frozen/achish.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### agag seed 11 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/agag/a-P1-s11.png` 머리 크롭(몸 bbox 위 20%) → `frozen/agag.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### ahimelech seed 5 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/ahimelech/a-P1-s5.png` 머리 크롭(몸 bbox 위 20%) → `frozen/ahimelech.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### bathsheba seed 42 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/bathsheba/a-P1-s42.png` 머리 크롭(몸 bbox 위 20%) → `frozen/bathsheba.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### david seed 42 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/david/a-P1-s42.png` 머리 크롭(몸 bbox 위 20%) → `frozen/david.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### david-boy seed 11 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/david-boy/a-P1-s11.png` 머리 크롭(몸 bbox 위 20%) → `frozen/david-boy.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### david-old seed 42 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/david-old/a-P1-s42.png` 머리 크롭(몸 bbox 위 20%) → `frozen/david-old.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### doeg seed 11 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/doeg/a-P1-s11.png` 머리 크롭(몸 bbox 위 20%) → `frozen/doeg.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### endor-medium seed 11 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/endor-medium/a-P1-s11.png` 머리 크롭(몸 bbox 위 20%) → `frozen/endor-medium.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### hiram seed 42 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/hiram/a-P1-s42.png` 머리 크롭(몸 bbox 위 20%) → `frozen/hiram.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### jesse seed 11 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/jesse/a-P1-s11.png` 머리 크롭(몸 bbox 위 20%) → `frozen/jesse.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### nahash seed 11 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/nahash/a-P1-s11.png` 머리 크롭(몸 bbox 위 20%) → `frozen/nahash.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### nathan seed 11 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/nathan/a-P1-s11.png` 머리 크롭(몸 bbox 위 20%) → `frozen/nathan.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### samuel seed 11 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/samuel/a-P1-s11.png` 머리 크롭(몸 bbox 위 20%) → `frozen/samuel.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### saul seed 11 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/saul/a-P1-s11.png` 머리 크롭(몸 bbox 위 20%) → `frozen/saul.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### saul-armor-bearer seed 11 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/saul-armor-bearer/a-P1-s11.png` 머리 크롭(몸 bbox 위 20%) → `frozen/saul-armor-bearer.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### saul-old seed 11 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/saul-old/a-P1-s11.png` 머리 크롭(몸 bbox 위 20%) → `frozen/saul-old.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### solomon seed 42 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/solomon/a-P1-s42.png` 머리 크롭(몸 bbox 위 20%) → `frozen/solomon.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### solomon-old seed 11 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/solomon-old/a-P1-s11.png` 머리 크롭(몸 bbox 위 20%) → `frozen/solomon-old.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 2차, 2026-09-04)

### jonathan seed 11 · 앵커 켬 0.25 · 문구 b (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/jonathan/b-P1-s11.png` 머리 크롭(몸 bbox 위 20%) → `frozen/jonathan.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 3차, 2026-09-04)

### joab seed 23 · 앵커 켬 0.25 · 문구 b (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/joab/b-P1-s23.png` 머리 크롭(몸 bbox 위 20%) → `frozen/joab.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 3차, 2026-09-04)

### sheba-queen seed 11 · 앵커 켬 0.25 · 문구 b (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/sheba-queen/b-P1-s11.png` 머리 크롭(몸 bbox 위 20%) → `frozen/sheba-queen.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 3차, 2026-09-04)

### mother-a seed 11 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/mother-a/a-P1-s11.png` 머리 크롭(몸 bbox 위 20%) → `frozen/mother-a.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 3차, 2026-09-04)

### mother-b seed 11 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/mother-b/a-P1-s11.png` 머리 크롭(몸 bbox 위 20%) → `frozen/mother-b.png`
- 선택 근거(사람 육안): 사용자 육안 판정(폰 판정 페이지 3차, 2026-09-04)

### zadok seed 11 · 앵커 켬 0.25 · 문구 a (2026-09-04, 판 경로 · ADR 260904-055320)

- 출처 `cast/zadok/a-P1-s11.png` 머리 크롭(몸 bbox 위 20%) → `frozen/zadok.png`
- 선택 근거(사람 육안): 사용자 육안 판정(장면 검토 페이지, 2026-09-04)

### saul seed 7 · Z-Image-Turbo Q8 · 정면 머리 초상 768×768 (2026-10-14, task#346 S1 — SDXL 정본 폐기, 옛 판은 `retired-sdxl/saul.png`)

- 출처 `gen_face_canon.py` 후보 8장(시드 11·42·7·23·5·101·202·303, 레포 밖 `~/.local/biblemap-imggen/face-canon/saul/`) → `frozen/saul.png`
- 선택 근거(VLM `claude -p`, `judge_face_canon.py`): 어휘 부합·화풍·깨끗함·머리 4항목 평균 9.0(후보 8장 중 최고, 범위 8.25~9.0). 풍성한 직모 검은 머리·짧은 검은 수염·각진 턱의 장년으로 정본(`dark hair`·`short dark beard`)과 맞고, 상위 3×3 쌍 판정에서 다윗 s11과 구별 9/10(직모 vs 곱슬·수염 밀도·나이대).
- 프롬프트 교훈: 「bare head」·「graying temples」는 정수리 대머리를 만들었다(v1·v2 각 8장 전부) — 「hair covering the whole head」로 바꾸자 전부 풍성한 머리.

### david seed 11 · Z-Image-Turbo Q8 · 정면 머리 초상 768×768 (2026-10-14, task#346 S1 — SDXL 정본 폐기, 옛 판은 `retired-sdxl/david.png`)

- 출처 `gen_face_canon.py` 후보 8장(같은 시드, `~/.local/biblemap-imggen/face-canon/david/`) → `frozen/david.png`
- 선택 근거(VLM): 4항목 평균 9.25(후보 8장 중 단독 최고, 나머지 9.0). 조밀한 검은 곱슬머리·성긴 짧은 수염·갸름한 청년 얼굴로 정본(`dark curly hair`·`short dark beard`·`lean young man`)과 맞고, 사울 s7과 구별 9/10.

### samuel seed 11 · Z-Image-Turbo Q8 · 정면 머리 초상 768×768 (2026-10-15, task#348 S1 — SDXL 정본 폐기, 옛 판은 `retired-sdxl/samuel.png`)

- 출처 `gen_face_canon.py --who samuel` 후보 8장(같은 시드, `~/.local/biblemap-imggen/face-canon/samuel/`) → `frozen/samuel.png`
- 선택 근거(VLM, `judge_face_canon.py --who samuel`): 4항목 평균 9.38(후보 8장 중 단독 최고, 범위 8.75~9.38). 흰 장발이 머리를 덮고 가슴까지 오는 흰 수염, 깊은 주름의 야윈 노인으로 정본(`old prophet`·`white hair`·`long white beard`·`thin`)과 맞다. 상위 3장 중 확정된 사울 정본과 가장 구별되는 1장으로도 뽑혔다(나이·머리·수염 색).
- 사람 확인은 task#348 판정 페이지 문항 ⓪에서 한다(중간 사람 관문 없음).

### saul · david · samuel seed 11 · Z-Image-Turbo Q8 · 정면 머리 초상 768×768 (2026-10-16, task#353 S3 — 정의 파생 정본, 옛 판은 `retired-v1/<id>.png`)

- 출처 `gen_cast_v2_pilot.py` → `gen_face_canon.prompt(id, view)`(cast-vocab-2 카드·얼굴 층에서만 파생, 인물별 `LOOK` 상수 없음) 후보 인물당 8시드 × 정면·3/4(레포 밖 `~/.local/biblemap-imggen/cast-v2-pilot/face/<id>/`) → 정면 `s11-front.png`를 `frozen/<id>.png`로. 3/4는 같은 시드·`view="34"`로 재현된다.
- 선택 근거(사람): task#353 판정 페이지 https://claude.ai/artifact/65nvPyVBZYynBCsd8tuSBe 정본 3문항에 사용자는 시드를 고르지 않고 「별차이 없어보인다」고 답했다(후보 8개가 서로 구별되지 않음 — 「없음」(정의 불일치)과 다름). 그래서 기본값으로 첫 시드 11을 썼다. 기록 `notes/CAST-V2-PILOT.md`.
- 프롬프트 교훈(346 교훈의 재발): 카드 층 머리 윤곽 text의 `bare head`(머리쓰개 없음)가 다시 민머리를 만들었다(사울 16/16). 이제 `derive_scene.head_text`가 그 낱말을 떼고 「hair covering the whole head, no headwear」를 붙인다 — 정본·장면 공통.
- 주의: 같은 정의로 그린 장면 사이 같은 인물 판정은 1/9였다. 이 정본은 「정의와 맞는 머리 초상」일 뿐, 장면에서의 같은 인물감은 아직 보장하지 않는다.
