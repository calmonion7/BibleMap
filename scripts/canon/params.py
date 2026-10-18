"""[[생성 파라미터]] 정본 — 저작 파이프라인 13종이 읽는 유일한 선언처(task#316).

이 파일 **밖**에서 여기 선언된 이름을 모듈 레벨로 다시 대입하면
`backend/scripts/validate_canon_pipeline.py`가 배포를 막는다. 값을 바꾸려면 여기서만 바꾼다.
근거는 ADR `260823-221839` — 기계로 강제하지 않는 규약 수치는 참조본에서 드리프트한다.
실제로 이 파일이 생기기 전 `CN_MODEL`·`SDXL_BASE`는 각 6곳, `SCENE_CN`·`STEPS`·`GUIDANCE`는
각 3곳에 리터럴로 복사돼 있었다.

**조건 종류별로 갈라 둔다**(ADR `260824-191250` — 파생은 아무것도 승계하지 않는다).
인물 두상과 장면 콘티는 조건 입력의 선 밀도가 달라 ControlNet 강도와 해상도가 함께 갈린다.
`COND`로 묶어 두되 각 값은 아래에 최상위 이름으로도 선언한다 — 게이트가 **이름 집합**으로
판정하기 때문에, 딕셔너리 안에만 있으면 다른 파일의 재선언을 막지 못한다.

이 파이프라인은 앱과 다른 런타임에서 돈다(ADR `260825-065028`) — 앱(backend/frontend)은 이 파일을
import하지 않는다. **재현은 아직 닫히지 않았다**: 미결 3축은 `requirements.txt` 머리 주석을 보라.
"""
import os

# --- 위치 -------------------------------------------------------------------
# `_HERE`는 이 파일의 내부 사정이라 사적 이름으로 둔다 — 게이트는 `_` 시작 이름을 정본 키로 보지
# 않으므로, 다른 스크립트가 자기 `HERE`를 갖는 것은 재선언이 아니다.
_HERE = os.path.dirname(os.path.abspath(__file__))
CANON_DIR = _HERE
REPO_ROOT = os.path.dirname(os.path.dirname(_HERE))   # scripts/canon → scripts → BibleMap
NOTES = os.path.join(_HERE, "notes")                  # 판단 문서 14 + meta json 12 (추적)
FROZEN = os.path.join(_HERE, "frozen")                # 동결 얼굴 2장 (추적) — 장면 생성의 정체성 입력
# 정답지(추적) — [[화풍 도달]] 판정의 양성 기준 10장. 사용자가 목표로 지정한 그림이라
# 지어내지 않으며, 축 A의 임계는 이 집합에서 파생한다(reference/REFERENCE.md).
REFERENCE = os.path.join(_HERE, "reference")
PROMPTS_JSON = os.path.join(NOTES, "prompts.json")    # derive_prompts.py가 쓰고 생성기 4종이 읽는다

# 산출물 루트. 스크립트를 추적 위치로 옮긴 뒤에도 **산출물 54MB는 따라오지 않는다**는 것이
# 이 한 줄의 요점이다 — `.gitignore`의 `.forge/reports/`가 계속 덮는다.
OUT_ROOT = os.path.join(REPO_ROOT, ".forge", "reports", "canon-pilot")

# --- 모델 -------------------------------------------------------------------
# 스크리블 ControlNet — 잉크 선화를 그대로 조건 입력으로 받는다(task#308이 고른 것).
CN_MODEL = "xinsir/controlnet-scribble-sdxl-1.0"
# 이름이 `BASE`가 **아닌** 이유: `cond_shoot_heads.py`의 `BASE`는 로컬 개발 서버 URL이라
# 이름이 겹친다. 정본 키가 `BASE`였다면 게이트가 그 무관한 줄을 재선언으로 오탐한다.
SDXL_BASE = "stabilityai/stable-diffusion-xl-base-1.0"
IP_ADAPTER_REPO = "h94/IP-Adapter"
IP_ADAPTER_SUBFOLDER = "sdxl_models"
IP_ADAPTER_WEIGHT = "ip-adapter_sdxl.bin"
# `judge_metrics.py`가 쓰는 CLIP 이미지 인코더(ViT-bigG). 파이프라인에서 **유일하게 리비전이
# 박힌 자리**지만 머신 로컬 캐시의 절대경로라 다른 머신에서는 성립하지 않는다 — 재현 미결 축의
# 하나이자, 「고정했다」로 읽으면 안 되는 자리다(ADR `260822-220823`).
IMAGE_ENCODER = (
    "/Users/calmonion/.cache/huggingface/hub/models--h94--IP-Adapter/"
    "snapshots/018e402774aeeddd60609b4ecdb7e298259dc729/sdxl_models/image_encoder"
)

