---
last_mapped_commit: 70a9781e6523a396ad856f980b5499b1cc814d7a
mapped: 2026-06-21
---

# BibleMap 코드베이스 우려사항

## 1. 기술 부채 / 취약한 영역

### 1-1. MapView.jsx — 단일 파일 과부하 (734줄)

**파일:** `/Users/calmonion/Project/BibleMap/frontend/src/MapView.jsx`

전체 734줄. 맵 초기화 `useEffect`(`416~604`) 하나가 라이프사이클·이벤트 핸들러·애니메이션·스파이더파이·클러스터·링 확장 클로저를 모두 포함한다. 두 번째 `useEffect`(selectedNode 변경, `606~703`)는 fetch·hull·fitBounds·자동 링 펼침 로직이 한 콜백에 밀집. 단일 콜백 내부 변경이 전체 맵 동작에 예기치 않은 부작용을 일으킬 위험이 높음.

- 모듈 상위 헬퍼(`registerEventHandlers`, `setupMapSources`, `placesToGeoJSON`, `outwardLabel`, `ringLabels` 등 `32~403`)로 일부 추출됐으나, `collapseRing`/`expandPlace`/`spiderifyPlaces`/`collapseSpider` 4개 애니메이션 함수는 여전히 init effect 내부 클로저(`446~581`)에 머무름 — `destroyed`, `animFrame`, `spiderAnimFrame`, `spiderState`, `expandedPlace` 등 effect-스코프 가변 상태를 공유하기 때문.
- 공유 source(`event-ring-source`, `place-spider-source`)에 여러 `requestAnimationFrame` 루프가 동시 `setData`할 수 있는 구조. `collapseRing`/`expandPlace`/`spiderify`/`collapseSpider`가 각자 `animFrame`/`spiderAnimFrame`을 취소·교체하나, 링과 스파이더가 별도 프레임 변수를 쓰므로 동시 진행 가능. 회고(`2026-06-12-place-event-radial-ring.md`)에 source 동시 setData 충돌 전례 기록됨.

> 참고: 이전 맵에 있던 `SHEET_VH`/`MOBILE_QUERY` 이중 하드코딩은 해소됨 — 현재 `frontend/src/constants.js`(`MOBILE_BREAKPOINT=768`, `SHEET_VH=55`)에서 단일 정의하고 `App.jsx`·`MapView.jsx`가 import해서 쓴다.

### 1-2. 기타 대형 파일

| 파일 | 줄 수 |
|------|-------|
| `/Users/calmonion/Project/BibleMap/frontend/src/MapView.jsx` | 734 |
| `/Users/calmonion/Project/BibleMap/frontend/src/SidePanel.jsx` | 435 |
| `/Users/calmonion/Project/BibleMap/frontend/src/TimelineView.jsx` | 368 |
| `/Users/calmonion/Project/BibleMap/backend/scripts/generate_person_event_verses.py` | 336 |
| `/Users/calmonion/Project/BibleMap/frontend/src/App.jsx` | 317 |
| `/Users/calmonion/Project/BibleMap/backend/scripts/load_theographic.py` | 320 |

### 1-3. testament 값 불일치

`BibleOverviewView.jsx:135-137`에 방어 코드 존재:

```js
const key = (t === 'OT' || t === '구약') ? 'OT' : (t === 'NT' || t === '신약') ? 'NT' : null
```

Neo4j 저장값과 코드가 가정하는 값('OT'/'NT')이 혼재. 새 코드 작성 시 어느 형식이 표준인지 불분명. `SidePanel.jsx:177`은 `node.properties.testament`를 그대로 출력하므로 표시 텍스트가 데이터 형식에 종속.

### 1-4. 데이터 기반 단일 고정 앵커 — 라벨 숨김 회귀 벡터

**파일:** `/Users/calmonion/Project/BibleMap/frontend/src/MapView.jsx:259-281`, `334-355`, `383-402`

