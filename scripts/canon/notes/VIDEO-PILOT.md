# 로컬 영상 모델 파일럿 — 장면 그림 한 장 → 3초 영상 (task 354)

목표: 투어 카드의 지금 애니메이션을 대체할 짧은 영상(사용자 2026-10-15). 승인된 장면 그림 한 장을 첫 프레임으로 넣고, 이 맥(M5·32GB)에서 3초 남짓 영상을 만든다. 두 모델(Wan 2.2 TI2V-5B·LTX-2.3 int4, 둘 다 MLX)을 같은 입력으로 시험한다.

## 고정 절(결과를 보기 전에 적음 — 실행 중 바꾸지 않는다)
- 입력(사람 승인본 2장, 둘 다 1216×640):
  - 길갈 `samples/face-widen/approved-gilgal.png`
  - 엔게디 `samples/engedi-final/approved-engedi-c.png`(2026-10-18 승인 — C s23 + 칼 K1 s2)
- 해상도 **1280×704**(가로). 두 모델 공식 가로 해상도 중 1216×640에 가장 가깝다. Wan 5B는 720P = 1280×704, LTX two-stage는 양변 64의 배수를 요구하고 1280·704 둘 다 맞다. 입력은 두 모델 모두 「덮도록 확대(×1.1) → 가운데 자르기」로 같은 그림을 미리 만들어 넣는다(1216×640 = 1.900, 1280×704 = 1.818이라 좌우가 약 2%씩 잘린다 → `~/.local/biblemap-imggen/video-pilot/input-<장면>.png`).
- 길이 **73프레임 @24fps = 3.04초**. Wan(4n+1)과 LTX(8k+1) 둘 다 허용값이라 두 모델이 같다.
- 시드 **42, 23**. 생성 수 2모델 × 2장면 × 2시드 = **8클립**.
- 움직임 문구(영문, 두 모델 같은 문구 — 그림에 이미 있는 것은 반복하지 않고 움직이는 것만 쓴다):
  - 길갈: `Slow gentle camera push-in. The crowd's raised hands sway slightly, the thin smoke rises and curls from the stone altar, robes stir in a light breeze. The two men in front stay still and calm. Pencil line drawing with watercolor wash on cream paper, hand-drawn texture kept throughout.`
  - 엔게디: `Slow gentle camera push-in. The kneeling man on the left slowly lifts the cut corner of the cloak with his knife; the crouching man on the right keeps looking toward the bright cave mouth and breathes slowly. Dust drifts in the light from the cave mouth. Pencil line drawing with sepia wash, hand-drawn texture kept throughout.`
- 생성은 **한 번에 하나**(다운로드·변환과도 겹치지 않음 — 메모리 「로컬 이미지 생성 스택」 운영 규칙). 각 클립은 별 프로세스로 띄워 끝나면 메모리를 반환한다. 이미 있으면 건너뛴다.

## 판정 규칙(실행 전 고정)
- 기계 측정(참고값, 게이트 아님) → `samples/video-pilot/metrics.json`:
  - 클립당 소요 시간(`sec`, 모델 로드 포함 전체 프로세스 벽시계)과 피크 메모리(`/usr/bin/time -l`의 최대 RSS — MLX 통합 메모리는 RSS에 다 안 잡힐 수 있어 참고값).
  - **깨짐 검사**: 프레임별 회색조 화소 표준편차(`std`)와 이웃 프레임 평균 절대차(`diff`). `std`가 첫 프레임 대비 30% 아래로 떨어지면(뭉갬·단색) 또는 `diff`가 클립 중앙값의 5배를 넘거나 0.25(0~1 척도)를 넘으면(노이즈 튐·장면 전환) 그 프레임을 깨짐으로 센다. 깨진 프레임 수를 적는다.
  - **화풍 표류**: `judge_style.style_metrics`의 `ink`로 첫 프레임 대 마지막 프레임 차 |Δink|를 재고, 같은 장면·같은 모델 두 시드의 마지막 프레임 사이 |Δink|와 나란히 적는다(시드 간 차보다 크면 「표류가 시드 잡음보다 크다」).
  - 처리량 추정: 275 × 클립당 시간.
- 사람 판정(폰 페이지, 한 화면 한 질문, 영상은 카드 폭으로 재생, 기계 수치 숨김):
  - 클립마다 「연필 화풍이 끝까지 남나 → 남는다 / 사진처럼 변한다」, 「얼굴이 무너지나 → 괜찮다 / 무너진다」.
  - 마지막 화면 「투어 카드 영상으로 쓸 만한 모델 → Wan / LTX / 둘 다 아님」.