# --- 샘플링 (조건 종류와 무관하게 공유) --------------------------------------
STEPS = 30        # task#308 관례 승계 — 비교 가능성 때문에 유지한다(바꾸면 앞선 실측과 못 잇는다).
GUIDANCE = 6.5    # 같은 이유로 승계. 화풍 블록이 세서 이 이상 올리면 채도가 튄다.

# --- 조건 종류별로 갈리는 값 --------------------------------------------------
# 강도는 **조건 입력의 선 밀도에 따라 다르다** — 두상 조건은 stroke 4~8개뿐이라 0.8이면
# "이 그림은 이 선이 전부"가 되어 모델이 얼굴 안을 비운다(사용자 UAT 2026-08-24 실패의 지배적
# 원인, sweep_cause.py 실측: 같은 프롬프트로 cn 0.8 빈 타원 / cn 0.5 얼굴). 장면 조건은 189선이라
# task#308이 검증한 0.8을 그대로 둔다 — 두 값을 하나로 묶으면 그 실측이 끊긴다.
PERSON_CN = 0.3   # 얇은 조건 입력(THIN_SW) 기준 확인값 — probe_cn.py: 0.5는 아직 유아기 둥근 얼굴,
                  # 0.3에서 곱슬·마른 얼굴의 열두 살 소년이 나온다(notes/SWEEP.md 참조).
SCENE_CN = 0.8    # ADR `260824-191250` — 장면 콘티(189선) 조건 입력용 고정값.
# 두상 크롭은 1024 정사각(원본 종횡비 ~1.08, 소폭 압축 허용), 장면은 task#308 관례를 그대로 잇는다.
PERSON_SIZE = (1024, 1024)
SCENE_SIZE = (1216, 640)
# 전신 표본(part2) 전용 캔버스 — **세로**다. 2026-08-26 실측: 가로 SCENE_SIZE로 단독 전신을
# 뽑으면 세로로 선 사람이 640 높이에 안 들어가 모델이 장면을 구성해 버린다(정강이에서 잘린
# 3/4 측면 + 언덕·풀밭 배경). PERSON_SIZE(1024 정사각)를 쓰지 않고 새 값을 둔 이유는
# PERSON_SIZE가 머리 인페인팅용 기존 상수이고 그것을 바꾸면 앞선 실측과 못 잇기 때문이다.
# 832x1216은 SDXL 표준 종횡비 버킷이다.
SAMPLE_SIZE = (832, 1216)
IP_SCALE = 0.3         # S2가 정한 값(gen_sweep_scale_age.py 판정).
IP_SCALES = [0.3, 0.5, 0.7]  # 스윕 2종이 함께 쓰는 후보 범위 — 두 곳에 복사돼 있던 값이다.
# 조건 입력 전용 균일 선 굵기(viewBox 단위). 머리 8단위 대비 ~1.9%로, 1024px 산출에서 약 9px.
# 원본 구조 선 2.6단위(머리의 32%)를 그대로 키우면 실루엣이 뭉개진다(회고 1of2 §3의 지배 원인).
# ControlNet을 **몇 스텝까지** 걸 것인가(0~1, 1.0 = 전 스텝). `diffusers 0.40.0`의
# StableDiffusionXLControlNetPipeline이 `control_guidance_start/end`로 받는데 task#316까지의
# 생성기는 넘기지 않아 줄곧 기본값 1.0으로 돌았다 — 즉 현행 값이지 고른 값이 아니었다.
# 뒤쪽 스텝에서 CN을 놓으면 구도는 잡히고 화풍은 모델이 마무리한다는 것이 task#317 S1의 가설.
CONTROL_END = 1.0
CONTROL_ENDS = [0.3, 0.5, 0.7, 1.0]  # S1 스윕 후보 — 마지막이 현행(기준선)
THIN_SW = 0.15
# 잉크/배경 이진화 임계(0~255). 좌상단 코너를 배경으로 보고 |a-bg| > THRESHOLD를 잉크로 본다.
# `prep_cond.py`와 `make_masks.py`가 **같은 임계·같은 극성**을 써야 마스크가 조건 입력과 어긋나지 않는다.
THRESHOLD = 60

