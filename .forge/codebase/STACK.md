---
last_mapped_commit: 4ad1d837a3771f69f53877b128938124b68d920b
mapped: 2026-08-21
---

# STACK

BibleMap의 언어·런타임·프레임워크·의존성·빌드/설정 사실 정리. 도메인 용어 정의는 여기 없음(그건 `CONTEXT.md`). 파일별 디렉터리 구조는 `.forge/codebase/STRUCTURE.md` 참고.

전체 구성: 백엔드 FastAPI + Neo4j Python 드라이버, 프론트 React + Vite + maplibre-gl, docker-compose 3서비스 스택(neo4j + api + nginx), self-hosted 러너 배포(배포 전 `scripts/check.sh` 게이트).

## 백엔드

- 언어/런타임: Python. 컨테이너 베이스는 `python:3.12-slim`(`backend/Dockerfile`). 반면 `deploy.sh`가 호스트에서 직접 실행하는 주입 스크립트(`backend/scripts/inject_ko_names.py`)와 `scripts/check.sh`의 검증 스크립트들은 이 머신의 host python3(현재 `Python 3.14.5`)로 돈다 — 컨테이너 밖 실행 경로가 상시 존재한다. 레포 루트 `scripts/uat_intro_entry.py`·`scripts/uat_intro_gutter.py`(신규)도 같은 host python3로 돌지만 `scripts/check.sh` 게이트에는 배선되지 않는다(각 스크립트 docstring에 사유 명시 — `deploy.sh`가 프론트 빌드 **전**에 check.sh를 부르므로 그 시점 `:8080`은 옛 빌드를 서빙해 게이트에 넣으면 초록·빨강이 둘 다 거짓이 된다). 사람이 배포 전후로 직접 호출하는 실측 UAT다.
- `playwright`(호스트 python에만 설치, 현재 `1.60.0`) — 위 두 UAT 스크립트가 `playwright.sync_api.sync_playwright`로 헤드리스 브라우저를 띄워 `localhost:8080`을 실측(`anthropic`과 동일하게 `backend/requirements.txt`에는 없음, API 이미지 미포함).
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
- 라우트 모듈: `backend/app/routes/*.py` 15개(`__init__.py` 포함, 신규 `timeline.py` 추가). `@router.get` 기준 **32개 GET 엔드포인트**(POST/PUT/DELETE 없음, `/timeline/canon`·`/place/{place_id}` 신규). 응답은 대부분 `JSONResponse` + `Cache-Control` 헤더(`max-age=300` 또는 `public, max-age=3600`, 예외로 `books.py`의 `/books-overview`는 `no-store`). 집계형 계산은 `lru_cache`(대부분 `maxsize=1`, 일부 `maxsize=66/256/2048/None`)로 프로세스 내 캐시 → **데이터 변경 시 API 재시작 필요**.
- 데이터/스크립트: `backend/scripts/*.py` 53개(+6). 접두사별 — `load_*` 8(Neo4j 적재), `generate_*` 11(오버레이 생성), `inject_*` 6(Neo4j 속성 주입), `validate_*` 22(검증, 신규 6종 전부 이번 구간 추가: `validate_curated_persons.py`·`validate_event_verses.py`·`validate_forge_docs_tracked.py`·`validate_intro_entry_route.py`·`validate_intro_gutter.py`·`validate_sortkey_startdate.py`), `build_*` 3(색인 빌드), `apply_*` 1(`apply_event_dedupe.py`). 앱 코드는 이 스크립트를 import하지 않는다(빌드타임/운영 전용 경계) — 예외 1건: `validate_event_verses.py`가 `generate_person_event_verses.py`의 `expand_range_label`/`verse_keys_by_book`을 import해 생성기와 같은 파서·오라클을 재사용한다(스크립트 간 import, 앱 경계와는 무관).
  - `backend/scripts/generate_person_event_verses.py`(task#282, ADR `260821-125000`) — 근거 절 범위 전개가 getbible 실시간 fetch에서 오프라인 판정으로 전환됨. `expand_range_label()`/`verses_for_label()`이 정본 절 사전(`data/bible/verses.json`)의 verseID 키 존재만으로 라벨이 가리키는 범위를 전개(네트워크 호출 0회) — 교차-장·장 단위 범위를 첫 절 1개만 베이킹하던 결함(실측 12건)을 없앤다. 기존 `fetch_chapter`/`fetch_verses`(getbible 호출부)는 새 경로에서 더는 호출되지 않는 죽은 코드로 남아 있다(수술적 범위 결정 — ADR이 명시, 걷어내지 않음). `--rebake [--dry-run]` 플래그로 기존 `event_verses/events.json` 블록을 새 오라클로 재전개하는 `rebake_range_labels()`도 이번에 추가.

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
- 엔트리: `frontend/index.html`(`#root`, `/src/main.jsx` 모듈 스크립트, `<title>BibleMap</title>`, favicon `/favicon.svg?v=2`) → `frontend/src/main.jsx` → `frontend/src/App.jsx`. 최상위 뷰는 `frontend/src/*.jsx` 다수(`MapView`, `TimelineView`, `PersonHub`, `StatsView`, `IntroView`, `BibleOverviewView`, `TopicalVersesView`, `SidePanel` 등). 장면 스케치는 `frontend/src/sketches/`(11개: `lib.jsx`·`SceneLabel.jsx` + 시대별 9개).
- API 클라이언트: `frontend/src/api.js` — 단일 `apiGet(path, {signal})`. `API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'`. 모든 요청 URL에 `?v=<__BUILD_ID__>` 부착, 비-OK 응답은 `err.status`를 실은 `Error`로 reject, `AbortError`는 그대로 전파.
- 폰트: 외부 CDN 아님. `frontend/public/fonts/im-fell-english-latin.woff2`를 `frontend/src/index.css`의 `@font-face`가 `/fonts/...`로 셀프호스팅(라이선스 `frontend/public/fonts/IM-Fell-English-OFL.txt`).

## 빌드 / 번들링

- Vite 설정(`frontend/vite.config.js`):
  - `plugins: [react()]`
  - `define.__BUILD_ID__ = JSON.stringify(String(Date.now()))` — 빌드마다 바뀌는 식별자. `frontend/src/api.js`가 캐시버스터로 사용해 배포 직후 `max-age` 응답 캐시를 무력화(같은 배포 안에서는 값 고정 → 캐시 이점 유지).
  - `build.rollupOptions.output.manualChunks`: `node_modules` 중 `maplibre-gl`은 `maplibre` 청크, 나머지는 `vendor` 청크.
- 지연 로딩(코드 분할): `frontend/src/IntroView.jsx`와 `frontend/src/TourPlayback.jsx`가 `lazy(() => import('./tourSketches'))` + `<Suspense>`로 스케치 번들을 분리 → 별도 `tourSketches-*.js` 청크.
- 산출물: `frontend/dist/`(gitignore 대상, nginx가 마운트로 서빙). 관측된 청크 — `index-*.js`(~251KB), `vendor-*.js`(~198KB), `maplibre-*.js`(~1.0MB), `tourSketches-*.js`(~391KB), `rolldown-runtime-*.js`, `index-*.css`/`maplibre-*.css`. **HMR이 아니라 마운트 서빙이므로 로컬 검증 전 `cd frontend && npm run build` 필요.**
- ESLint(`frontend/eslint.config.js`, flat config): `defineConfig([globalIgnores(['dist']), {...}])` — `js.configs.recommended` + `reactHooks.configs.flat.recommended` + `reactRefresh.configs.vite`. `files: ['**/*.{js,jsx}']`, `globals.browser` + `__BUILD_ID__: 'readonly'`, JSX 파서 옵션.
- 백엔드 이미지 빌드: `backend/Dockerfile` — `python:3.12-slim` → `COPY requirements.txt` → `pip install --no-cache-dir -r requirements.txt` → `COPY app/ ./app/` → `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`. `data/`와 `backend/scripts/`는 이미지에 복사되지 않는다(데이터는 볼륨 마운트, 스크립트는 호스트 실행).

## 설정 파일 (git 추적)

- 루트: `docker-compose.yml`, `deploy.sh`, `.env.example`, `.gitignore`, `README.md`, `CLAUDE.md`, `BIBLEMAP_PLAN.md`
- 백엔드: `backend/Dockerfile`, `backend/requirements.txt`
- 프론트: `frontend/package.json`, `frontend/package-lock.json`, `frontend/vite.config.js`, `frontend/eslint.config.js`, `frontend/index.html`, `frontend/.env.production`, `frontend/.gitignore`, `frontend/README.md`
- 인프라/CI: `nginx/nginx.conf`, `.github/workflows/deploy.yml`, `scripts/check.sh`, `scripts/uat_intro_entry.py`(신규), `scripts/uat_intro_gutter.py`(신규) — 뒤 둘은 CI 게이트 미배선, 사람이 배포 전후 수동 실행하는 Playwright UAT.
- 에이전트 도구 설정: `.claude/settings.json`(내용은 `{"worktree":{"bgIsolation":"none"}}`), `.claude/launch.json`, `.claude/agents/*.md` 5개(`data-author`, `frontend-dev`, `line-artist`, `scripture-reviewer`, `ui-verifier`)
- gitignore 대상: `frontend/node_modules/`, `frontend/dist/`, `.env`, `__pycache__/`, `.venv/` + forge 휘발 상태(`.forge/backlog|done|executed|quick`, `plan.md`, `run.md`, `STATUS.md`, `loop.md`, `ask.md`(신규), `reports/`(신규), `scratch/`(신규)). `.forge/CONTEXT.md`·`adr/`·`retro/`·`codebase/`는 화이트리스트로 추적.

## 환경변수 (이름만 — 값은 이 문서에 절대 기재하지 않음)

| 이름 | 사용처 | 비고 |
| --- | --- | --- |
| `NEO4J_PASSWORD` | 루트 `.env` → `docker-compose.yml`(neo4j·api), `backend/app/db.py`, `backend/scripts/*`(호스트 실행), `scripts/check.sh` | 유일한 필수 비밀. compose가 `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}`로 파생하며 `:?` 확장이라 미설정 시 compose 실패 |
| `NEO4J_URI` | `backend/app/db.py`, 적재/주입 스크립트 | compose가 api에 `bolt://neo4j:7687` 주입. 호스트 실행 시 기본 `bolt://localhost:7687` |
| `NEO4J_USER` | 동상 | 기본 `neo4j` |
| `DATA_DIR` | `backend/app/overlays.py` | 기본 `/app/data`. 미해석 시 레포 `data/`로 폴백 |
| `ANTHROPIC_API_KEY` | `backend/scripts/generate_book_context.py`, `generate_book_events.py`, `generate_person_context.py`, `generate_person_traits.py`, `generate_verse_events.py` | **빌드타임 생성 스크립트 전용**. 런타임 API·컨테이너는 사용하지 않음 |
| `VITE_API_URL` | `frontend/src/api.js`(`import.meta.env`) | `frontend/.env.production`에서 `/api`로 고정(빌드타임 주입). 개발 기본값은 `http://localhost:8000` |
| `DOCKER_CONFIG` | `deploy.sh`가 임시 디렉터리로 export | macOS 키체인 우회용(빈 `auths` + `~/.docker/cli-plugins` 심링크) |
| `CHECK_STRICT` | `scripts/check.sh`(신규) | `1`이면 ESLint/vitest 부재·Neo4j 미기동 스킵-경고를 실패로 승격. `deploy.sh`가 항상 `1`로 호출 |

- `import.meta.env.DEV`도 프론트에서 사용(Vite 기본 제공, 별도 설정 없음).

## Docker / 배포 스택

- `docker-compose.yml` — 3 서비스:
  - `neo4j`: 이미지 `neo4j:5`. 포트 `127.0.0.1:7474`(HTTP)·`127.0.0.1:7687`(Bolt) 루프백 바인딩. 볼륨 `neo4j_data:/data`. 환경 `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD:?...}`. `restart: unless-stopped`.
  - `api`: `build: ./backend`. 환경 `NEO4J_URI=bolt://neo4j:7687`, `NEO4J_USER=neo4j`, `NEO4J_PASSWORD=${NEO4J_PASSWORD:?...}`. 볼륨 `./data:/app/data`(데이터는 볼륨 마운트, 이미지 미포함). `depends_on: neo4j`. 컨테이너 내부 uvicorn `0.0.0.0:8000`(호스트 미노출).
  - `nginx`: 이미지 `nginx:alpine`. 포트 `8080:80`. 볼륨 `./frontend/dist:/usr/share/nginx/html:ro`, `./nginx/nginx.conf:/etc/nginx/nginx.conf:ro`. `depends_on: api`. `nginx.conf`에 gzip 신규 추가(`gzip on`, 대상 MIME `text/css`·`application/javascript`·`application/json`·`image/svg+xml` 등, `gzip_min_length 1024`, `gzip_proxied any`—`/api/*` 프록시 응답 포함, `gzip_comp_level 5`).
  - 명명 볼륨 `neo4j_data`. compose 프로젝트명은 `deploy.sh`가 `-p biblemap`으로 고정(compose 파일 자체에는 `name:` 없음).
- 헬스체크·리소스 제한·다단계 빌드 없음. 서비스 3개 모두 단일 compose 파일에 정의(오버라이드 파일 없음).

## 배포 파이프라인

- `.github/workflows/deploy.yml`: `on: push` (`branches: [main]`), `runs-on: self-hosted`, 단일 스텝 "Pull & Deploy" — `cd /Users/calmonion/Project/BibleMap && git fetch origin && git reset --hard origin/main && bash deploy.sh`. 체크아웃 액션조차 쓰지 않고 러너 로컬 클론을 직접 리셋한다.
- `deploy.sh`(레포 루트, 실행 권한 있음) — task#259/ADR `260801-195022`로 순서 재구성(주입은 멱등이므로 검증 **앞**에서 DB를 정본으로 되돌린 뒤 게이트가 판정):
  1. `/tmp/biblemap-deploy.lock`로 중복 배포 차단(`EXIT` 트랩으로 해제). 로그 `~/Library/Logs/com.biblemap.deploy.log`(`tee -a`).
  2. 임시 `DOCKER_CONFIG` 생성(빈 `auths`) + `~/.docker/cli-plugins` 심링크 — 이게 없으면 `docker compose` 서브커맨드를 못 찾는다(주석에 명시).
  3. 루트 `.env`를 `set -a`로 로드(호스트 실행 스크립트가 동일 비번 사용).
  4. `[1/7]` Neo4j 도달 대기 — `127.0.0.1:7687` 소켓 접속을 최대 15회(2초 간격) 재시도. 실패 시 배포 중단.
  5. `[2/7]` 데이터 주입(둘 다 멱등): `python3 backend/scripts/inject_ko_names.py` → `inject_date_corrections.py`. 실패를 대기 실패로 위장시키지 않도록 `2>/dev/null` 없이 실행.
  6. `[3/7]` `cd frontend && npm install --silent`.
  7. `[4/7]` **검증 게이트**: `CHECK_STRICT=1 bash scripts/check.sh` — `PIPESTATUS[0]` 비0이면 배포 중단(`exit 1`). `CHECK_STRICT=1`이 스킵-경고 항목(ESLint·Neo4j 연대 정합)을 실패로 승격시킨다.
  8. `[5/7]` 프론트 빌드: `npm run build --silent`.
  9. `[6/7]` `docker compose -p biblemap build api`.
  10. `[7/7]` 컨테이너 재시작: `docker compose -p biblemap up -d api` 후 `up -d --force-recreate nginx`(task#263 — nginx는 이미지 빌드도 바인드 마운트 스펙 변경도 없어 `nginx.conf`만 바뀌면 Compose가 재생성 필요를 못 알아채 no-op되므로 매 배포 강제 재생성).
  - 주의: `deploy.sh`는 `load_*` 적재 스크립트를 실행하지 않는다 — Neo4j 그래프 적재는 별도 수동 실행.
- 배포 전 검증 게이트 `scripts/check.sh`(AI 불요, 단독 실행 가능, `set -u`):
  - 파일 기반 데이터 검증 **20종**(task#259/#274/#277~284)을 `python3 -m backend.scripts.validate_<name>`으로 실행: `covenants`, `messianic_prophecies`, `parables_miracles`, `topical_verses`, `pm_map_coverage`, `scene_coverage`, `chapter_sections`, `chapter_summaries`, `quotations`, `person_context`, `god_reliance`, `traits`, `era_bands_consistency`, `approx_book_verses`, `intro_menu_parity`, `curated_persons`(신규), `intro_gutter`(신규), `intro_entry_route`(신규), `event_verses`(신규), `sortkey_startdate`(신규). 이어서 대조군(자기 검사가 고의 드리프트 주입에 실제로 FAIL하는지 확인, 회고 `260820-003946`) 7종을 `--selftest`로 순회: `intro_menu_parity`, `curated_persons`(신규), `intro_gutter`(신규), `intro_entry_route`(신규), `event_verses`(신규), `sortkey_startdate`(신규), `era_bands_consistency`(신규 — 이전엔 대조군이 없었다).
  - 영구 forge 문서 추적 가드(신규, task#279 S4): `validate_forge_docs_tracked.py`가 `.forge/adr`·`.forge/retro` 아래 미추적(untracked, gitignore 제외) 파일이 0건인지 `git ls-files --others --exclude-standard`로 확인 — 위 20종 데이터 검증 루프와 별개 섹션. git 작업트리가 아니면(`git rev-parse --is-inside-work-tree` 실패) 본검사·`--selftest` 둘 다 스킵-경고. **배포 경로에서도 살아 있는 하드 게이트다** — `.github/workflows/deploy.yml`이 개발 트리와 같은 디렉터리에서 `git reset --hard`(추적 파일만 되돌리고 미추적은 남김) 후 `deploy.sh`를 부르므로, 미추적 영구 문서가 있으면 `CHECK_STRICT=1` 경로에서 배포가 중단된다.
  - 프론트 검증: `frontend/node_modules` 있으면 `npx --no-install eslint src` + `npm test --silent`(= `vitest run`) 실행, 없으면 둘 다 스킵-경고.
  - 연대 정합: `127.0.0.1:7687` 소켓 접속되면 `validate_event_chronology` 실행, 아니면 스킵-경고. 이때 루트 `.env` 로드 후 `NEO4J_URI`/`NEO4J_USER` 기본값을 채워 넘긴다.
  - `CHECK_STRICT=1`(task#259)이면 위 스킵-경고(ESLint/vitest 부재, Neo4j 미기동, git 미가용)가 실패로 승격된다(`skip()` 헬퍼). `deploy.sh`는 항상 이 모드로 호출하고, 단독 개발 실행(`bash scripts/check.sh`, Neo4j 없이 파일 검증만)은 기본값(스킵 허용)을 유지.
  - 하드 항목 하나라도 실패하면 실패 항목 tail 8줄 출력 후 `exit 1`.
  - `backend/scripts/validate_era_bands_consistency.py`는 시대 경계 결합점 **7축**(task#255 S1, task#284에서 3축 추가)을 정합 단언한다: ① `frontend/src/eraBands.js`의 `ERA_BANDS` ② `backend/app/routes/stats.py`의 `ERA_BANDS` ③ `backend/app/curated.py`의 `ERA_ORDER`(순서만) ④ `data/covenants/covenants.json`의 각 언약 `era` ⑤ `data/tours/*.json`의 각 투어 `era`(신규) ⑥ `frontend/src/PersonHub.jsx`의 `ERA_ORDER` 사본(신규, `curated.py`와 이름·순서 모두 대조) ⑦ `frontend/src/**/*.{jsx,js}`에서 `===` 직전 식별자 사슬에 `era`/`Era` 토큰이 있는 문자열 리터럴 비교 전부(신규 — 정규식 스크래핑, 파일 허용목록이 아니라 식별자-사슬 클래스로 오탐 경계를 좁힘). 각 축은 몇 항목을 보았는지 출력하고 0건이면 실패(공허한 통과 방지).
- 프로덕션 도메인은 이 머신 스택의 프록시 → `localhost:8080`이 곧 prod이고 동일 Neo4j를 본다. `data/`가 볼륨 마운트이므로 데이터만 바뀐 경우 `docker compose -p biblemap restart api`로 `lru_cache`만 비우면 반영된다.

## 데이터 자산(`data/`, 전량 git 추적)

런타임이 읽는 정본 JSON은 전부 레포에 커밋된다. 디렉터리 31개 + 루트 파일 2개(`data/word_distribution.json` ~284KB, `data/word_sentiment.json` ~22KB). 큰 자산: `data/bible/verses.json` ~9.8MB(정본 절 사전), `data/word_verse_index/index.json` ~1.6MB, `data/verse_persons/index.json` ~837KB. 다건 디렉터리: `data/person_events/`(35), `data/god_reliance/`(33), `data/tours/`(9), `data/names_ko/`(5). 이전 매핑 시점에 미커밋이던 `data/covenants/`·`data/messianic_prophecies/`·`data/jesus_parables_miracles/`·`data/topical_verses/`는 현재 모두 커밋 완료.