- 결론:
  - 사람이 고른 모델이 있으면 그 모델로 다음 과제(장면 10개 무인 배치 + 앱 카드 시험)를 연다.
  - 「둘 다 아님」이면 342 구조(한 장 + CSS 확대·패럴랙스 움직임 틀)로 돌아간다.

## 설치(S0)
- 런타임: `~/.local/biblemap-imggen/.venv-video`(Python 3.14.5 — mlx 휠 있음, python@3.12 불필요). 소스는 `~/.local/biblemap-imggen/src/`에 클론해 로컬 설치: `mlx-video` `87db56a`, `ltx-2-mlx` `9e4a1a5`(v0.16.3, `ltx-core-mlx`·`ltx-pipelines-mlx`). mlx 0.32.4. 변환용 torch 2.14.1.
- 모듈 경로(README·소스 확인): Wan `python -m mlx_video.models.wan_2.generate`(README의 `mlx_video.wan_2`는 옛 경로), 변환 `mlx_video.models.wan_2.convert`. LTX는 CLI `ltx-2-mlx generate`.
- **5B `--image` 지원**: README 표는 I2V를 14B에만 적지만 소스 `wan_2/generate.py:425`에 TI2V-5B 경로가 있다 — 이미지 한 장을 VAE로 인코딩해 첫 잠재 프레임에 넣고 마스크로 고정(매 단계 재적용, `:667`). 입력은 덮기 확대 + 가운데 자르기(`i2v_utils.preprocess_image`).
- **Wan 2.2 TI2V-5B: 설치 성공.** `Wan-AI/Wan2.2-TI2V-5B`(31.9GB) → `--quantize --bits 4` 변환 148초(변압기 2.9GB·T5 11.4GB bf16·VAE 2.8GB) → `~/.local/biblemap-imggen/models-video/Wan2.2-TI2V-5B-MLX`.
  - 시간 시험(입력 길갈, 1280×704×73, CFG 켬, 2단계 — 그림은 판정에 안 씀): T5 인코딩 47.7초 · **49.8 s/단계** · VAE 해독 449.8초(자동 타일) · 전체 607초 · 피크 메모리 footprint 35.8GB(스왑 사용). 시험 중 LTX 다운로드가 겹쳐 있었다.
  - **단계 설정 = 공식 기본값**(40단계·unipc·guide 5·shift 5, 결과 그림을 보기 전 시간만 보고 결정): 추정 클립당 약 42분, Wan 4클립 약 2.8시간 → 감당 가능. 4단계 Turbo LoRA(`Kijai/WanVideo_comfy` Wan22-Turbo, 추정 약 10분)는 **라이선스 미표기**라 쓰지 않는다 — Wan을 고르는 근거(Apache 2.0)를 깎는다. 다운로드만 해 둠.
  - 부정 문구: 기본값(중국어)에 `风格·作品·画作·画面`이 있어 고정 절의 공용 부정 문구로 바꾼다(`--negative-prompt`).
- **LTX-2.3 int4: 설치 성공(다운로드 중 기록).** `dgrauet/ltx-2.3-mlx-q4`는 README의 「약 12GB」가 아니라 **55.6GB**다(변압기 3벌 각 10.5GB + distilled LoRA 2벌 각 7.1GB + connector 5.9GB 등). `--two-stage --low-ram`은 1단계 `transformer-dev`, 2단계는 LoRA 융합 대신 미리 합친 `transformer-distilled-1.1`로 바꿔 끼운다(`_base._resolve_safetensors`가 버전 붙은 파일을 고름) → 안 쓰는 `transformer-distilled.safetensors` 하나만 빼고 받음. 텍스트 인코더 `mlx-community/gemma-3-12b-it-4bit` 7.5GB.
  - 설정: `generate --two-stage --low-ram --no-audio -f 73 --frame-rate 24 -H 704 -W 1280 --image <입력> 0 1.0`(이미지 CRF는 2.3 기본 33). 다른 단계 수는 기본값(1단계 30·2단계 3·cfg 3·stg 1).
- 비로그인 HF(초당 약 8MB) — 받기 합계 약 1시간 반.

## 생성 결과(기계 측정 — 참고값, 게이트 아님)
8/8 생성 성공(2026-10-18 17:36~22:15, 한 번에 하나, 다른 생성·다운로드 없음). 수치 원본 `samples/video-pilot/metrics.json`. 클립은 레포 밖 `~/.local/biblemap-imggen/video-pilot/`.