# 조건 종류별 묶음. 위 이름들에서 조립한다 — 여기서 리터럴을 다시 적으면 그 자체가 드리프트다.
COND = {
    "person_head": {"cn_scale": PERSON_CN, "size": PERSON_SIZE, "ip_scale": IP_SCALE},
    "scene_conti": {"cn_scale": SCENE_CN, "size": SCENE_SIZE, "ip_scale": IP_SCALE},
}

# --- 시드 -------------------------------------------------------------------
# 스윕류가 축을 섞지 않으려고 고정하는 단일 시드. 다윗 동결본(gen/david-s11.png)·bg-on/bg-off와 같다.
SEED_FIXED = 11
BG_SEED = 11                    # 배경 후보 1장 — 위와 같은 시드를 쓴다(축을 섞지 않는다).
PERSON_SEEDS = [11, 42, 7, 23]  # 인물 후보 4장.
SCENE_SEEDS = [11, 42, 7]       # 장면 4조건 × 3시드 — PERSON_SEEDS 관례에서 3개.
FACE_CANON_SIZE = (768, 768)    # task#346 S1 — Z-Image 얼굴 정본 후보(정사각 정면 머리, 옛 frozen과 같은 비율).
FACE_CANON_SEEDS = [11, 42, 7, 23, 5, 101, 202, 303]   # 인물당 후보 8장.

# --- 얼굴 닮음 자(check_face_scale.py)·판정자 교정(check_face_judge.py) — task#346 S2, 실행 전 고정 ---
FACE_SCALE_SIZES = [256, 128, 64]       # 같은 그림의 머리 크롭을 이 한 변(px)으로 줄여 넣는 척도 검사(a) — 32는 CLIP이 무너지는 영역이라 제외(실측 풀 얼굴 최소 139px)
FACE_SCALE_DEGRADE_MAX_PX = 128         # 열화 해상도 상한: 이보다 큰 얼굴은 정본·후보 모두 128로 맞춰 큰 얼굴 우대를 없앤다
FACE_SCALE_SPREAD_MAX = 0.05            # (a) 크기를 바꿨을 때 점수 최대-최소 허용 폭
FACE_SCALE_CORR_MAX = 0.5               # (b) 후보 풀에서 log(얼굴 크기)–점수 상관 |r| 허용 상한
FACE_SCALE_POOL_MIN = 8                 # (b) 검출 성공 후보가 이보다 적으면 검사 불성립(실패)
FACE_SCALE_HEAD_MARGIN = 0.15           # 머리 상자 사방 여유 비율(정본·후보 같은 비율)
FACE_JUDGE_REJECT_MIN = 0.9             # 다른 인물 쌍 중 기각돼야 하는 비율 하한
FACE_JUDGE_ACCEPT_MIN = 0.9             # 정본 변형 쌍 중 통과해야 하는 비율 하한

# --- A 갈래 다각도 시트(gen_face_sheet.py·select_face_sheet.py) — task#346 S3 ---
FACE_SHEET_SEED0 = 1000         # 시트 시드 시작값(정본 시드와 겹치지 않게)
FACE_SHEET_SIZES = {"close": (768, 768), "half": (768, 768), "full": (640, 896)}   # 구도별 생성 크기
FACE_SHEET_STAGE1 = 20          # 1차(CLIP 마진) 통과 장수
FACE_SHEET_STAGE2 = 12          # 2차(VLM 같은 사람) 최종 장수 상한(10~15)