3개 symbol 레이어(`places-label`/`place-spider-label`/`event-ring-label`)가 native `text-variable-anchor`(줌 인식 + 8슬롯 충돌-폴백)를 버리고 데이터 기반 단일 고정 `text-anchor`/`text-offset`로 전환됨(task-74→75). 단일 슬롯 충돌 시 라벨이 대체 위치를 못 찾고 그냥 숨음 — 가시 라벨 감소 가능. 회고(`2026-06-21-map-label-outward-anchor.md`)에 "의도된 트레이드오프 + 회귀 벡터"로 명시. 향후 맵 라벨 작업 시 먼저 점검 대상.

---

## 2. TODO/FIXME/HACK 주석

소스 코드 전반에 TODO/FIXME/HACK 주석은 발견되지 않음. 아래 세 곳에 의도적 rate limit 슬립이 있음:

- `/Users/calmonion/Project/BibleMap/backend/scripts/generate_verse_events.py:162` — `time.sleep(0.3)  # rate limit 방지`
- `/Users/calmonion/Project/BibleMap/backend/scripts/generate_book_context.py:107` — `time.sleep(0.3)  # rate limit 여유`
- `/Users/calmonion/Project/BibleMap/backend/scripts/generate_person_traits.py:124` — `time.sleep(0.3)`

---

## 3. 성능 우려사항

### 3-1. 검색 엔드포인트 — nameKo/name 인덱스 없음

**파일:** `/Users/calmonion/Project/BibleMap/backend/app/routes/search.py:14-30`

```cypher
MATCH (n)
WHERE (n.nameKo CONTAINS $q OR toLower(n.name) CONTAINS toLower($q))
AND n.theographic_id IS NOT NULL
... ORDER BY rank, n.nameKo LIMIT 20
```

`main.py` lifespan(`backend/app/main.py:11-18`)이 5개 라벨에 `theographic_id` 인덱스만 생성. `nameKo`/`name`에는 인덱스·풀텍스트 인덱스 없음 → `CONTAINS`/`toLower` 매칭은 전체 노드 풀스캔. `ORDER BY n.nameKo`도 인덱스 미활용. 풀텍스트 인덱스 도입은 레트로(`2026-06-11-source-cleanup-structural.md`)에서 "별도 fg-ask로 분리"로 언급됐으나 미구현.

### 3-2. Book 노드 조회 시 3~4중 쿼리

**파일:** `/Users/calmonion/Project/BibleMap/backend/app/routes/nodes.py:145-259`

`/node/{id}` 단일 조회 시 세션 내 순차 쿼리:
1. 노드 기본 조회 (`150`)
2. 이웃 + 총수 (`167-172`, 이전 2쿼리를 1쿼리로 머지함)
3. Book 타입일 때만 topPersons (`202`)
4. Book 타입일 때만 topEvents (`220`)

Book 노드는 4 왕복, 비-Book은 2 왕복.

### 3-3. lru_cache — 대형 파일 메모리 상주

**파일:** `/Users/calmonion/Project/BibleMap/backend/app/overlays.py:42`

`event_verses()`가 `data/event_verses/events.json`(**8.3MB**, 8,344,587 bytes)을 `lru_cache(maxsize=1)`로 메모리에 영구 보유. uvicorn `--workers N` 다중 실행 시 워커마다 독립 복사본 → 메모리 N배.

캐시된 함수 목록:
- `overlays.py:31` — `book_events_raw()`
- `overlays.py:37` — `approx_years()`
- `overlays.py:43` — `event_verses()` (8.3MB)
- `events.py:11` — `_load_approx_book_index()` (Neo4j 전체 Book 쿼리 + 역방향 맵)
- `events.py:53` — `_compute_events()` (Neo4j 전체 Event 쿼리)

모든 `lru_cache`가 프로세스 재시작 전까지 무효화되지 않음 — DB 데이터 변경 후 API 재시작 없이는 반영 안 됨(7-1 참조).

### 3-4. Vite 번들 — 코드 스플리팅 없음

