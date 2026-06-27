---
last_mapped_commit: 14e0a78c3e0ab7fc7d960c4cabdf3eab3fc297e6
mapped: 2026-06-27
---

# ARCHITECTURE

## 전체 패턴

3-tier 웹앱이다. **React SPA 프론트엔드** ↔ **FastAPI 백엔드** ↔ **Neo4j 그래프 DB**. 정적 빌드(`frontend/dist`)와 API(`/api/`)는 nginx 한 프로세스가 서빙·프록시하고, 컨테이너 구성은 `docker-compose.yml`(`neo4j` / `api` / `nginx` 3 서비스)이다.

데이터는 두 갈래다.
1. **Neo4j** — 권위 그래프(인물/장소/사건/집단/책 노드와 관계). 런타임에 Cypher로 질의.
2. **런타임 JSON 오버레이** — `data/` 아래 JSON 파일. 백엔드가 메모리에 1회 로드(`lru_cache`)해 Neo4j 결과에 머지. 그래프에 없는 한글명·근거 구절·추정연도·책↔사건 매핑 등을 덧붙인다.

빌드 산출물 마운트 방식이라 HMR이 아니다 — 프론트 검증 전 `cd frontend && npm run build` 필요.

## 레이어 / 데이터 흐름

```
브라우저
  └ React SPA (frontend/src) ── fetch ──▶ nginx /api/ ──▶ FastAPI :8000 ──▶ Neo4j :7687
                                                                  └ data/*.json 오버레이(메모리 캐시)
```

프론트는 `apiGet`(단일 fetch 헬퍼, `frontend/src/api.js`) 하나로만 백엔드를 호출한다. 베이스 URL은 `import.meta.env.VITE_API_URL`(프로덕션 `/api`, 개발 기본 `http://localhost:8000`). 비-OK 응답은 status를 담은 Error로 reject, 취소는 `AbortError`로 전파해 호출부가 구분한다.

## 백엔드 (`backend/app`)

- **진입점 `main.py`** — `FastAPI(lifespan=...)`. lifespan에서 5개 라벨(`Person/Place/Event/PeopleGroup/Book`)에 `theographic_id` 인덱스를 멱등 생성(실패해도 계속). CORS는 GET만 허용. 라우터 4개(`nodes/events/search/books`)를 include.
- **`db.py`** — Neo4j 드라이버 싱글턴(`get_driver`, 전역 lazy). URI/USER/PASSWORD는 환경변수, 비밀번호 없으면 RuntimeError.
- **`overlays.py`** — `data/` JSON 로더. `_resolve`가 `DATA_DIR`(기본 `/app/data`) → 레포 `data/` 순으로 파일을 찾는다. `@lru_cache(maxsize=1)`로 노출하는 2개: `book_events_raw()`(`{bookId:[eventId]}`), `event_verses()`(사건별 근거 구절).
- **라우트 (`routes/`)**
  - `nodes.py` — `/node/{id}`(노드 본문 + 이웃을 단일 쿼리로 collect, 총수 동시 반환, `NODE_NEIGHBOR_LIMIT`=50; Book이면 `topPersons`/`topEvents` 추가, Person `traits`는 JSON 파싱), `/node/{id}/places`(라벨별로 다른 Cypher — Person/PeopleGroup/Book은 사건 경유 장소, Event/Place는 직접, `isPrimary` 플래그 부여, lat/lng 있는 Place만), `/node/{id}/neighbors/grouped`(타입별 그룹, 타입당 30개 상한 `MAX_NEIGHBORS_PER_TYPE` — MapView 사건 링이 소비), `/person/{id}/event-ids`.
  - `events.py` — `/events`(타임라인 전체 사건; Neo4j 사건 + `_load_approx_book_index`로 만든 역방향 `{eventId:[book]}` 추정책 머지, 둘 다 `lru_cache`), `/event/{id}/verses`(오버레이 그대로). 응답에 `Cache-Control: max-age=300`.
  - `search.py` — `/search?q=`(nameKo/name CONTAINS, 정확>접두>부분 rank 정렬, `SEARCH_LIMIT`=20 상한).
  - `books.py` — `/books-overview`(개요용 전체, no-store).
- **Cypher 패턴** — 모든 노드는 `theographic_id`로 식별. 라우트 핸들러가 `with driver.session()`을 열고 Cypher를 직접 실행(ORM 없음). 결과를 dict로 변환해 프론트 친화 형태로 정형화.

## 데이터 적재 스크립트 (`backend/scripts`)

런타임 경로 밖. 일회성/배치 실행으로 그래프를 채운다. 모두 `NEO4J_*` 환경변수로 직접 접속, MERGE 기반 멱등.