# --- task#346 S5 — A/B 얼굴 유지 비교
FACE_AB_SEEDS = [42, 23]         # 비교 시드(345 시드 [11,42,7,23] 중 승인 시드 11·7을 뺀 둘 — 승인 그림과 같은 그림이 (f)에서 재생성되지 않게)
FACE_AB_CROP_SCALE = 2.6         # A 인페인트: 머리 상자 한 변의 이 배수를 정사각 크롭해 768로 올려 그린다
FACE_AB_INPAINT_STRENGTH = 0.85  # A 인페인트 강도(1.0이면 원본 무시, 낮을수록 원래 얼굴 구조가 남는다)
FACE_AB_MASK_GROW = 1.15         # A 마스크(머리 상자 타원)의 확장 배율
FACE_AB_MASK_FEATHER = 0.12      # A 마스크 가장자리 번짐(마스크 한 변 대비)

# --- task#347 — B-e 얼굴을 지키며 화풍 되찾기(R1 머리 되붙이기 · R2 저강도 img2img). 실행 전 고정 ---
FACE_STYLE_SETTINGS = {"R1": [1.3, 1.6], "R2": [0.25, 0.4]}   # R1 = 머리 상자 타원 확장 배율, R2 = img2img 강도
FACE_STYLE_R1_FEATHER = 0.12     # R1 타원 마스크 번짐(마스크 한 변 대비 — A와 같은 값)
FACE_STYLE_REGION_SCALE = 2.0    # 화풍 측정 영역 ①: 머리 상자 중심, 한 변 2배 상자(머리 포함). ② 그림 전체
FACE_STYLE_METRICS = ("sat_p95", "val_p05", "ink")   # judge_style.style_metrics — 화풍 거리 = 두 영역 × 세 지표 절대차 평균
FACE_STYLE_UNIT = "head"         # 집계 단위: 그림이 아니라 머리 하나(장면·시드·인물)
FACE_STYLE_DIST_MAX_RATIO = 0.5  # 통과 ①: 화풍 거리가 같은 장면·시드·인물 B-e 원본 거리의 이 배 이하
FACE_STYLE_FACE_MIN_RATIO = 0.8  # 통과 ②: 얼굴 마진 점수(346 S2 자)가 B-e 원본 점수의 이 배 이상
FACE_STYLE_REQUIRE_SAME = True   # 통과 ③: VLM(check_face_judge.same_person)이 정본과 같은 사람이라 한다

# task#348 — 조건부 R1(머리 되붙이기)을 새 장면(골리앗)·새 인물(사무엘)로 넓히기. 실행 전 고정. 347 FACE_STYLE_*는 건드리지 않는다.
FACE_WIDEN_SCENES = {"goliath": ("authored-david-goliath-gath", ["david"]),
                     "gilgal": ("authored-saul-gilgal-coronation", ["saul", "samuel"])}   # 장면 → (승인 장면 id, 되붙일 인물)
FACE_WIDEN_SEEDS = [42, 23]       # klein 시드 — 347과 같은 둘
FACE_WIDEN_R1_GROW = 1.6          # R1 확장 배율(347 채택값). 깃털·LAB 맞춤은 FACE_STYLE_R1_FEATHER·gen_face_style 그대로
# 기계 자(화풍 거리·얼굴 마진·VLM 같은 사람)는 347 FACE_STYLE_* 정의 그대로 재고, 통과 판정은 「참고」로만 적는다 — 머리 판정은 사람.

