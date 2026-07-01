---
last_mapped_commit: 0189ad9fb964e5eb4fcc91776b3202f7014058dd
mapped: 2026-07-02
---

# INTEGRATIONS

BibleMap의 외부 의존은 모두 단순하다: 자체 Neo4j(Bolt), 빌드/시드 타임에만 호출하는 두 외부 데이터 소스(GitHub raw의 Theographic 데이터셋, getbible.net 절 본문), 프론트가 런타임에 부르는 지도 타일/폰트 CDN, 그리고 배포 경로(Cloudflare Tunnel + GitHub Actions self-hosted runner). 런타임 백엔드는 외부 API를 호출하지 않는다.

## Neo4j (Bolt)

- **프로토콜/주소**: Bolt. 백엔드 컨테이너는 `bolt://neo4j:7687`(compose 내부 DNS, `docker-compose.yml`의 `api` 서비스 env). 드라이버 기본값은 `bolt://localhost:7687`(`backend/app/db.py`, `backend/scripts/*.py`).
- **인증**: `NEO4J_USER`/`NEO4J_PASSWORD` 환경변수. compose가 `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}`로 DB 측 인증을 파생.
- **드라이버**: 공식 `neo4j` Python 패키지(`GraphDatabase.driver`). 백엔드는 `backend/app/db.py`에서 전역 싱글턴.
- **노출**: 포트 `7474`/`7687`은 `127.0.0.1`에만 바인딩 — 구조적으로 외부 비노출(터널은 API만 가리킴).
- **호스트 직접 접근**: `backend/scripts/`의 적재/주입 스크립트는 호스트에서 `bolt://localhost:7687`로 직접 쓴다(예: `deploy.sh` [4/4]에서 `backend/scripts/inject_ko_names.py`).

## Theographic Bible Metadata (GitHub raw, 빌드/시드 타임)

- **소스**: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/{people,places,events,peopleGroups,books,verses}.json`.
- **호출처**: 표준 라이브러리 `urllib.request`로 다운로드. 사용하는 스크립트:
  - `backend/scripts/load_theographic.py` — people/places/events/peopleGroups를 Neo4j에 적재하고 `theographic_id` 인덱스 생성.
  - `backend/scripts/generate_book_context.py`(books), `backend/scripts/generate_event_verses.py`(events·verses), `backend/scripts/generate_person_traits.py`(people·events), `backend/scripts/generate_verse_events.py`(books·events·verses) 등 `generate_*` 스크립트.
- **타이밍**: 빌드/시드 시점에만. 런타임 백엔드는 호출하지 않음(결과는 Neo4j 또는 `data/` JSON에 영속).

## getbible.net (절 본문, 빌드 타임 pre-bake)

- **엔드포인트**: `https://api.getbible.net/v2/{slug}/{book_order}/{chapter}.json` (slug = 번역본; 한국어 `korean`, 영어 `kjv`).
- **호출처**: `backend/scripts/generate_verse_text.py`(주 pre-bake)와 `backend/scripts/generate_person_event_verses.py`. 둘 다 `urllib.request` 사용.
- **방식/주의점**:
  - 빌드타임에 절 본문을 받아 `data/` JSON(`event_verses/events.json`, `book_context/books.json`, `character_traits/people.json`, `place_context/places.json`)에 `textKo`/`textEn`(또는 `keyVerseText*`) 필드로 인라인 저장 → **런타임 외부 호출 제거**(ADR-0003).
  - (slug, book, chapter)당 1회만 fetch·캐시(멱등). 이미 본문 있는 항목 스킵, 실패는 `null` 기록 후 재시도 가능.
  - getbible는 기본 `Python-urllib` UA에 403을 주므로 브라우저류 UA(`Mozilla/5.0 (compatible; BibleMap-build/1.0)`)로 요청(`backend/scripts/generate_verse_text.py` 주석, 2026-06-15 retro 교훈).

## 지도 타일·폰트 CDN (프론트 런타임)

`frontend/src/MapView.jsx`의 MapLibre 스타일에서 직접 참조하는 외부 호스트:

- **베이스맵 래스터 타일**: Esri ArcGIS `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` (raster, tileSize 256).
- **글리프(폰트)**: Protomaps `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`.

(API 키 불필요한 공개 엔드포인트. 별도 인증 없음.)

## 인증

- 사용자 인증/세션/토큰 없음. 백엔드는 GET 전용·`allow_origins=["*"]` CORS(`backend/app/main.py`). 유일한 시크릿은 Neo4j 비밀번호(`NEO4J_PASSWORD`, 호스트 `.env`).

## Cloudflare Tunnel (`biblemap.taebro.com`)

- **노출 도메인**: `https://biblemap.taebro.com`. cloudflared가 outbound로만 연결하므로 호스트에 인바운드 포트를 열지 않음.
- **구성**(`BIBLEMAP_PLAN.md` §3.4): 기존 호스트 cloudflared 터널(상시 구동)에 public hostname만 추가. `~/.cloudflared/config.yml`의 `ingress`에 `biblemap.taebro.com → http://localhost:<포트>` 규칙 추가 + `cloudflared tunnel route dns`로 DNS 등록. 별도 launchd 불필요. Neo4j는 ingress에 없어 구조적으로 차단.
- 주의: 플랜 문서(§3.4)는 cloudflared가 api 포트(8000)를 직접 가리키는 토폴로지를 기술하나, 현재 `docker-compose.yml`은 `api` 포트를 publish하지 않고 nginx(`8080`)만 publish한다. 실제 터널이 가리키는 호스트 포트는 호스트 측 `~/.cloudflared/config.yml`에 있으며 저장소 내 파일로는 확정 불가(`.cloudflared` 설정은 저장소 밖).

## GitHub Actions self-hosted runner → deploy.sh

- **워크플로우**: `.github/workflows/deploy.yml`. `push`가 `main`에 들어오면 `runs-on: self-hosted` 잡이 `cd /Users/calmonion/Project/BibleMap` → `git fetch origin` → `git reset --hard origin/main` → `bash deploy.sh` 실행.
- **`deploy.sh` 단계**:
  1. lock 파일(`/tmp/biblemap-deploy.lock`)로 동시 실행 차단, 로그 `~/Library/Logs/com.biblemap.deploy.log`.
  2. macOS 키체인 우회: 임시 `DOCKER_CONFIG`(빈 auths)를 만들고 `~/.docker/cli-plugins`를 심볼릭 링크해 `docker compose` 플러그인 인식(CI 환경 footgun 회피).
  3. 호스트 `.env`에서 `NEO4J_PASSWORD` 로드(호스트 직접 실행하는 주입 스크립트와 비번 일치).
  4. `[1/4]` 프론트 빌드(`cd frontend && npm install && npm run build` → `frontend/dist/`).
  5. `[2/4]` `docker compose -p biblemap build api`.
  6. `[3/4]` `docker compose -p biblemap up -d api nginx`.
  7. `[4/4]` `python3 backend/scripts/inject_ko_names.py`를 Neo4j 준비될 때까지 최대 15회(2초 간격) 재시도; 끝내 실패하면 `exit 1`로 배포 중단.
- 러너 격리 주의(글로벌 메모리): self-hosted 러너는 레포 전용 디렉터리/서비스로 격리해야 하며, 배포 무음 실패 시 폴러보다 러너 상태를 먼저 의심.