| 모델 | 클립당 시간 | 275 정차지 | 피크 footprint | 깨짐 프레임 | 화풍 표류 \|Δink\| (s42 / s23) · 시드 간 |
|---|---|---|---|---|---|
| LTX-2.3 int4 two-stage | 1643~1675초(평균 27.5분) | **126시간(5.3일)** | 15.9~16.1GB | 길갈 s42 **14**, 나머지 0 | 길갈 .0045/.0195 · .0146 — 엔게디 .0559/.0276 · .0286 |
| Wan 2.2 TI2V-5B 4bit 40단계 | 2473~2566초(평균 41.7분) | **191시간(8.0일)** | 33.3GB(스왑) | 0 | 길갈 .0036/.0062 · .0026 — 엔게디 .0063/.0044 · .0019 |

- **LTX 길갈 s42의 「깨짐 14」는 노이즈·뭉갬이 아니다.** 이웃 프레임 차이가 한 프레임 걸러 0.0017 ↔ 0.013으로 번갈아 나온다 — 움직임이 두 프레임에 한 번만 일어나는 끊김(약 12fps 떨림). 중앙값이 반쪽 0에 끌려 내려가 「중앙값 5배」 규칙에 걸렸다. 최대 차이 0.0167은 노이즈 기준 0.25에 한참 못 미친다. 짝·홀 차이 비가 이 클립만 6.8(나머지 7개 1.0~1.4). 규칙은 고정이라 숫자는 그대로 둔다.
- 화소 표준편차는 8개 모두 첫 프레임의 97% 이상 유지(뭉갬·단색화 없음).
- 화풍 표류: Wan은 첫→끝 |Δink| 0.004~0.006으로 거의 그대로, LTX는 0.005~0.056으로 더 움직인다(엔게디 s42가 시드 간 차의 2배). 단 `ink`는 화풍 **종류**를 못 가른다(메모리 「로컬 이미지 생성 스택」 — 「그린 양」에 가깝다) → 사진처럼 변했는지는 사람 판정이 정한다.
- 움직임 양(이웃 프레임 차 중앙값): LTX 0.0026~0.0088, Wan 0.0027~0.0042 — LTX가 더 많이 움직인다.

## 사람 판정
판정 페이지(비공개 Artifact, 모델 이름 가림 — 묶음 A/B, 섞기 시드 354): `make_video_pilot_page.py` → https://claude.ai/artifact/8zp4XRqtmhyeQhMWei6Vv5 (문항 17: 화풍 8 · 얼굴 8(머리 확대) · 쓸 만한 묶음 1).

사용자 답(2026-10-18, 17문항 전부 답함, 「모르겠음」 0):

| 클립 | 화풍 | 얼굴 |
|---|---|---|
| ltx-gilgal-s42 | 남는다 | 괜찮다 |
| ltx-gilgal-s23 | 남는다 | 괜찮다 |
| ltx-engedi-s42 | 남는다 | 괜찮다 |
| ltx-engedi-s23 | 남는다 | 괜찮다 |
| wan-gilgal-s42 | 남는다 | 괜찮다 |
| wan-gilgal-s23 | 남는다 | 괜찮다 |
| wan-engedi-s42 | 남는다 | 괜찮다 |
| wan-engedi-s23 | 남는다 | 괜찮다 |

- 투어 카드 영상으로 쓸 만한 묶음: **B = LTX**(A = Wan). 모델 이름을 가린 상태에서 고름.
- 읽기: 화풍·얼굴은 두 모델 모두 8/8 통과라 두 축으로는 갈리지 않았다. 갈린 것은 마지막 「카드로 쓸 만한가」 하나다. 기계 수치로 보면 LTX가 더 많이 움직이고(이웃 프레임 차 중앙값 약 2배) 더 빠르며(27.5분 대 41.7분) 메모리가 절반(16GB 대 33GB)이다. 이유를 따로 묻지는 않았다.
- 끊김: 기계가 잡은 LTX 길갈 s42의 한 프레임 걸러 움직임은 사람 판정 문항(화풍·얼굴)에 들어 있지 않았다 → 다음 과제에서 시드별 끊김 검사(짝·홀 차 비)를 가드로 쓴다.
- 대표 클립: `samples/video-pilot/ltx-engedi-s42.webm`(LTX 중 끊김 없는 첫 시드 — 클립 간 우열은 묻지 않아 기본값 규칙으로 고름, VP9 720폭 116KB).

결론: LTX-2.3 int4(two-stage) 채택 — 다음 과제로 장면 10개 무인 배치 + 앱 카드 시험을 연다(275 정차지 추정 126시간, 끊김 가드 포함).