# task#349 — klein 얼굴 적중률(참조 1명 대 2명, 머리당 시드 8) + 화질(결) 측정. 실행 전 고정. 347·348 FACE_STYLE_*·FACE_WIDEN_*는 건드리지 않는다.
FACE_HITRATE_SCENES = {"gilgal": ["saul", "samuel"], "engedi": ["david", "saul"]}   # 장면 → 머리(나이 문제 없는 두 승인본, 골리앗 다윗 제외)
FACE_HITRATE_SEEDS = [42, 23, 5, 101, 202, 303, 404, 505]   # 머리당 klein 시드 8
FACE_HITRATE_CONDS = ("K1", "K2")   # K1 = 그 인물 정본 하나만 참조·그 얼굴만 / K2 = 두 정본 다 참조·두 얼굴 다(348 방식). 같은 장면·같은 시드
FACE_HITRATE_LAP_RATIO_MAX = 1.5    # 화질 자: 머리 상자 회색조 라플라시안 분산 「대상 ÷ 승인본 같은 머리」 > 이 값이면 「거칠다」고 예측
FACE_HITRATE_R1_SEEDS = [42, 23]    # 화질 표본: K2 이 시드들의 R1 되붙이기(확장 FACE_WIDEN_R1_GROW, 깃털·LAB 347 그대로) 4장 = 머리 8

# task#356 — 인물 LoRA 학습 시트(정본 초상 + 전신 단독). 생성 전 고정. 353 FACE_CANON_*·cast-v2-pilot 산출은 건드리지 않는다.
LORA_SHEET_WHO = ("saul", "david", "samuel")
LORA_SHEET_TRIGGER = {"saul": "saul_bm", "david": "david_bm", "samuel": "samuel_bm"}   # 캡션 첫 낱말(정체성은 이 낱말에 묶는다)
LORA_SHEET_PORTRAIT_SEEDS = [11, 42, 7]     # 353 cast-v2-pilot/face/<id>/s<시드>-<front|34>.png 재사용(시드 11이 정본) → 인물당 6장
LORA_SHEET_BODY_SEEDS = [11, 42, 7, 23, 5, 101, 202, 303]   # 전신 시드 8(= FACE_CANON_SEEDS 값)
LORA_SHEET_POSES = {"stand": "standing still, full front view", "walk": "walking, three-quarter side view"}   # 자세 2묶음 × 시드 8 = 전신 16
LORA_SHEET_BODY_SIZE = (768, 1152)          # 전신 세로 캔버스(Z-Image-Turbo Q8)
LORA_SHEET_BODY_MIN = 8                     # 사람 거르기 뒤 남은 전신이 이보다 적으면 기록(이번엔 다시 그리지 않음)
LORA_SHEET_BODY_MAX = 10                    # 남은 전신 중 시드 순으로 이 장수까지 시트에 쓴다
# task#356 수리 r1(사용자 결정 「2」) — 문구 전신의 만화체 얼굴 위에 정본 초상 머리를 되붙인다(347 R1 기법). 결과는 사람이 다시 거른다.
LORA_SHEET_PASTE_WHO = ("saul", "david")
LORA_SHEET_PASTE_POSE = "stand"                 # 정면 서기만(정본 정면 머리와 방향이 같다). 걷기는 고개 방향이 갈려 뺀다
LORA_SHEET_PASTE_CANON_SEEDS = [11, 42, 7]      # 붙일 정본 정면 머리 — 전신 시드 순서대로 돌려 쓴다
LORA_SHEET_PASTE_GROW = 1.0                     # 머리 상자(얼굴 상자 × face_ab_heads.GROW) 배율 — 1.6이면 정본 어깨까지 덮는다
# task#356 수리 r2 — r1에서 남은 것은 바탕 전신의 머리가 작은 것뿐이었다 → 바탕부터 사실 비율로 다시 그려 같은 방식으로 되붙인다.
# 시험 1장(인물당 s404)에서 비율 낱말 「realistic adult proportions, small head, head about one eighth of body height」은
# 머리를 줄이지 못했다(사울 배율 0.455 — 더 큼, 다윗 0.394) → 낱말은 빼고 기존 문구 그대로 시드를 늘린다(r1 남음률 사울 3/8·다윗 1/8).
LORA_SHEET_R2_PROP = ""
LORA_SHEET_R2_SEEDS = {"saul": [404, 505, 606, 707, 808, 909, 1001, 1102],
                       "david": [404, 505, 606, 707, 808, 909, 1001, 1102] + [1200 + 7 * i for i in range(24)]}