- **`load_theographic.py`** — 원천. theographic-bible-metadata(GitHub raw JSON)를 fetch해 Person/Place/Event/PeopleGroup 노드 + 관계(`PARENT_OF`/`CHILD_OF`/`SIBLING_OF`/`PARTNER_OF`/`MEMBER_OF`/`HAS_PARTICIPANT`/`OCCURS_AT`/`PART_OF`)를 배치 적재.
- **`load_*`** — `load_books`(Book 노드 + `CONTAINS_BOOK`), `load_authored_events`/`load_person_events`/`load_verse_events`(추가 Event + 선택적 CONTAINS_BOOK).
- **`inject_*`** — `data/` JSON을 읽어 기존 노드에 속성 SET: `inject_ko_names`(한글명), `inject_place_context`/`inject_book_context`(배경·키구절), `inject_person_traits`(traits).
- **`enrich_place_coords`** — Place 좌표 보강(기존값 보존).
- **`generate_*`** — `data/` 아래 JSON 오버레이를 생성하는 빌더(구절 텍스트·추정연도·책 이벤트 등).

## 프론트엔드 (`frontend/src`)

- **진입점** — `main.jsx`(StrictMode + `createRoot`) → `App.jsx`.
- **`App.jsx`** — 셸. 상단 네비(3 탭) + 검색박스 + 3 뷰(항상 마운트, CSS `display` 토글로 상태 보존) + 오버레이 패널(데스크톱 우측 슬라이드 / 모바일 하단 시트, `MOBILE_BREAKPOINT`=768로 분기). 검색 결과 선택 시 타입별 탭으로 이동(`Person/Place→map`, `Event→timeline`, `Book→overview`). 절 본문 언어(`verseLang`) 상태를 타임라인·SidePanel에 공유. `/` 키로 검색 포커스.
- **상태 훅** — `useNodeSelection.js`(선택 노드 + 히스토리 스택 + Person 이벤트 ID 집합 + `selectedNodeMeta`; `selectNode`는 `useCallback([])`로 참조 안정화 — selectedNode 변경이 MapView effect를 재실행해 fetch가 abort되는 버그 방지, 최신값은 `selectedNodeRef`로 읽음. `handleNodeLoaded` 콜백으로 SidePanel이 받은 노드 메타를 역수신해 중복 fetch 회피), `useSearch.js`(250ms 디바운스 검색 + AbortController 경쟁 차단 + 타입 필터/키보드 하이라이트).
- **3 뷰**
  - `MapView.jsx` — MapLibre GL 지도(아래 별도 절).
  - `TimelineView.jsx` — `/events` 기반 연대 타임라인. 사건 근거 구절 인라인 드릴다운(`/event/{id}/verses`, out-of-order 응답을 ref로 방어), bookFilter/personFilter 지원.
  - `BibleOverviewView.jsx` — `/books-overview` 기반 장르별 책 카드 그리드(구약 5 / 신약 5 장르 순서·한글 메타 하드코딩).
- **`SidePanel.jsx`** — 선택 노드 상세. `/node/{id}` 호출 → 노드 속성 + 타입별 그룹 이웃(`REL_KO` 관계 한글화) + 절 본문. `onNodeLoaded` 콜백으로 메타를 App에 역전달.
- **공유 모듈** — `theme.js`(타입→색/한글/순서 단일 팔레트, `SELECT_HL` 강조색), `constants.js`(`MOBILE_BREAKPOINT`/`SHEET_VH`), `convexHull.js`(Graham scan — Person hull 폴리곤용), `VerseLangTabs.jsx`(한/영 세그먼트 탭), `Spinner.jsx`.

## MapView 구조 (4-모듈 분리)

`MapView.jsx`(약 193줄)는 **컴포넌트 셸만** 담는다 — 지도 생성, effect 3개(초기화 / 선택반응 / `isVisible` 리사이즈), 에러·위치없음 안내 UI. 순수 로직과 명령형 지도 제어는 3개 형제 모듈로 분리됐다.

- **`mapGeo.js` — 순수 기하/GeoJSON/라벨 앵커 계산** (지도 인스턴스 비의존, `maplibregl`은 `LngLatBounds`에만 사용).
  - `coreBounds(places)` — outlier 제외 프레이밍 bounds(median 중심 거리 중앙값×3 임계, 제외 없거나 거의 한 점이면 `null` → 호출측이 전체 bounds로 폴백).
  - `outwardLabel(ex, ny)`(모듈 내부) / `ringLabels(lat, n)` / `placesToGeoJSON(places)` — 라벨을 이웃·링 중심 **반대(바깥)** 방향으로 미는 8방위 `text-anchor`+`text-offset` 계산(화면 세로는 `cos(lat)` 보정). `placesToGeoJSON`은 좌표를 소수점 4자리(`~1e-4°≈11m`)로 묶어 동일/근접 좌표 그룹을 만든 뒤(`frontend/src/mapGeo.js:45`), **단독 좌표**는 최근접 이웃 반대쪽으로 라벨을 밀고, **같은 좌표에 2개+가 겹친 그룹**은 마커를 한 점에 둔 채 `ringLabels`로 라벨만 방사형 분산한다(task-84 — 거리 0이면 `outwardLabel`이 같은 앵커로 퇴화해 라벨이 충돌·숨김되는 문제 회피). Feature 속성에 `id/label/isPrimary/anchor/offset`을 싣는다.
  - `easeOutCubic(t)` — 애니메이션 이징.
  - `ringPositions(lng, lat, n, R)` — 중심 주위 n개 균등 링 좌표.
  - `buildEventGeoJSON(events, positions, anchors)` / `buildSpiderGeoJSON(features, positions, anchors)` — 링/스파이더 프레임 GeoJSON 생성(스파이더는 원위치를 `originalLng/originalLat` 속성에 보존).