**파일:** `/Users/calmonion/Project/BibleMap/frontend/vite.config.js`

- `manualChunks`로 `maplibre`/`vendor`만 분리. `maplibre` 청크 단독으로 Vite 500kB 경고 초과(회고에 "의도된 상태"). 레트로(`2026-06-16-refactor-3of4-bundle-code-splitting.md`).
- 3개 뷰(`MapView`, `TimelineView`, `BibleOverviewView`) 모두 `App.jsx`에서 정적 import → 초기 로드에 포함. dynamic import / `React.lazy` 없음.
- `vendor` 청크에 `lucide-react`, `react`, `react-dom` 미분리 병합.
- 소스맵 설정 없음.

### 3-5. TimelineView 전체 이벤트 일괄 fetch

**파일:** `/Users/calmonion/Project/BibleMap/frontend/src/TimelineView.jsx`

마운트 시 `/events` 전체를 한 번에 fetch. 페이지네이션/무한스크롤 없음. `/events` 응답에 `Cache-Control: max-age=300`(`events.py:95`) 적용으로 브라우저 캐시는 되나 초기 응답 비용 있음.

### 3-6. nginx gzip 압축 없음

**파일:** `/Users/calmonion/Project/BibleMap/nginx/nginx.conf`

`gzip` 설정 없음. JS 번들(maplibre 포함 ~1.2MB 이상)이 비압축 전송. 정적 자산 캐시(`max-age=31536000, immutable`)·index.html no-cache는 설정됨.

### 3-7. uvicorn 단일 워커

**파일:** `/Users/calmonion/Project/BibleMap/backend/Dockerfile:6`

`CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]` — `--workers` 미지정. CPU 집약 요청 처리 중 다른 요청 대기.

---

## 4. 보안 우려사항

### 4-1. MapLibre 팝업 — XSS 취약 가능성

**파일:** `/Users/calmonion/Project/BibleMap/frontend/src/MapView.jsx:10-30`, `59`, `84`

`placePopupHTML(label, isPrimary)`가 템플릿 리터럴로 HTML을 조립해 `.setHTML(...)`에 전달:

```js
<div ...>${label}</div>
```

`label`은 `e.features[0].properties.label`(Neo4j `nameKo`/`name`/`title` 유래). HTML 이스케이프 없음 → Neo4j 데이터에 `<script>` 등 포함 시 XSS 가능. `typeLabel`은 하드코딩 문자열이라 안전. 그 외 SidePanel·Timeline·Overview는 JSX 텍스트 보간(`{node.properties.background}`, `{keyVerse}` 등)이라 자동 이스케이프됨 — `setHTML` 경로가 유일한 미이스케이프 표면.

### 4-2. CORS — 전체 오리진 허용

**파일:** `/Users/calmonion/Project/BibleMap/backend/app/main.py:25-31`

```python
allow_origins=["*"], allow_credentials=False, allow_methods=["GET"]
```

read-only GET API이고 credentials 비허용이라 직접 피해는 제한적이나, 퍼블릭 배포 시 무제한 오리진 접근 허용.

### 4-3. 인증/Rate Limiting 없음

전체 API에 인증·API 키·rate limiting 없음. 검색 엔드포인트(`/search`) rate limit은 프론트 디바운스(`useSearch.js`)에만 의존. 서버 측 보호 없음.

### 4-4. Cypher — f-string으로 LIMIT 조립

**파일:** `/Users/calmonion/Project/BibleMap/backend/app/routes/nodes.py:169`, `/Users/calmonion/Project/BibleMap/backend/app/routes/search.py:27`