# task#357 — 인물 LoRA 2/2: 356 시트로 LoRA 학습 → 353 세 장면을 LoRA 걸고 다시 그려 카드 크기 같은 인물 판정. 학습·생성 전 고정.
LORA_SCENE_WHO = ("saul", "david", "samuel")
LORA_SCENE_SCALE = 1.0          # 추론 세기 한 값(ADR 260904-055320 「한 값으로 시험」)
LORA_SCENE_TRAIN_STEP = 300     # 346 설정의 300스텝 — 학습 설정(25에폭)은 그대로라 13~14장이면 300을 넘겨 돌고, 300 체크포인트 어댑터를 쓴다
LORA_SCENE_SEEDS = [11, 42, 7, 23, 5, 101, 202, 303]   # = FACE_CANON_SEEDS
LORA_SCENE_SCENES = {"gilgal": ("authored-saul-gilgal-coronation", ["saul", "samuel"]),
                     "engedi": ("authored-david-en-gedi-saul", ["david", "saul"]),
                     "ramah": ("authored-david-ramah-samuel", ["david", "samuel"])}   # 장면 → (명세 id, 정본 인물 2)
LORA_SCENE_PAIRS = {"saul": ("gilgal", "engedi"), "david": ("engedi", "ramah"), "samuel": ("gilgal", "ramah")}   # 353과 같은 짝
LORA_SCENE_CONTROL_SEEDS = [11, 42, 7]   # 음성 대조 = 353 cast-v2-pilot/scene/<장면>/s<시드>.png 같은 시드끼리 쌍(인물마다 3, 합 9)
LORA_SCENE_SHUFFLE_SEED = 357            # 화면 A 쌍 순서 섞기(대조 위치를 숨김)
LORA_SCENE_ADOPT_MIN = 5                 # 채택: L1 인물마다 「읽힌다」 ≥ 5/8, 3명 모두
LORA_SCENE_CONTROL_MAX = 3               # 분해능: 음성 대조 「읽힌다」 합 ≤ 3/9 (넘으면 보류)

# task#358 — 정본 참조 편집: 353 바탕 위에서 처치 인물의 몸 상자를 마스크로 잡고 정본 참조 2장으로 편집(mflux Qwen edit). 편집 전 고정.
REF_EDIT_WHO = ("saul", "david")
REF_EDIT_SCENES = {"gilgal": ["saul"], "engedi": ["saul", "david"], "ramah": ["david"]}   # 장면 → 처치 인물(엔게디는 사울 → 다윗 차례)
REF_EDIT_SEEDS = LORA_SCENE_SEEDS                 # 판정 시드 8 — 11·42·7은 353 바탕 그대로, 나머지 5는 같은 설정으로 새로
REF_EDIT_PREVIEW_SEEDS = [404, 505]               # 세기 미리보기 시드(판정 시드와 안 겹침) — 길갈 사울만
REF_EDIT_MODELS = [("qwen-image-2.1", "mflux-generate-qwen-2.1-edit", 8),     # 1순위(q8, --low-ram)
                   ("qwen-image-edit-2511", "mflux-generate-qwen-edit", 4)]   # 2순위(낮은 양자화) — 1순위가 「안 돔」일 때만
REF_EDIT_REF_FULL = {"saul": "07", "david": "07"}  # 356 시트 lora-sheet-v2/<id>/<번호>.png — 캡션 「standing still, full front view」의 첫 장(정본 머리 되붙임)
REF_EDIT_AXIS = "strength"                         # 편집 세기 축 — mask 안에서 바탕을 얼마나 남기나(얼굴 ↔ 화풍 균형). guidance는 2.1이 「guidance 없이」 학습돼 축으로 안 씀
REF_EDIT_AXIS_VALUES = [0.7, 0.85, 1.0]            # 1.0 = 문서 기본값
REF_EDIT_STEPS = 25                                # 공식 ComfyUI 편집 워크플로 값(mflux README 예시)
REF_EDIT_MASK_PAD = 0.06                           # 몸 상자를 각 변으로 폭·높이의 이만큼 넓혀 마스크(옷자락·머리카락 포함)
REF_EDIT_SHUFFLE_SEED = 358                        # 화면 A·C 순서 섞기(대조 위치를 숨김)
REF_EDIT_ADOPT_MIN = 5                             # 채택: 사울·다윗 각각 「읽힌다」 ≥ 5/8
REF_EDIT_CONTROL_MAX = 2                           # 분해능: 대조 「읽힌다」 합 ≤ 2/6 (넘으면 보류)
REF_EDIT_STYLE_PENALTY = 0.5                       # 처치 무너짐 비율 − 대조 무너짐 비율 > 이 값이면 채택 → 조건부

