---
last_mapped_commit: 50d8961b1d6148fed2952fc59cb4bed3e634b592
mapped: 2026-10-24
---

# STACK

BibleMap의 언어·런타임·프레임워크·의존성·빌드/설정 사실 정리. 도메인 용어 정의는 여기 없음(그건 `CONTEXT.md`). 파일별 디렉터리 구조는 `.forge/codebase/STRUCTURE.md` 참고.

전체 구성: 백엔드 FastAPI + Neo4j Python 드라이버, 프론트 React + Vite + maplibre-gl, docker-compose 3서비스 스택(neo4j + api + nginx), 표준 배포(push → 레포 전용 self-hosted 러너 → `deploy/pre-deploy.sh`(게이트) → `~/runtime/taebro-infra/bin/deploy`, main=prod·dev=dev 두 실행 자리).

여기에 이번 구간부터 **세 번째 런타임**이 붙었다 — `scripts/canon/`의 로컬 이미지 생성(저작) 파이프라인이다. Python + torch/diffusers로 돌고, 실행 venv와 모델 가중치는 레포 밖에 있으며, 앱 이미지·배포 경로에는 들어가지 않는다(ADR `260825-065028`). 자세한 것은 아래 「저작 파이프라인」 절.

## 백엔드

- 언어/런타임: Python. 컨테이너 베이스는 `python:3.12-slim`(`backend/Dockerfile`). 반면 `deploy/pre-deploy.sh`가 호스트에서 직접 실행하는 주입 스크립트(`backend/scripts/inject_ko_names.py`·`inject_date_corrections.py`)와 `scripts/check.sh`의 검증 스크립트들은 이 머신의 host python3(현재 `Python 3.14.5`)로 돈다 — 컨테이너 밖 실행 경로가 상시 존재한다. 레포 루트 `scripts/uat_intro_entry.py`·`uat_intro_gutter.py`·`uat_scene_detail_pilot.py`(신규)·`uat_tour_chunk_split.py`(신규)·`render_scene.py`(신규)도 같은 host python3로 돌지만 `scripts/check.sh` 게이트에는 배선되지 않는다(각 스크립트 docstring에 사유 명시 — `deploy/pre-deploy.sh`가 이미지 빌드 **전**에 check.sh를 부르므로 그 시점 서빙 중인 것은 옛 빌드라 게이트에 넣으면 초록·빨강이 둘 다 거짓이 된다). 사람이 배포 전후로 직접 호출하는 실측 UAT·저작 도구다.
- `playwright`(호스트 python에만 설치, 현재 `1.60.0`) — 위 UAT·렌더 스크립트들과 저작 파이프라인의 `scripts/canon/cond_shoot_heads.py`가 `playwright.sync_api.sync_playwright`로 헤드리스 브라우저를 띄워 `localhost:8080`을 실측·촬영한다(`anthropic`과 동일하게 `backend/requirements.txt`에는 없음, API 이미지 미포함. `scripts/canon/requirements.txt`에도 없다 — 저작 파이프라인 절 참조).
- 런타임 의존성(`backend/requirements.txt`, 전부 핀 고정):
  - `fastapi==0.136.3`
  - `neo4j==6.2.0` (공식 Neo4j Python 드라이버)
  - `uvicorn==0.49.0` (ASGI 서버)
  - 이 3개가 컨테이너에 설치되는 전부. `anthropic` SDK는 requirements에 **없고** 호스트 python에만 설치돼 있다(현재 `anthropic 0.111.0`) — 빌드타임 생성 스크립트 전용이라 API 이미지에는 들어가지 않는다.
- 앱 엔트리: `backend/app/main.py` — `FastAPI(lifespan=...)`.
  - `lifespan`에서 Neo4j 인덱스 5종(`Person`/`Place`/`Event`/`PeopleGroup`/`Book`의 `theographic_id`)을 `CREATE INDEX <label>_tid IF NOT EXISTS`로 보장. 실패해도 `logger.exception` 후 인덱스 없이 계속 진행.
  - `CORSMiddleware`: `allow_origins=["*"]`, `allow_credentials=False`, `allow_methods=["GET"]`, `allow_headers=["*"]` — 읽기 전용 공개 API.
  - 라우터 14개 include: `nodes, events, search, books, persons, journey, places, tours, family, words, verses, reliance, stats, timeline`(신규).
  - 로깅: `_configure_logging()`을 라우터 import 전(모듈 최상단)에 1회 호출. `neo4j`/`urllib3`/`asyncio`는 WARNING 승격, `uvicorn`·`uvicorn.access`는 `propagate=False`(root 중복 emit 차단). `uvicorn.error`는 의도적으로 제외(자체 핸들러가 없어 propagate를 끊으면 기동/에러 라인이 사라짐 — 주석에 명시).