`LIMIT {NODE_NEIGHBOR_LIMIT}`(`nodes.py:169`), `LIMIT {SEARCH_LIMIT}`(`search.py:27`), `[0..{NODE_NEIGHBOR_LIMIT}]`(`nodes.py:169`)을 f-string으로 Cypher에 삽입. 현재는 모듈 상단 하드코딩 상수(`MAX_NEIGHBORS_PER_TYPE=30`, `NODE_NEIGHBOR_LIMIT=50`, `SEARCH_LIMIT=20`)라 실제 인젝션 위험 없음. 사용자 입력값(`q`, `id`)은 모두 파라미터 바인딩(`$q`, `$id`) 사용 — 정상. 향후 가변 값이 f-string 경로로 들어오면 Cypher 인젝션 위험.

### 4-5. 에러 메시지 내부 정보 노출

**파일:** `/Users/calmonion/Project/BibleMap/frontend/src/BibleOverviewView.jsx`

`err.message`를 사용자에게 그대로 노출하는 패턴. 내부 오류 세부사항이 UI로 새어나올 수 있음(MapView는 `setError(true)` 불리언만 사용해 안전).

### 4-6. Docker 이미지 태그 비고정

**파일:** `/Users/calmonion/Project/BibleMap/docker-compose.yml:3`

`image: neo4j:5` — 마이너·패치 버전 미고정. 무의도적 업데이트 가능. (API 이미지는 `python:3.12-slim`으로 마이너까지 고정.)

---

## 5. 변경 위험 영역

### 5-1. MapView.jsx 클러스터/스파이더파이 로직

**파일:** `/Users/calmonion/Project/BibleMap/frontend/src/MapView.jsx:97-101`, `472-499`

- **클러스터 확장 줌 가드 버그 후보:** `places-cluster` 클릭(`97-101`)에서
  ```js
  const zoom = map.getSource('places-source').getClusterExpansionZoom(feature.properties.cluster_id)
  if (zoom) map.easeTo({ center: ..., zoom, ... })
  ```
  `if (zoom)`는 `getClusterExpansionZoom`이 `0`을 반환할 때 false → 줌 0으로의 확장이 무시됨. 데이터 위도대(중동, zoom 5 기준)에서 실제 도달 가능성은 낮으나, falsy(0) 가드는 코드 스멜. MapLibre v5에서 이 API가 콜백→동기 반환으로 바뀐 전례(`2026-06-20-map-place-overlap-cluster-spiderify.md`)가 있어 버전 검증 없이 코드 붙이는 패턴 주의.
- **클러스터 파라미터 튜닝값:** `setupMapSources`(`226-232`)의 `clusterMaxZoom: 13`, `clusterRadius: 18`. 회고(`2026-06-21-map-loosen-clustering.md`)에 "12~14 밑으로 낮추면 마커 원이 포개져 클러스터 존재 이유와 충돌"로 하한 명시. "뭉침 더 줄여줘" 요청 시 라벨 배치(task-74/75)와 클러스터 파라미터를 혼동하지 말 것.
- **스파이더파이/링 R 계산:** `spiderifyPlaces`(`476-477`)·`expandPlace`(`553-555`)가 화면 80px를 `map.project`/`unproject`로 degrees 변환해 R 산출. 줌이 정착되기 전 계산하면 화면 밖으로 날아감(task-15 전례, `656-657` 주석). 자동 펼침은 `moveend`+700ms 폴백 타이머(`668-684`)로 정착 후 실행.

### 5-2. fitBounds outlier 프레이밍 — 저줌 뭉침

**파일:** `/Users/calmonion/Project/BibleMap/frontend/src/MapView.jsx:647-691`

모세처럼 원거리 장소(예: 홍해)가 섞이면 전체를 담느라 줌이 낮아져 마커가 뭉친다. 회고(`2026-06-21-map-loosen-clustering.md`)에 clusterRadius가 아닌 줌 프레이밍 문제로 분류, "별도 작업 후보(outlier 제외/maxZoom·padding 조정)"로 미해결 기록.

### 5-3. 데이터 파이프라인 — 실행 순서 미문서화

**파일:** `/Users/calmonion/Project/BibleMap/backend/scripts/` (디렉토리 전체, 22개 스크립트)