# task#359 — 같은 참조 편집을 Qwen-Image-Edit-2511로: 전체 편집 → 358 몸 상자만 바탕에 되붙임. 장면·시드·참조·마스크·판정 규칙은 REF_EDIT_* 그대로. 편집 전 고정.
REF_EDIT_2511_MODEL = ("qwen-image-edit-2511", "mflux-generate-qwen-edit")
REF_EDIT_2511_QUANTS = [8, 6, 4]                   # 양자화 사다리(q8 --low-ram → q6 → q4) — 단계마다 첫 1장까지만 「안 돔」 확인
REF_EDIT_2511_STEPS = 20                           # mflux 기본(cli/defaults/defaults.py)
REF_EDIT_2511_GUIDANCE = 2.5                       # models/qwen README 기본
REF_EDIT_2511_FEATHER = 8                          # 되붙임 경계 가우시안 반경 px(마스크 상자 경계만 부드럽게)
REF_EDIT_2511_MIN_DIFF = 10.0                      # 조작 확인 하한: 몸 상자 안 평균 픽셀 차(0~255) — 358 세기 1.0 변화 29.9의 1/3
REF_EDIT_2511_MAX_SEC = 600                        # 「안 돔」: 장당 10분 초과(스왑)
REF_EDIT_2511_SHUFFLE_SEED = 359                   # 화면 A·C 순서 섞기
REF_EDIT_2511_PROMPT = ("Replace the man on the {side} in image 1 with the man shown in image 2 and image 3 — same face, hair, "
                        "beard, body build and clothing. Keep his pose and position, and keep the pencil and watercolor drawing style, "
                        "lighting and everything else of image 1 unchanged.")   # 358 틀에서 「the person in the masked area」만 위치로

# task#360 — 같은 참조 편집을 2511 + Lightning 4스텝 LoRA로(guidance 1 래퍼 mflux_qwen_edit_cfg1.py). 장면·시드·참조·마스크·되붙임·판정 규칙은 REF_EDIT_*·REF_EDIT_2511_* 그대로. 편집 전 고정.
REF_EDIT_LIGHTNING_LORA = ("lightx2v/Qwen-Image-Edit-2511-Lightning", "Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors", 1.0)   # (HF 레포, 파일, 세기)
REF_EDIT_LIGHTNING_QUANTS = [8, 6]                 # q8 --low-ram → 「안 돔」이면 q6 한 번만, 그래도 안 되면 stop
REF_EDIT_LIGHTNING_STEPS = 4
REF_EDIT_LIGHTNING_GUIDANCE = 1.0                  # 래퍼가 부정 계산을 건너뜀(결과 동일, 후속 시험 평균 차 0.053/255)
REF_EDIT_LIGHTNING_MAX_SEC = 600                   # 「안 돔」: 첫 1장 장당 10분 초과 또는 오류
REF_EDIT_LIGHTNING_MIN_TARGETED = 10.0             # 조작 확인 하한: 전체 편집 원본 대 입력 그림의 몸 상자 안 평균 차 − 상자 밖 평균 차(0~255) — 후속 시험 외형 명시 33.4, 무처치 −2.7
REF_EDIT_LIGHTNING_SHUFFLE_SEED = 360              # 화면 A·C 순서 섞기
REF_EDIT_LIGHTNING_PROMPT = ("Change the man on the {side} in image 1 into the man shown in image 2 and image 3: {look}. "
                             "Keep his pose, his position and size in the scene, and keep the pencil and watercolor drawing style "
                             "and everything else in image 1 unchanged.")   # {look} = derive_scene.cast_describe(장면 안 정본 — cast_override 포함), 손으로 쓰지 않음