- Neo4j 드라이버: `backend/app/db.py` — 모듈 전역 싱글턴 `get_driver()`. `NEO4J_URI`(기본 `bolt://localhost:7687`), `NEO4J_USER`(기본 `neo4j`), `NEO4J_PASSWORD`(필수, 없으면 `RuntimeError`).
- 오버레이 로더: `backend/app/overlays.py` — `data/` 하위 JSON을 `functools.lru_cache(maxsize=1)`로 1회 로드. `_resolve`/`_resolve_dir`가 `DATA_DIR`(기본 `/app/data`) → 레포 `data/`(`_REPO_DATA_DIR`) 순으로 해석하고, 없으면 `[Overlays]` 경고 후 빈 데이터 폴백. 로더 15종: `book_events_raw`, `event_verses`, `bible_verses`, `word_distribution`, `books_ko`, `chapter_summaries`, `chapter_sections`, `quotations`, `messianic_prophecies`, `covenants`, `parables_miracles`, `place_coords`, `place_context`(신규, 장소 페이지용), `topical_verses`, `verse_persons`. 그 외 헬퍼 `curated_person_id(events)` 하나(큐레이션 신원 규약 단일 지점).
- 절 검색 공용 모듈: `backend/app/verse_search.py`(신규) — 정본 절 사전(`overlays.bible_verses()`)을 substring으로 전수 스캔하는 `search_verses(term, book_id, match_en)`. `functools.lru_cache(maxsize=256)`로 질의 단위 캐시. `search.py`(통합 검색)와 `words.py`(단어별 절 목록)가 공유(이전엔 `words.py`에 중복 구현).
- 큐레이션 인물 색인 공용 모듈: `backend/app/curated.py`(신규, task#278) — `overlays.py`와 같은 층(라우트를 import하지 않아 순환 import 차단). `CURATED`(slug → `{nameKo, era}` 35건 고정 매핑), `ERA_ORDER`(시대 표시 순서 8구간), `person_events(slug)`(`person_events/<slug>.json`을 `sortKey` 순 정렬, `lru_cache(maxsize=64)`), `curated_index()`(큐레이션 35인 목록, `lru_cache(maxsize=1)`), `id_to_slug()`/`slug_to_id()`/`seal_id_to_slug()`(전부 `lru_cache(maxsize=1)`). 소비 라우트 8개: `persons`·`journey`·`places`·`timeline`·`tours`·`stats`·`reliance`·`family`(이전엔 `persons.py`의 `_ERA`/`_NAME_KO`/`_build_list`가 여러 라우트에 중복 정의됐던 것을 이 모듈로 승격).
- 라우트 모듈: `backend/app/routes/*.py` 15개(`__init__.py` 포함, 신규 `timeline.py` 추가). `@router.get` 기준 **32개 GET 엔드포인트**(POST/PUT/DELETE 없음, `/timeline/canon`·`/place/{place_id}` 신규). 응답은 전부 `JSONResponse` + `Cache-Control` 헤더인데, 이번 구간에 **`public, max-age=3600` 6곳이 전부 `max-age=300`으로 내려갔다**(`books.py` 3곳·`reliance.py` 2곳·`verses.py` 1곳). 이제 상한은 `max-age=300` 하나이고 예외는 `books.py`의 `/books-overview`(`no-store`) 뿐 — `backend/scripts/validate_api_cache_headers.py`가 `max-age ≤ 300` 경계를 게이트로 강제한다(긴 `max-age`가 ETag 없이 붙으면 `data/` 편집 + `restart api`로 고친 내용이 재방문 브라우저에 반영되지 않고, `api.js`의 빌드타임 캐시버스터는 그 경로를 원리적으로 못 덮는다). 집계형 계산은 `lru_cache`(대부분 `maxsize=1`, 일부 `maxsize=66/256/2048/None`)로 프로세스 내 캐시 → **데이터 변경 시 API 재시작 필요**.
- 데이터/스크립트: `backend/scripts/*.py` 57개(+4). 접두사별 — `load_*` 8(Neo4j 적재), `generate_*` 11(오버레이 생성), `inject_*` 6(Neo4j 속성 주입), `validate_*` 25(검증, 신규 3종: `validate_api_cache_headers.py`·`validate_scene_sketch_detail.py`·`validate_canon_pipeline.py`), `build_*` 3(색인 빌드), `apply_*` 1(`apply_event_dedupe.py`). 접두사 밖 3개는 `__init__.py`, `enrich_place_coords.py`, 그리고 신규 `_svgpath.py`(SVG `d` 속성 → 절대 좌표 점 목록 파서 — `validate_scene_sketch_detail.py`가 선 겹침을 바운딩박스 대신 점으로 재려고 쓰는 사적 헬퍼). 앱 코드는 이 스크립트를 import하지 않는다(빌드타임/운영 전용 경계) — 예외 1건: `validate_event_verses.py`가 `generate_person_event_verses.py`의 `expand_range_label`/`verse_keys_by_book`을 import해 생성기와 같은 파서·오라클을 재사용한다(스크립트 간 import, 앱 경계와는 무관).
  - `backend/scripts/generate_person_event_verses.py`(task#282, ADR `260821-125000`) — 근거 절 범위 전개가 getbible 실시간 fetch에서 오프라인 판정으로 전환됨. `expand_range_label()`/`verses_for_label()`이 정본 절 사전(`data/bible/verses.json`)의 verseID 키 존재만으로 라벨이 가리키는 범위를 전개(네트워크 호출 0회) — 교차-장·장 단위 범위를 첫 절 1개만 베이킹하던 결함(실측 12건)을 없앤다. 기존 `fetch_chapter`/`fetch_verses`(getbible 호출부)는 새 경로에서 더는 호출되지 않는 죽은 코드로 남아 있다(수술적 범위 결정 — ADR이 명시, 걷어내지 않음). `--rebake [--dry-run]` 플래그로 기존 `event_verses/events.json` 블록을 새 오라클로 재전개하는 `rebake_range_labels()`도 이번에 추가.

## 저작 파이프라인 (`scripts/canon/`) — 앱과 다른 런타임

이번 구간에 들어온 새 서브시스템(`.py` 46개 + 판단 문서·판정 자산 130여 개). 레포 안에는 **소스·판단 문서·정답지 자산만** 있고, 실행 인터프리터와 모델 가중치는 레포 밖에 있다. 앱(`backend/app/`·`frontend/src/`)은 이 디렉터리를 import하지 않고 `backend/Dockerfile`·`docker-compose.yml`·`deploy/pre-deploy.sh`도 이 파이프라인을 설치·실행하지 않는다(ADR `260825-065028`) — 게이트 하나(`validate_canon_pipeline.py`)만 소스를 읽는 형태로 배포 경로에 걸려 있다.

- 언어/런타임: Python 3.14. 실행 인터프리터는 **레포 밖** `~/.local/biblemap-imggen/.venv314/bin/python3`(실측 `Python 3.14.5`, 호스트 python3와 같은 버전이지만 별개 venv) — 스크립트 docstring과 `scripts/canon/notes/*.md`의 재현 명령이 전부 이 절대경로를 적어 둔다. 디바이스는 Apple Silicon **MPS 고정**(`.to("mps")`, `torch.Generator("mps").manual_seed(...)`) — CUDA/CPU 분기가 없다.
- 의존성 박제: `scripts/canon/requirements.txt`(2026-08-25 시점 venv `pip freeze` 43줄, 전부 핀 고정). 핵심 — `torch==2.13.0`, `diffusers==0.40.0`, `transformers==5.15.1`, `accelerate==1.14.0`, `huggingface_hub==1.28.0`, `safetensors==0.8.0`, `numpy==2.5.2`, `pillow==12.3.0`. **파일 머리 주석이 재현 미결 3축(모델 리비전 미고정·MPS 결정성 미보장·재현 미실측)을 명시한다 — 「고정했다」로 읽으면 안 된다.**
  - 실제 venv는 이미 이 박제에서 드리프트해 있다(2026-09-02 실측 `pip freeze` 46줄): 박제에 없는 `gguf==0.19.0`·`peft==0.20.0`·`torchvision==0.28.0`이 설치돼 있다. 반대로 `playwright`는 이 venv에 **없다** — playwright를 쓰는 유일한 파이프라인 스크립트 `scripts/canon/cond_shoot_heads.py`는 호스트 python3(playwright `1.60.0`) 경로로 도는 셈이다.
- 모델 자산: 레포에 없다. `from_pretrained`가 `~/.cache/huggingface`(실측 47GB)의 허브 캐시를 읽는다. 선언처는 `scripts/canon/params.py` — `SDXL_BASE`(`stabilityai/stable-diffusion-xl-base-1.0`), `CN_MODEL`(스크리블 ControlNet `xinsir/controlnet-scribble-sdxl-1.0`), `IP_ADAPTER_REPO`(`h94/IP-Adapter`, `sdxl_models/ip-adapter_sdxl.bin`), `IMAGE_ENCODER`(CLIP ViT-bigG 이미지 인코더). 앞 셋은 저장소 이름일 뿐 리비전이 아니고, 유일하게 스냅샷 해시가 박힌 `IMAGE_ENCODER`는 **이 머신 로컬 캐시의 절대경로**라 다른 머신에서는 성립하지 않는다.
- diffusers 파이프라인 클래스: `StableDiffusionXLControlNetPipeline`(스윕·프로브 대다수, 17곳), `StableDiffusionXLControlNetInpaintPipeline`(순차 인페인팅), `StableDiffusionXLInpaintPipeline`(현행 정본 생성기 `gen_scripture_scene.py` — 콘티를 쓰지 않기로 해서 ControlNet 없이 단계 인페인팅만 쓴다), `StableDiffusionXLImg2ImgPipeline`, `AutoPipelineForText2Image`. 마스크는 `diffusers.image_processor.IPAdapterMaskProcessor`, 판정용 CLIP은 `transformers`의 `CLIPVisionModelWithProjection`/`CLIPTextModelWithProjection`/`CLIPTokenizer`.
- **두 번째 생성 런타임(mflux/MLX)**: 현행 생성·편집은 SDXL이 아니라 레포 밖 `~/.local/biblemap-imggen/.venv-mflux`(Python 3.14.5, 실측 mflux 0.22.0·mlx 0.32.3)의 `mflux-generate-z-image(-turbo)`(Z-Image-Turbo Q8, Apache-2.0)·`mflux-generate-flux2-edit`(`flux2-klein-4b`, 국소 편집)·`mflux-generate-qwen-edit`(`qwen-image-edit-2511` + Lightning, 인물 정본 참조 편집)·`mflux-train`(Z-Image LoRA 학습)을 서브프로세스로 부른다(`gen_*.py`·`batch/run_scene.py` 등). 가중치는 HF 캐시, 스크립트·재현 명령은 `.venv314`(diffusers/ControlNet 가이드)와 `.venv-mflux`를 용도별로 나눠 적는다. 이 둘 모두 `scripts/canon/requirements.txt`(주석 포함 62줄 · 패키지 핀 43줄, 2026-08-25 뒤 무변경)에 박제돼 있지 않다.
- **`claude -p` 판정자(구독 OAuth, 키 없음)**: `batch/judge_vlm.py`·`judge_spec.py`·`style_judge.py` 등이 `claude -p --model <sonnet|opus> --output-format json --no-session-persistence`를 서브프로세스로 불러 그림·명세를 채점한다. 별도 API 키·SDK를 쓰지 않는다.
- **영상 시험(앱 비포함)**: `batch/build_anim.py`·`batch/anim_template.html`과 레포 밖 `~/.local/biblemap-imggen/models-video/`(MLX LTX-2.3 q4, Wan2.2-TI2V-5B-MLX 변환본)로 로컬 클립 파일럿을 돈다.
- **크기 기준표 설정**: `scripts/canon/scale.json`(cm 정본·키 비·`crowd_stage`·`perspective` 등 단일 표, 칸마다 근거 `[직접]`/`[추론]`/`[저작]` 표기)을 `scripts/canon/scale.py` 읽개가 로드해 가이드(`batch/make_guide.py`)·검사(`check_scenes.py`)·판정 문항(`batch/judge_items.py`)이 숫자를 거기서만 읽는다(ADR `261024-083947`). 규칙 원장 `scripts/canon/rules.json`이 생성·명세 층 규칙의 정본이고 `recheck.py`가 전 명세·승인 그림을 재검한다. 의존은 표준 라이브러리뿐.
- 파라미터 정본: `scripts/canon/params.py` 하나가 생성 파라미터(모델 ID, `STEPS=30`, `GUIDANCE=6.5`, `PERSON_CN=0.3`/`SCENE_CN=0.8`, `PERSON_SIZE`/`SCENE_SIZE`/`SAMPLE_SIZE`, `IP_SCALE=0.3`, `THRESHOLD=60`, 시드 `SEED_FIXED=11`·`PERSON_SEEDS`·`SCENE_SEEDS`)와 경로(`CANON_DIR`·`REPO_ROOT`·`NOTES`·`FROZEN`·`REFERENCE`·`OUT_ROOT`)를 선언하고, 나머지 스크립트는 `import params`로만 읽는다. `_`로 시작하는 이름은 정본 키가 아니다(게이트 계약).
- 스크립트 구성: `.py` 46개(루트 42 + `conti/` 2 + `setup/` 2, `params.py` 포함). 접두사별 — `gen_*` 21(생성기·스윕), `judge_*` 8(기계 판정), 그 밖에 `derive_prompts.py`(프롬프트 파생 정본, 45KB — 어떤 프롬프트도 리터럴로 파일에 적지 않는다), `try_prompt.py`(토큰·그림·3축 연습대, `--check`는 GPU 0), `prep_cond.py`·`make_masks.py`(조건 입력·마스크, `params.THRESHOLD` 공유), `long_prompt.py`(77토큰 우회), `freeze_faces.py`/`freeze_samples.py`, `arm_sweep.py`·`sweep_cause.py`·`probe_cn.py`, `cond_shoot_heads.py`(playwright 촬영).
- 산출물은 레포에 들어오지 않는다: `params.OUT_ROOT = .forge/reports/canon-pilot`이고 `.gitignore`의 `.forge/reports/`가 덮는다. 시드 고정이라 **재현 명령이 산출물을 대신한다**(`notes/SCENE-1SAM17.md` §0에 현행 재현 명령이 있다 — 전 8단계·시드 1개 약 5분).
- 추적 자산(레포 안, 합계 49MB, PNG 62장): `reference/` 26MB(화풍 판정의 양성 기준 = 정답지 + 후보군), `setup/` 12MB, `samples/` 5.3MB, `frozen/` 3.0MB(동결 두상 2장 — 정체성 입력), `scene_ref/` 800KB, `conti/` 316KB. 판단 문서 `notes/`는 `.md` 20 + 측정 `.json` 37.
- **앱 소스를 입력으로 읽는다(단방향)**: `derive_prompts.py`가 `frontend/src/sketches/cast/<name>.jsx`의 `export const AXES`/`BRIEF`를 정적으로 읽고, `data/person_events/<slug>.json`의 `sortKey` 차이에서 나이를 파생한다. `cond_shoot_heads.py`는 로컬 개발 서버(`BASE`, 기본 `http://localhost:8080`)의 `#/cast` 화면을 playwright로 클립 촬영해 조건 입력 PNG를 만든다 — **파이프라인이 프론트 빌드·nginx에 의존하는 유일한 지점**이다.
- 별건 조사(코드 아님): `scripts/canon/notes/ZIMAGE.md`가 다른 엔진(`leejet/Z-Image-Turbo-GGUF` Q8 트랜스포머 + `Tongyi-MAI/Z-Image-Turbo`의 Qwen3-4B 텍스트 인코더)으로 같은 장면을 재 본 실측을 적어 뒀다. 그 시험 스크립트·산출물은 전부 레포 밖이고 `params.py`·생성기 어느 것도 그 엔진을 참조하지 않는다(venv의 `gguf` 패키지가 그 조사의 잔여물이다).

## 프론트엔드

- 언어/런타임: JavaScript(ESM, `"type": "module"`), React JSX. TypeScript 빌드 아님(`@types/*`는 에디터 타입용만). 호스트 Node `v24.15.0`, npm `11.12.1`. `frontend/package.json`에 engines 핀 없음.
- 런타임 의존성(`frontend/package.json` → 실제 설치 버전):
  - `react@^19.2.6`, `react-dom@^19.2.6` (설치 19.2.7)
  - `maplibre-gl@^5.24.0` (설치 5.24.0, 지도)
  - `lucide-react@^1.17.0` (설치 1.17.0, 아이콘)
- 개발/빌드 의존성:
  - `vite@^8.0.12` (설치 8.0.16 — 내부 번들러가 rolldown. `node_modules/rolldown`·`@rolldown` 존재, 빌드 산출물에 `rolldown-runtime-*.js` 청크가 나옴)
  - `@vitejs/plugin-react@^6.0.1`
  - `eslint@^10.3.0`(설치 10.4.1), `@eslint/js@^10.0.1`, `eslint-plugin-react-hooks@^7.1.1`, `eslint-plugin-react-refresh@^0.5.2`, `globals@^17.6.0`
  - `@types/react@^19.2.14`, `@types/react-dom@^19.2.3`
  - `vitest@^4.1.10`(신규) — 유닛 테스트 러너. 별도 `vitest.config.*` 없이 `frontend/vite.config.js` 설정을 그대로 씀. 테스트 파일 5개: `frontend/src/dates.test.js`, `mapGeo.test.js`, `mapRingController.test.js`, `urlState.test.js`, `useReadingProgress.test.js`.
- npm 스크립트(`frontend/package.json`): `dev`(vite), `build`(vite build), `lint`(eslint .), `preview`(vite preview), `test`(신규, `vitest run`). 패키지 매니저는 npm(`frontend/package-lock.json` 커밋됨, lockfileVersion 기반 재현). yarn/pnpm 설정 파일 없음.
- 엔트리: `frontend/index.html`(`#root`, `/src/main.jsx` 모듈 스크립트, `<title>BibleMap</title>`, favicon `/favicon.svg?v=2`) → `frontend/src/main.jsx` → `frontend/src/App.jsx`. 최상위 뷰는 `frontend/src/*.jsx` 다수(`MapView`, `TimelineView`, `PersonHub`, `StatsView`, `IntroView`, `BibleOverviewView`, `TopicalVersesView`, `SidePanel` 등) + 신규 `frontend/src/CastSheet.jsx`(개발 전용 설정화 시트 — `#/cast` 스테이지, 어디서도 링크되지 않아 주소를 직접 입력해야 진입, ADR `260823-190821`). 장면 스케치는 `frontend/src/sketches/`: 시대별 투어 모듈 9개 + `lib.jsx`(저작 규약 정본)·`SceneLabel.jsx` + 신규 `introMontage.jsx`(5개 투어에 흩어진 5씬만 재수출 — 인트로가 투어 청크 5개를 끌어오지 않게), 그리고 신규 인물 정본 `sketches/cast/{david,goliath}.jsx`·`sketches/cast/props/altar.jsx`(정적 지오메트리 + `export const AXES`/`BRIEF`/`HEAD_DIAMETER` — 저작 파이프라인의 `derive_prompts.py`가 이 소스를 읽는다).
- API 클라이언트: `frontend/src/api.js` — 단일 `apiGet(path, {signal})`. `API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'`. 모든 요청 URL에 `?v=<__BUILD_ID__>` 부착, 비-OK 응답은 `err.status`를 실은 `Error`로 reject, `AbortError`는 그대로 전파.
- 폰트: 외부 CDN 아님. `frontend/public/fonts/im-fell-english-latin.woff2`를 `frontend/src/index.css`의 `@font-face`가 `/fonts/...`로 셀프호스팅(라이선스 `frontend/public/fonts/IM-Fell-English-OFL.txt`).

## 빌드 / 번들링

- Vite 설정(`frontend/vite.config.js`):
  - `plugins: [react()]`
  - `define.__BUILD_ID__ = JSON.stringify(String(Date.now()))` — 빌드마다 바뀌는 식별자. `frontend/src/api.js`가 캐시버스터로 사용해 배포 직후 `max-age` 응답 캐시를 무력화(같은 배포 안에서는 값 고정 → 캐시 이점 유지).
  - `build.rollupOptions.output.manualChunks`: `node_modules` 중 `maplibre-gl`은 `maplibre` 청크, 나머지는 `vendor` 청크.
- 지연 로딩(코드 분할): `frontend/src/IntroView.jsx`와 `frontend/src/TourPlayback.jsx`가 `lazy(() => import('./tourSketches'))` + `<Suspense>`로 스케치 번들을 분리하고, `frontend/src/App.jsx`가 `lazy(() => import('./CastSheet'))`로 설정화 시트를 분리한다.
- **투어 단위 청크 분할(신규)**: `frontend/src/tourSketches.jsx`의 `TOUR_MODULES`가 9개 시대 모듈을 `() => import('./sketches/<모듈>')` 형태로만 참조한다 — 9모듈을 한 레지스트리로 정적 병합하던 이전 구조가 만든 단일 대청크(425KB)를 깨고 코드 경계를 번들 경계로 승격한 것(주석에 명시).
- 산출물: `frontend/dist/`(gitignore 대상, nginx가 마운트로 서빙). 관측된 청크(투어 분할 후) — `index-*.js`(~273KB), `vendor-*.js`(~199KB), `maplibre-*.js`(~1.03MB), `tourSketches-*.js`(~6.7KB로 축소), 투어별 청크 9개(`davidUnitedKingdom-*.js` ~78KB · `exodusToConquest-*.js` ~65KB · `gospelOfJesus-*.js` ~62KB · `ageOfJudges-*.js` ~58KB · `patriarchsCovenant-*.js` ~49KB · `elijahAndElisha-*.js` ~45KB · `theEarlyChurch-*.js` ~41KB · `creationToFlood-*.js` ~31KB · `exileAndReturn-*.js` ~29KB), `CastSheet-*.js`(~7.3KB), `introMontage-*.js`(~7.8KB), `goliath-*.js`·`lib-*.js`·`SceneLabel-*.js`(투어 청크와 시트 청크가 공유하는 소청크), `rolldown-runtime-*.js`, `index-*.css`/`maplibre-*.css`. **HMR이 아니라 마운트 서빙이므로 로컬 검증 전 `cd frontend && npm run build` 필요.**
- ESLint(`frontend/eslint.config.js`, flat config): `defineConfig([globalIgnores(['dist']), {...}])` — `js.configs.recommended` + `reactHooks.configs.flat.recommended` + `reactRefresh.configs.vite`. `files: ['**/*.{js,jsx}']`, `globals.browser` + `__BUILD_ID__: 'readonly'`, JSX 파서 옵션. 블록 하나가 추가됐다 — `files: ['src/sketches/cast/**/*.jsx']`에서 `react-refresh/only-export-components`를 끈다(인물 정본은 별칭·축 선언을 컴포넌트 export와 **같은 파일**에 둬야 검증기가 소스 하나를 정적으로 읽을 수 있다, ADR `260823-190821`).
- 백엔드 이미지 빌드: `backend/Dockerfile` — `python:3.12-slim` → `COPY requirements.txt` → `pip install --no-cache-dir -r requirements.txt` → `COPY app/ ./app/` → `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`. `data/`와 `backend/scripts/`는 이미지에 복사되지 않는다(데이터는 볼륨 마운트, 스크립트는 호스트 실행).

## 설정 파일 (git 추적)

- 루트: `docker-compose.yml`, `.dockerignore`, `deploy/`(`pre-deploy.sh`·`taebro.env`), `.env.example`, `.gitignore`, `README.md`, `CLAUDE.md`, `BIBLEMAP_PLAN.md`
- 백엔드: `backend/Dockerfile`, `backend/requirements.txt`
- 저작 파이프라인: `scripts/canon/requirements.txt`(레포 밖 venv의 박제), `scripts/canon/params.py`(생성 파라미터 정본) — 둘 다 앱 빌드가 읽지 않는다
- 프론트: `frontend/package.json`, `frontend/package-lock.json`, `frontend/vite.config.js`, `frontend/eslint.config.js`, `frontend/index.html`, `frontend/.env.production`, `frontend/.gitignore`, `frontend/README.md`
- 인프라/CI: `nginx/Dockerfile`, `nginx/nginx.conf`, `.github/workflows/deploy.yml`, `scripts/check.sh`. `scripts/` 루트의 나머지 python 6개는 두 부류다 — ① `check.sh`에 **배선된** 소스 불변식 `check_cast_axes.py`(인물 정본 5축 구별성)·`check_mask_ranges.py`(영역 마스크 delay 범위 연속성, `--selftest` 포함), ② 게이트 미배선 도구 `uat_intro_entry.py`·`uat_intro_gutter.py`·`uat_scene_detail_pilot.py`·`uat_tour_chunk_split.py`(사람이 배포 전후 수동 실행하는 Playwright UAT)와 `render_scene.py`(장면 하나를 빌드→렌더→고배율 촬영해 PNG로 남기는 저작자용 시각 피드백 루프 — `--cast`로 `#/cast` 시트도 찍는다. 판정 게이트가 아니라 도구라 배선하지 않는다고 docstring이 명시). ②는 `deploy/pre-deploy.sh`가 이미지 빌드 **전**에 check.sh를 부르므로 그 시점 서빙 중인 것은 옛 빌드라 게이트에 넣으면 초록·빨강이 둘 다 거짓이 된다.
- 에이전트 도구 설정: `.claude/settings.json`(내용은 `{"worktree":{"bgIsolation":"none"}}`), `.claude/launch.json`, `.claude/agents/*.md` 5개(`data-author`, `frontend-dev`, `line-artist`, `scripture-reviewer`, `ui-verifier`)
- gitignore 대상: `frontend/node_modules/`, `frontend/dist/`, `frontend/public/scene-color/`(신규 — 장면 채색층 `.webp` 자산. `sketches/ageOfJudges.jsx`가 `color: '/scene-color/samuel-circuit.webp'`로 참조하는데 레포에 커밋되지 않는다. 레포 안 어떤 스크립트도 이 디렉터리를 쓰지 않는다 — 외부에서 넣는 자산이다), `.env`, `__pycache__/`, `.venv/` + forge 휘발 상태(`.forge/backlog|done|executed|quick`, `plan.md`, `run.md`, `STATUS.md`, `loop.md`, `ask.md`, `reports/`, `scratch/`). `.forge/reports/`가 저작 파이프라인 산출물(`canon-pilot/`) 전량을 덮는다. `.forge/CONTEXT.md`·`adr/`·`retro/`·`codebase/`는 화이트리스트로 추적.

## 환경변수 (이름만 — 값은 이 문서에 절대 기재하지 않음)

| 이름 | 사용처 | 비고 |
| --- | --- | --- |
| `NEO4J_PASSWORD` | 실행 자리 `~/runtime/biblemap/<prod|dev>/.env`(배포) · 루트 `.env`(단독 개발) → `docker-compose.yml`(neo4j·api), `backend/app/db.py`, `backend/scripts/*`(호스트 실행), `scripts/check.sh` | 유일한 필수 비밀. compose가 `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}`로 파생(`:?` 필수 표시는 일부러 없음 — 값이 틀리면 `/health`가 503으로 잡는다) |
| `NEO4J_URI` | `backend/app/db.py`, 적재/주입 스크립트 | compose가 api에 `bolt://neo4j:7687` 주입. 호스트 실행 시 기본 `bolt://localhost:7687`, `deploy/pre-deploy.sh`는 `bolt://localhost:${NEO4J_BOLT_PORT}`로 export |
| `NEO4J_USER` | 동상 | 기본 `neo4j` |
| `DATA_DIR` | `backend/app/overlays.py` | 기본 `/app/data`. 미해석 시 레포 `data/`로 폴백 |
| `ANTHROPIC_API_KEY` | `backend/scripts/generate_book_context.py`, `generate_book_events.py`, `generate_person_context.py`, `generate_person_traits.py`, `generate_verse_events.py` | **빌드타임 생성 스크립트 전용**. 런타임 API·컨테이너는 사용하지 않음 |
| `VITE_API_URL` | `frontend/src/api.js`(`import.meta.env`) | `frontend/.env.production`에서 `/api`로 고정(빌드타임 주입). 개발 기본값은 `http://localhost:8000` |
| `NEO4J_BOLT_PORT`·`NEO4J_HTTP_PORT`·`TAEBRO_HTTP_PORT` | 실행 자리 `.env` → `docker-compose.yml` 포트 매핑, `deploy/pre-deploy.sh`, `scripts/check.sh` | env별 호스트 포트(Neo4j Bolt prod 7687·dev 7688, HTTP 7474·7475). nginx 호스트 포트는 `TAEBRO_HTTP_PORT`. 전부 `127.0.0.1` 바인딩 |
| `CHECK_STRICT` | `scripts/check.sh` | `1`이면 ESLint/vitest 부재·Neo4j 미기동·git 미가용 스킵-경고를 실패로 승격. `deploy/pre-deploy.sh`가 항상 `1`로 호출 |
| `BASE` | `scripts/canon/cond_shoot_heads.py`(신규) | 조건 입력 촬영이 붙을 **로컬 개발 서버 URL**, 기본 `http://localhost:8080`(표준 배포 뒤 이 포트는 prod 고정이 아니라 `TAEBRO_HTTP_PORT` 값을 따른다). 모델 ID가 아니다(정본이 모델 쪽을 `SDXL_BASE`로 부르는 이유가 이 이름 충돌) |

- `import.meta.env.DEV`도 프론트에서 사용(Vite 기본 제공, 별도 설정 없음).

## Docker / 배포 스택

- `docker-compose.yml` — 3 서비스, 파일 최상단 `name: biblemap-local`(작업 폴더에서 `compose up`을 해도 prod `biblemap`을 덮지 않게 한 이름; 배포가 `-p biblemap`/`biblemap-dev`로 덮어쓴다):
  - `neo4j`: 이미지 `neo4j:5`. 포트 `127.0.0.1:${NEO4J_BOLT_PORT}:7687`·`127.0.0.1:${NEO4J_HTTP_PORT}:7474`. 볼륨 `neo4j_data:/data`. 힙 192m·페이지캐시 32m 고정, `mem_limit: 512m`, `restart: unless-stopped`.
  - `api`: `build: context .`, `dockerfile: backend/Dockerfile`(`python:3.12-slim`, `backend/app/`와 **`data/`를 이미지에 굽는다** — 볼륨 마운트 아님, 롤백 때 데이터도 함께 되돌아감). 환경 `NEO4J_URI=bolt://neo4j:7687`·`NEO4J_USER`·`NEO4J_PASSWORD`. `mem_limit: 192m`. 컨테이너 내부 uvicorn `0.0.0.0:8000`(호스트 미노출).
  - `nginx`: `build: nginx/Dockerfile`(다단계 — `node:24-alpine`에서 `npm ci`·`npm run build` 후 `nginx:alpine`에 `nginx.conf`와 `dist`를 굽는다). 포트 `127.0.0.1:${TAEBRO_HTTP_PORT}:80`. `mem_limit: 64m`. `nginx.conf`는 gzip(`gzip_proxied any`, `gzip_comp_level 5`)과 `location = /health` → `http://api:8000/health` 프록시를 둔다.
  - 명명 볼륨 `neo4j_data`. `.dockerignore`가 `.git`·`.forge`·`.claude`·`node_modules`·`frontend/dist`·`scripts`·`.env`를 빌드 컨텍스트에서 뺀다.
- 헬스: `backend/app/main.py`의 `GET /health` — Neo4j `verify_connectivity()` 성공 시 `{"app":"biblemap","neo4j":"ok"}`, 실패 시 503 `{"neo4j":"fail"}`. compose 레벨 `healthcheck`는 없다(배포 스크립트가 이 경로를 폴링).
- `deploy/taebro.env` — taebro-infra 계약 v5 4절 선언(비밀 아님): `HEALTH_PATH=/health`·`HEALTH_EXPECT=biblemap`·`HEALTH_TIMEOUT=180`·`BUILD_SERVICES=api nginx`.

## 배포 파이프라인

- `.github/workflows/deploy.yml`: `on: push`(`branches: [main, dev]`, `paths-ignore: ['.forge/**','**/*.md']`)·`workflow_dispatch`, `concurrency: deploy-<ref>`, `runs-on: [self-hosted, ARM64]`. 스텝 3개 — `actions/checkout@v4` → `deploy/pre-deploy.sh <prod|dev>` → `~/runtime/taebro-infra/bin/deploy biblemap <prod|dev>`(main=prod, 그 외=dev). PR 계열 트리거는 일부러 없다. 옛 `deploy.sh`(루트)는 삭제됐다.
- `deploy/pre-deploy.sh <prod|dev>`(ADR `260801-195022`의 순서 유지 — 주입은 멱등이므로 검증 **앞**): 실행 자리 `~/runtime/biblemap/<env>/.env`를 로드(없으면 실패)하고 `NEO4J_URI=bolt://localhost:${NEO4J_BOLT_PORT}`로 export한 뒤 ① `frontend`에서 `npm ci --silent` ② `python3 backend/scripts/inject_ko_names.py`·`inject_date_corrections.py`(해당 env의 Neo4j) ③ `CHECK_STRICT=1 bash scripts/check.sh`. 프론트 빌드·이미지 빌드·컨테이너 교체는 이 스크립트 몫이 아니라 `bin/deploy`(taebro-infra)가 `BUILD_SERVICES`로 한다.
- 호스트 python3 실행 경로: 주입 2종과 check.sh 검증기는 러너 호스트의 python3(컨테이너 밖)로 돈다. `load_*` 적재 스크립트는 배포가 실행하지 않는다 — 그래프 적재는 별도 수동.
- 배포 전 검증 게이트 `scripts/check.sh`(AI 불요, 단독 실행 가능, `set -u`):
  - 파일 기반 데이터 검증 **22종**(task#259/#274/#277~286)을 `python3 -m backend.scripts.validate_<name>`으로 실행: `covenants`, `messianic_prophecies`, `parables_miracles`, `topical_verses`, `pm_map_coverage`, `scene_coverage`, `chapter_sections`, `chapter_summaries`, `quotations`, `person_context`, `god_reliance`, `traits`, `era_bands_consistency`, `approx_book_verses`, `intro_menu_parity`, `curated_persons`, `intro_gutter`, `intro_entry_route`, `event_verses`, `sortkey_startdate`, `api_cache_headers`(신규 — 라우트 `max-age ≤ 300` 경계), `scene_sketch_detail`(신규 — 장면 스케치 저작 규약 B1~B6. 규약 정본은 `frontend/src/sketches/lib.jsx`의 주석이고, 검증기는 `--dur-draw`(`index.css`)·패널 대기(`tourSketches.jsx`)·`stepDuration` 공식(`useTourPlayback.js`)을 **소스에서 파생**한다 — 상수를 복사해 두면 타이밍이 바뀔 때 게이트가 조용히 거짓 초록이 된다). 이어서 대조군(자기 검사가 고의 드리프트 주입에 실제로 FAIL하는지 확인, 회고 `260820-003946`) **10종**을 `--selftest`로 순회: `intro_menu_parity`, `curated_persons`, `intro_gutter`, `intro_entry_route`, `event_verses`, `sortkey_startdate`, `era_bands_consistency`, `api_cache_headers`(신규), `scene_sketch_detail`(신규 — B1~B6 각각을 개별 주입해 6건 모두 빨강인지), `scene_coverage`(신규 — A~G 7클래스를 개별 주입하고, 특히 미저작(A)과 미연결(D/E)이 **다른 메시지**로 갈리는지 단언).
  - 브라우저 없이 도는 소스 불변식 2건(신규, `backend.scripts` 밖의 `scripts/` 직호출): `check_cast_axes.py`(`sketches/cast/*.jsx` 5축 — 머리카락·수염·머리쓰개·나이대·성별 — 조합이 서로 겹치지 않는지), `check_mask_ranges.py`(+`--selftest`, `GoliathScene` 영역 마스크 delay 범위가 연속하고 겹치지 않는지. `scripts/canon/make_masks.py`가 같은 모듈의 `derive_ranges()`를 그대로 가져다 쓴다).
  - 저작 파이프라인 정본 단일화 가드(신규, task#316): `validate_canon_pipeline.py`가 두 축을 **소스만 읽어** 판정한다(GPU도 생성 venv도 없는 환경에서 돌기 때문에 파이프라인 실행형은 애초에 성립하지 않는다). 축1 — `scripts/canon/params.py`를 AST로 파싱해 정본 키 집합을 **파생**하고(손으로 적은 목록이 아니다), 그 이름이 같은 디렉터리 다른 `.py`에서 모듈 레벨로 재대입되면 FAIL. 튜플 대입(`STEPS, GUIDANCE = 30, 6.5`)도 잡고, `repo/name` 형태의 모델 ID는 **값으로도** 본다(이름만 바꾼 복사본 차단). 수치는 값 축에서 의도적으로 제외(오탐). 축2 — `scripts/` 아래 미추적 파일 0건. 위생이 아니라 필요 때문이다: check.sh가 부르는 `check_cast_axes.py`·`check_mask_ranges.py`가 미추적이면 새 클론·CI에서 **게이트 자신이 깨진다**. `--selftest`가 두 축 각각에 고의 위반을 임시 스캔 루트(`.forge/.canon-gate-selftest`)에 주입해 검출을 확인하고 원복한다(실제 `scripts/canon/`은 건드리지 않는다). git 미가용 시 skip 계약(전용 종료코드 3)은 아래 forge 문서 가드와 같다.
  - 영구 forge 문서 추적 가드(신규, task#279 S4): `validate_forge_docs_tracked.py`가 `.forge/adr`·`.forge/retro` 아래 미추적(untracked, gitignore 제외) 파일이 0건인지 `git ls-files --others --exclude-standard`로 확인 — 위 22종 데이터 검증 루프와 별개 섹션. git 작업트리가 아니면(`git rev-parse --is-inside-work-tree` 실패) 본검사·`--selftest` 둘 다 스킵-경고. 표준 배포 전환(task#341) 뒤 배포는 러너의 깨끗한 `actions/checkout`에서 돌므로 미추적 파일이 없어 배포 경로에서는 늘 통과한다 — 실제로 잡는 곳은 작업 폴더의 push 전 단독 실행이다.
  - 프론트 검증: `frontend/node_modules` 있으면 `npx --no-install eslint src` + `npm test --silent`(= `vitest run`) 실행, 없으면 둘 다 스킵-경고.
  - 연대 정합: `127.0.0.1:${NEO4J_BOLT_PORT:-7687}` 소켓 접속되면 `validate_event_chronology` 실행, 아니면 스킵-경고. 이때 루트 `.env` 로드 후 `NEO4J_URI`/`NEO4J_USER` 기본값을 채워 넘긴다.
  - `CHECK_STRICT=1`(task#259)이면 위 스킵-경고(ESLint/vitest 부재, Neo4j 미기동, git 미가용)가 실패로 승격된다(`skip()` 헬퍼). `deploy/pre-deploy.sh`는 항상 이 모드로 호출하고, 단독 개발 실행(`bash scripts/check.sh`, Neo4j 없이 파일 검증만)은 기본값(스킵 허용)을 유지.
  - 하드 항목 하나라도 실패하면 실패 항목 tail 8줄 출력 후 `exit 1`.
  - `backend/scripts/validate_era_bands_consistency.py`는 시대 경계 결합점 **7축**(task#255 S1, task#284에서 3축 추가)을 정합 단언한다: ① `frontend/src/eraBands.js`의 `ERA_BANDS` ② `backend/app/routes/stats.py`의 `ERA_BANDS` ③ `backend/app/curated.py`의 `ERA_ORDER`(순서만) ④ `data/covenants/covenants.json`의 각 언약 `era` ⑤ `data/tours/*.json`의 각 투어 `era`(신규) ⑥ `frontend/src/PersonHub.jsx`의 `ERA_ORDER` 사본(신규, `curated.py`와 이름·순서 모두 대조) ⑦ `frontend/src/**/*.{jsx,js}`에서 `===` 직전 식별자 사슬에 `era`/`Era` 토큰이 있는 문자열 리터럴 비교 전부(신규 — 정규식 스크래핑, 파일 허용목록이 아니라 식별자-사슬 클래스로 오탐 경계를 좁힘). 각 축은 몇 항목을 보았는지 출력하고 0건이면 실패(공허한 통과 방지).
- 실행 자리는 env별(`~/runtime/biblemap/prod`·`dev`)이고 포트가 갈린다(prod Bolt 7687, dev 7688). 데이터(`data/`)가 이미지에 구워지므로 데이터만 바뀌어도 재배포(push)가 필요하다 — 옛 「`restart api`로 `lru_cache` 비우기」 경로는 더는 반영되지 않는다.

## 데이터 자산(`data/`, 전량 git 추적)

런타임이 읽는 정본 JSON은 전부 레포에 커밋된다. 디렉터리 31개 + 루트 파일 2개(`data/word_distribution.json` ~284KB, `data/word_sentiment.json` ~22KB). 큰 자산: `data/bible/verses.json` ~9.8MB(정본 절 사전), `data/word_verse_index/index.json` ~1.6MB, `data/verse_persons/index.json` ~837KB. 다건 디렉터리: `data/person_events/`(35), `data/god_reliance/`(33), `data/tours/`(9), `data/names_ko/`(5). 이전 매핑 시점에 미커밋이던 `data/covenants/`·`data/messianic_prophecies/`·`data/jesus_parables_miracles/`·`data/topical_verses/`는 현재 모두 커밋 완료.

## AGE 호환성 점검 하네스 (`scripts/age_compat/`) — 앱 스택 밖 일회용
- 의존성은 `scripts/age_compat/requirements.txt`(`neo4j==6.2.0`·`fastapi==0.136.3`·`httpx`·`psycopg[binary]==3.3.6`)로 별도 고정. 앱 `backend/requirements.txt`에는 `psycopg`가 들어가지 않는다.
- 진입점 `run_check.py`가 `scripts/age_compat/docker-compose.yml`을 올려(`-p biblemap-agecheck`) 점검 후 `down -v`까지 소유. Apache AGE 어댑터는 `age_adapter.py`, 결과는 `REPORT.md`(판정: 막힘). 판정에 따라 그래프 DB는 neo4j 유지(`.forge/adr/261010-110220-keep-neo4j-as-standard-db-exception.md`).