`load_*`/`generate_*`/`inject_*`/`enrich_*` 간 의존 순서가 README·CONTEXT.md 어디에도 명시되지 않음. 신규 `inject_place_context.py:21`이 에러 메시지로 `run generate_verse_text.py first` 힌트를 주는 정도 외엔 순서를 소스에서 역추적해야 함. `generate_verse_text.py`(프리베이크)는 4개 생성 데이터(event_verses·book_context·character_traits·place_context)의 구절 본문을 모두 채우므로 다수 inject 스크립트의 선행 의존.

### 5-4. 외부 서비스 의존 파이프라인

- **getbible.net:** `generate_verse_text.py:53-54,82-83`, `generate_person_event_verses.py:22,172-175` — 기본 urllib UA(`Python-urllib`)에 403 → 브라우저류 UA 스푸핑(`_UA = "Mozilla/5.0 (compatible; BibleMap-build/1.0)"`). 정책 변경 시 파이프라인 실패. (이 두 스크립트는 `timeout=15`/`30` 지정함.)
- **GitHub raw URL:** `load_theographic.py:14-25`, `generate_book_context.py:34`, `generate_event_verses.py:38`, `generate_person_traits.py:36`, `generate_verse_events.py:58` — `raw.githubusercontent.com/robertrouse/theographic-bible-metadata/...` 직접 fetch. 이들 `urlopen` 호출에 timeout 파라미터 없음 → 네트워크 행 시 무한 대기 가능. 외부 repo 변경·GitHub 장애 시 실패.
- **Anthropic API:** `generate_book_context.py`, `generate_person_traits.py`, `generate_event_verses.py`, `generate_verse_events.py`가 `ANTHROPIC_API_KEY` 의존. ADR-0006으로 우회(LLM이 직접 데이터 생성)하여 실질 실행 불가 상태.

---

## 6. 누락된 에러 처리

### 6-1. generate_person_event_verses.py — 실패한 챕터 재시도 불가

**파일:** `/Users/calmonion/Project/BibleMap/backend/scripts/generate_person_event_verses.py`

`fetch_chapter()` 네트워크 실패 시 해당 chapter를 None 처리하고 계속 진행. 멱등 로직(`books` 필드 있으면 스킵)으로 실패 항목은 재실행해도 스킵됨 → 실패한 챕터가 영구 누락 가능.

### 6-2. inject_place_context.py — 매칭 실패 무경고

**파일:** `/Users/calmonion/Project/BibleMap/backend/scripts/inject_place_context.py:38-52`

`UNWIND ... MATCH (p:Place {theographic_id: row.theographic_id}) SET ...` — JSON의 `theographic_id`가 어떤 Place 노드와도 매칭 안 되면 그 row는 조용히 SET 누락. 검증은 `count(p) WHERE p.background IS NOT NULL`(`49-51`)과 Bethlehem 단건 확인(`54-60`)뿐 → places.json 43건 중 일부가 매칭 실패해도 드러나지 않음(누락 건수 미보고).

### 6-3. expandPlace fetch 실패 — 무음 무시

**파일:** `/Users/calmonion/Project/BibleMap/frontend/src/MapView.jsx:541-545`

```js
try { grouped = await apiGet(`/node/${placeId}/neighbors/grouped`, { signal }) }
catch { return }
```

링 펼침용 fetch 실패(네트워크 오류 포함)를 AbortError와 구분 없이 전부 무음 return. 사용자에게 "사건 정보를 불러오지 못함" 피드백 없음 — 클릭해도 링이 안 펼쳐지는 무반응으로만 보임.

### 6-4. /node/{node_id} — node_id 포맷 검증 없음

**파일:** `/Users/calmonion/Project/BibleMap/backend/app/routes/nodes.py:145-156`

`node_id` 포맷 검증 없음. 존재하지 않는 ID는 404, 임의 문자열은 파라미터 바인딩으로 안전하나 검증 자체는 부재.

### 6-5. /event/{event_id}/verses — 빈 응답 처리