# task#360 S0 뒤 개정(2026-10-17, 사용자 「권장진행」): 카드 층 {look}은 바탕과 같은 문구라 다윗이 무처치(targeted −1.49·8.27)였고 정본 그림(붉은 튜닉)에서 멀어졌다
# → {look}을 정본 그림(frozen 초상 + lora-sheet-v2 전신 07) 쪽 서술로. 그림을 보고 손으로 썼다(사람 결정). 나머지 고정 절은 그대로.
REF_EDIT_LIGHTNING_LOOK_SRC = "image+scene"        # "card" = cast_describe(S0 첫 시도) · "image" = 아래 서술(360 재현은 이 값으로) · "image+scene" = task#361
REF_EDIT_LIGHTNING_LOOK_IMAGE = {
    "saul": "an ancient Israelite man in his 40s, short dark hair cropped close, short full dark beard, angular face, lean average build, "
            "in a plain brown short-sleeved tunic reaching the shins with a brown leather belt",
    "david": "an ancient Israelite young man in his 20s, thick tight dark curly hair, short full dark beard, rosy cheeks, slender build, "
             "in a plain red short-sleeved knee-length tunic with a brown leather belt",
}
# task#361(2026-10-17): 360 엔게디 처치 8/8 「무너짐」 — 정본 튜닉 절이 사울 겉옷을 지웠다(용어집 「카드 층 / 얼굴 층」: 차림은 장면 명세가 덮어씀).
# → "image+scene" = 정체성(얼굴·머리·수염·체격·나이대)은 아래(LOOK_IMAGE에서 차림 절만 뗌) + ", wearing " + 장면 명세 figures[].costume.en. 편집 대상은 엔게디만.
REF_EDIT_LIGHTNING_LOOK_IDENTITY = {
    "saul": "an ancient Israelite man in his 40s, short dark hair cropped close, short full dark beard, angular face, lean average build",
    "david": "an ancient Israelite young man in his 20s, thick tight dark curly hair, short full dark beard, rosy cheeks, slender build",
}
REF_EDIT_COSTUME_SCENES = {"engedi": ["saul", "david"]}   # "image+scene" 모드의 편집 장면 → 처치 인물(사울 → 다윗 차례)
REF_EDIT_COSTUME_SHUFFLE_SEED = 361                # 판정 화면 순서 섞기
# task#362(2026-10-17): 엔게디 장면 문구 수리(굴 벽 색 낱말) — 판정 화면 순서 섞기(기준 + 새 바탕 8 + 353 바탕 8)
ENGEDI_TEXT_SHUFFLE_SEED = 362
# task#363(2026-10-17): 512토큰 수리 판정 — 화면 순서 섞기(장면마다 기준 + 새 8 + 이전 8)
PROMPT_512_SHUFFLE_SEED = 363
PROMPT_512_SHUFFLE_SEED_R2 = 3632   # r2(차림 자리·인물별 방향 복원) — r1 그림 위치를 기억하지 않게
# task#364(2026-10-18): 엔게디 굴 어둠·빛 판정 — 화면 순서 섞기(기준 + r2 8 + A 8 + B 8)
ENGEDI_DARK_SHUFFLE_SEED = 364
# task#365(2026-10-18): 엔게디 시선 축 판정 — 그림 순서 섞기(기준 + r2 8 + A 8 + B 8, 네 화면 같은 순서)
ENGEDI_GAZE_SHUFFLE_SEED = 365
# task#366(2026-10-18): 엔게디 마주 봄 B1·B2 판정 — 그림 순서 섞기(기준 + A 8 + B1 8 + B2 8 + B 8, 네 화면 같은 순서)
ENGEDI_AWAY_SHUFFLE_SEED = 366
# task#367(2026-10-18): 엔게디 마주 봄 귀속·손 B′·Bh 판정 — 그림 순서 섞기(기준 + A 8 + B 8 + B′ 8 + Bh 8, 네 화면 같은 순서)
ENGEDI_BACKHAND_SHUFFLE_SEED = 367