- **`mapLayers.js` — 정적 지도 설정 + 이벤트 등록 + 팝업**.
  - `EMPTY_GEOJSON` — 빈 FeatureCollection 상수(소스 초기화·클리어용).
  - `setupMapSources(map)` — 소스/레이어 일괄 등록: `hull-source`(Person 볼록껍질, 마커 아래 먼저), `places-source`(클러스터 on, `clusterMaxZoom:13`/`clusterRadius:18`/`clusterMinPoints:4` — `frontend/src/mapLayers.js:143`; `clusterRadius`는 마커 원이 실제 겹칠 때만 묶이도록 18(task-76 복원, 12~14 미만 금지), `clusterMinPoints:4`는 동일/근접 좌표 2~3개는 버블 대신 라벨 표시·4개+만 클러스터(task-84) — circle/label/cluster/cluster-count 레이어), `place-spider-source`(겹침 분산), `event-ring-source`(사건 링). 각 마커는 shadow+circle+label 3중 레이어.
  - `registerEventHandlers(map, {collapseRing, collapseSpider, expandPlace, spiderifyPlaces, onSelectNode, popupRef, expandedPlaceRef})` — 클릭/호버 핸들러 일괄 바인딩: 마커 클릭 시 겹침이면 spiderify·아니면 ring expand(같은 장소 재클릭은 collapse), 클러스터 클릭은 확대, 스파이더 마커 클릭은 원위치로 펼침, 빈 곳 클릭은 전체 collapse + 팝업 제거. `onSelectNode`로 App에 선택 전파.
  - `placePopupHTML` / `escapeHtml`(모듈 내부) — 마커 팝업 HTML 생성·이스케이프.
- **`mapRingController.js` — 링/스파이더 애니메이션 컨트롤러 팩토리**.
  - `createRingController(map, {expandedPlaceRef, setError})` — 공유 가변 상태(`animFrame`/`spiderAnimFrame`/`spiderState`/`destroyed`/`expandAbortCtrl`)를 클로저에 캡슐화. `expandedPlace`는 컴포넌트의 `expandedPlaceRef`와 **공유** — selection effect와 클릭 핸들러가 펼침 상태를 함께 읽는다(재클릭 collapse 판단).
  - 반환: `collapseRing` / `collapseSpider` / `expandPlace` / `spiderifyPlaces` / `destroy`. `expandPlace`는 `/node/{id}/neighbors/grouped`를 fetch해 Event 이웃을 zoom-adaptive 반경(화면 80px→degrees)으로 `requestAnimationFrame` 링 애니메이트(이전 fetch는 AbortController로 취소). `spiderifyPlaces`는 겹친 마커를 같은 방식으로 분산. `destroy()`가 진행 프레임·진행 fetch를 정리.

`MapView`의 초기화 effect는 `createRingController`로 컨트롤러를 만들고 `expandPlaceRef.current`에 `expandPlace`를 연결한 뒤, `map.on('load')`에서 `setupMapSources`+`registerEventHandlers`를 호출한다. 선택반응 effect는 `/node/{id}/places`를 받아 `placesToGeoJSON`으로 마커를 그리고, Person+3장소↑면 `convexHull`로 hull을 그리며, `isPrimary` 장소가 있으면 카메라 정착(moveend / 700ms 폴백 타이머) 후 링을 자동 펼친다(`isPrimary` 없는 인물/집단은 `coreBounds`로 전체 프레이밍). 언마운트 시 `ring.destroy()` + 팝업·ref 정리 + `map.remove()`.

## 빌드 / 배포

- **프론트** — Vite(`vite.config.js`). `manualChunks`로 `maplibre-gl`을 별도 청크 분리. `npm run build` → `frontend/dist`. React 19 / maplibre-gl 5 / lucide-react / vite 8.
- **nginx** — `nginx/nginx.conf`. `/api/` → `api:8000` 프록시, 정적 자산 1년 immutable 캐시, `index.html` no-cache, SPA fallback(`try_files $uri /index.html`).
- **배포** — `deploy.sh`, `.github/workflows/deploy.yml`. 백엔드 `backend/Dockerfile`(python-slim + uvicorn). 백엔드 의존성: `fastapi` / `neo4j` / `uvicorn`.