**파일:** `/Users/calmonion/Project/BibleMap/backend/app/routes/events.py:98-104`

존재하지 않는 `event_id`에 대해 `{"books": []}`를 200 OK로 반환. 클라이언트가 유효하지 않은 ID와 구절 없는 이벤트를 구분 불가.

> 참고: 이전 우려 "authored Place 노드 `name` 미설정"은 해소됨 — `enrich_place_coords.py:37-38`이 MERGE 시 `pl.name`·`pl.title`을 함께 SET한다.

---

## 7. 데이터 품질 이슈

### 7-1. lru_cache — DB 변경 시 즉시 반영 안 됨

**파일:** `/Users/calmonion/Project/BibleMap/backend/app/overlays.py`, `/Users/calmonion/Project/BibleMap/backend/app/routes/events.py`

Neo4j 데이터 변경(스크립트 재실행, 직접 패치) 후 API 프로세스 재시작 없이는 캐시된 데이터(`_compute_events`, `_load_approx_book_index`, overlay JSON들)가 그대로 서빙됨. 파이프라인 재실행 후 API 재시작이 필수 절차이나 문서화 없음.

### 7-2. testament 값 혼재

**파일:** `/Users/calmonion/Project/BibleMap/frontend/src/BibleOverviewView.jsx:135-137`

Neo4j 저장값과 코드 기대값('OT'/'NT')이 공존. 방어 코드로 양방향 처리 중이나 근본 원인(데이터 형식 통일) 미해결.

### 7-3. 장소 컨텍스트 keyVerse 중복

**파일:** `/Users/calmonion/Project/BibleMap/data/place_context/places.json`

회고(`2026-06-21-place-scripture-context.md`)에 하란·우르 keyVerse가 동일("창 11:31", 의도된 데이터)·일부 절 trailing space(getbible 원본 보존) 기록. 데이터 결함은 아니나 표시 일관성 점검 시 인지 필요.

---

## 8. 테스트 부재

애플리케이션 소스에 `.test.`/`.spec.` 파일 없음(`node_modules` 내부 라이브러리 테스트 제외). `frontend/package.json` scripts는 `dev`/`build`/`lint`/`preview`만 — test 스크립트 없음. 백엔드도 테스트 프레임워크·테스트 파일 없음. Playwright UAT는 회고에 패턴으로 반복 언급되나 리포지토리에 자동화 테스트 파일은 없음. 변경 회귀를 자동 감지할 수단 부재 — 검증은 매번 수동 Playwright + `.forge/reports/` 스크린샷에 의존.

---

## 9. 기타 구조적 이슈

### 9-1. 함수 내부 import

**파일:** `/Users/calmonion/Project/BibleMap/backend/app/routes/nodes.py:240`

```python
import json as _json
```

`traits` 처리 분기 내부 조건부 import. 기능 문제 없으나 모듈 레벨 import 규범 위반.

### 9-2. 검색 입력 길이 제한 없음

**파일:** `/Users/calmonion/Project/BibleMap/backend/app/routes/search.py:8-11`

`/search?q=`에 `q.strip()` 빈 값 체크만 수행. 길이 제한 없음. 극단적으로 긴 입력 시 인덱스 없는 `CONTAINS` 풀스캔(3-1) 부하 증가.

### 9-3. dead config — text-justify

**파일:** `/Users/calmonion/Project/BibleMap/frontend/src/MapView.jsx:270`, `344`, `393`

`text-variable-anchor`(task-74) 제거 후 `'text-justify': 'auto'`가 3개 symbol 레이어에 dead config로 잔존. `placesToGeoJSON`/`ringLabels`의 `cosLat` 가드 `|| 1`은 `Math.cos(90°)=6.12e-17`(truthy)라 무효이나 데이터 위도대(26~37°N) 미도달로 실해 없음. 둘 다 코드 스멜 수준(회고 `2026-06-21-map-label-outward-anchor.md`에 정리 부채로 기록).
