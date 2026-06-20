---
last_mapped_commit: 7a1ef362b1fb247b09edeeaa1380e6449fce5721
mapped: 2026-06-20
---

# BibleMap 코드베이스 우려사항

## 1. 기술 부채 / 취약한 영역

### 1-1. MapView.jsx — 단일 파일 과부하 (708줄)

**파일:** `/Users/calmonion/Project/BibleMap/frontend/src/MapView.jsx`

전체 708줄 중 `useEffect` 하나가 맵 초기화·이벤트 핸들러·애니메이션·스파이더파이·클러스터·링 확장을 모두 포함. 두 번째 `useEffect`(selectedNode 변경 처리)도 195~677줄 범위에 걸침. 단일 콜백 내부 변경이 전체 맵 동작에 예기치 않은 부작용을 일으킬 위험이 높음.

- `SHEET_VH`(55vh)와 `MOBILE_QUERY`(768px) 상수가 `App.jsx:18-20`과 `MapView.jsx:633-634`에 각각 하드코딩되어 이중 관리됨. 한 쪽만 변경하면 레이아웃 깨짐.
- `onSelectNode` 콜백 identity 안정화(`useCallback([], ...)`)를 맵 초기화 effect가 의존함 (`MapView.jsx:578`의 deps). `useNodeSelection.js`에 주석으로 이유 설명되어 있으나 미묘한 결합.

### 1-2. 기타 대형 파일

| 파일 | 줄 수 |
|------|-------|
| `/Users/calmonion/Project/BibleMap/frontend/src/SidePanel.jsx` | 392 |
| `/Users/calmonion/Project/BibleMap/frontend/src/TimelineView.jsx` | 367 |
| `/Users/calmonion/Project/BibleMap/frontend/src/App.jsx` | 318 |
| `/Users/calmonion/Project/BibleMap/backend/scripts/generate_person_event_verses.py` | 336 |
| `/Users/calmonion/Project/BibleMap/backend/scripts/load_theographic.py` | 320 |

### 1-3. testament 값 불일치

`BibleOverviewView.jsx:137`에 `(t === 'OT' || t === '구약')` 형태의 방어 코드가 존재. Neo4j 저장값('구약'/'신약')과 일부 코드가 가정하는 값('OT'/'NT')이 혼재. 새 코드 작성 시 어느 쪽 형식을 사용해야 하는지 불분명.

---

## 2. TODO/FIXME/HACK 주석

소스 코드 전반에 TODO/FIXME/HACK 주석은 발견되지 않음. 아래 두 곳에 의도적 rate limit 슬립이 있음:

- `/Users/calmonion/Project/BibleMap/backend/scripts/generate_verse_events.py:162` — `time.sleep(0.3)  # rate limit 방지`
- `/Users/calmonion/Project/BibleMap/backend/scripts/generate_book_context.py:107` — `time.sleep(0.3)  # rate limit 여유`

---

## 3. 성능 우려사항

### 3-1. 검색 엔드포인트 — 풀 노드 스캔

**파일:** `/Users/calmonion/Project/BibleMap/backend/app/routes/search.py:27`

```cypher
MATCH (n)
WHERE (n.nameKo CONTAINS $q OR toLower(n.name) CONTAINS toLower($q))
LIMIT 20
```

`nameKo`, `name` 필드에 Neo4j 인덱스가 없음. `main.py` lifespan에서 `theographic_id`에만 인덱스 생성. 모든 검색이 전체 노드 풀스캔. 풀텍스트 인덱스 필요성은 레트로(`2026-06-11-source-cleanup-structural.md`)에서 "별도 fg-ask로 분리 예정"으로 언급됐으나 미구현.

### 3-2. Book 노드 조회 시 4중 쿼리

**파일:** `/Users/calmonion/Project/BibleMap/backend/app/routes/nodes.py:145-258`

Book 타입 노드 단일 조회 시 Neo4j 세션 내에서 순차적으로 4번 쿼리 실행:
1. 노드 기본 조회 (line 150)
2. 이웃 노드 조회 (line 167)
3. topPersons 쿼리 (line 201)
4. topEvents 쿼리 (line 220)

### 3-3. lru_cache — 대형 파일 메모리 상주

**파일:** `/Users/calmonion/Project/BibleMap/backend/app/overlays.py:42`

`event_verses()` 함수가 8.1MB JSON 파일을 `lru_cache(maxsize=1)`로 메모리에 영구 보유. uvicorn `--workers N` 다중 실행 시 각 워커마다 독립 복사본 → 메모리 N배 증가.

캐시된 함수 목록:
- `overlays.py:30` — `book_events_raw()`
- `overlays.py:36` — `approx_years()`
- `overlays.py:42` — `event_verses()` (8.1MB)
- `events.py:11` — `_load_approx_book_index()` (Neo4j 전체 쿼리)
- `events.py:53` — `_compute_events()` (Neo4j 전체 Event 쿼리)

모든 `lru_cache`가 프로세스 재시작 전까지 무효화되지 않음 — DB 데이터 변경 후 API 재시작 없이는 반영 안 됨.

### 3-4. Vite 번들 — 코드 스플리팅 없음

**파일:** `/Users/calmonion/Project/BibleMap/frontend/vite.config.js`

- `maplibre` 청크 단독 **1,027kB** (Vite 500kB 경고 초과). 레트로에 "의도된 상태"로 명시.
- 3개 뷰(`MapView`, `TimelineView`, `BibleOverviewView`) 모두 초기 로드에 포함. dynamic import / lazy loading 없음.
- `vendor` 청크에 `lucide-react`, `react`, `react-dom`이 미분리 병합.
- 소스맵 설정 없음.

### 3-5. TimelineView 전체 이벤트 일괄 fetch

**파일:** `/Users/calmonion/Project/BibleMap/frontend/src/TimelineView.jsx:48-51`

마운트 시 `/events` 전체를 한 번에 fetch. 페이지네이션/무한스크롤 없음. `Cache-Control: max-age=300`으로 브라우저 캐시는 적용되나 초기 응답 비용 있음.

### 3-6. nginx gzip 압축 없음

**파일:** `/Users/calmonion/Project/BibleMap/nginx/nginx.conf`

`gzip` 설정 없음. JS 번들(~1.2MB 이상)이 비압축으로 전송됨.

### 3-7. uvicorn 단일 워커

**파일:** `/Users/calmonion/Project/BibleMap/backend/Dockerfile:6`

`CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]` — `--workers` 미지정. CPU 집약 요청 처리 중 다른 요청 대기.

---

## 4. 보안 우려사항

### 4-1. MapLibre 팝업 — XSS 취약 가능성

**파일:** `/Users/calmonion/Project/BibleMap/frontend/src/MapView.jsx:451-468`, `495-512`

```js
.setHTML(`
  <div ...>
    <div ...>${label}</div>
    <div ...>${typeLabel}</div>
  </div>
`)
```

`label`은 `e.features[0].properties.label` (Neo4j `nameKo` 또는 `name` 직접 삽입). HTML 이스케이프 없음. Neo4j 데이터에 `<script>` 등이 포함될 경우 XSS 가능. `typeLabel`은 하드코딩 문자열이라 안전.

### 4-2. CORS — 전체 오리진 허용

**파일:** `/Users/calmonion/Project/BibleMap/backend/app/main.py:26-31`

```python
allow_origins=["*"]
```

현재 read-only API이므로 직접 피해는 제한적이나, 퍼블릭 배포 시 무제한 접근 허용.

### 4-3. 인증/Rate Limiting 없음

전체 API에 인증·API 키·rate limiting 없음. 검색 엔드포인트(`/search`) rate limit은 프론트엔드 250ms 디바운스에만 의존. 서버 측 보호 없음.

### 4-4. Cypher — f-string 조립 패턴

**파일:** `/Users/calmonion/Project/BibleMap/backend/app/routes/nodes.py:168-170`, `/Users/calmonion/Project/BibleMap/backend/app/routes/search.py:27`

`LIMIT {NODE_NEIGHBOR_LIMIT}`, `LIMIT {SEARCH_LIMIT}`를 f-string으로 Cypher에 삽입. 현재는 모듈 상단 하드코딩 상수라 실제 인젝션 위험 없으나, 해당 위치에 가변 값이 들어오는 패턴으로 확장될 경우 Cypher 인젝션 위험.

### 4-5. 에러 메시지 내부 정보 노출

**파일:** `/Users/calmonion/Project/BibleMap/frontend/src/BibleOverviewView.jsx:149`

```js
setError(err.message || '불러오기 실패')
```

`err.message`가 내부 오류 세부사항을 사용자에게 노출할 수 있음.

### 4-6. Docker 이미지 태그 비고정

**파일:** `/Users/calmonion/Project/BibleMap/docker-compose.yml:2`

`image: neo4j:5` — 마이너·패치 버전 미고정. 무의도적 업데이트 가능.

---

## 5. 변경 위험 영역

### 5-1. MapView.jsx 클러스터/스파이더파이 로직

**파일:** `/Users/calmonion/Project/BibleMap/frontend/src/MapView.jsx`

레트로(`2026-06-20-map-place-overlap-cluster-spiderify.md`)에 MapLibre v5에서 `getClusterExpansionZoom` API가 콜백→동기 반환값으로 변경된 전례 기록됨. 라이브러리 버전 검증 없이 코드를 붙이는 패턴이 반복됨. 클러스터·스파이더파이·링 로직이 단일 effect에 밀집되어 부분 수정 시 다른 기능에 영향 가능성 높음.

### 5-2. 데이터 파이프라인 — 실행 순서 미문서화

**파일:** `/Users/calmonion/Project/BibleMap/backend/scripts/` (디렉토리 전체)

스크립트 간 의존 순서가 README·CONTEXT.md 어디에도 명시되지 않음. 최소 15개 스크립트의 실행 순서를 소스 코드에서 역추적해야 함.

### 5-3. 외부 서비스 의존 파이프라인

- **getbible.net:** `generate_person_event_verses.py:22` — `Python-urllib` UA 차단으로 브라우저 UA 스푸핑 중(`_UA = "Mozilla/5.0 (compatible; BibleMap-build/1.0)"`). 정책 변경 시 파이프라인 실패.
- **GitHub raw URL:** `load_theographic.py` — `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/...` 직접 fetch. 외부 repo 변경 또는 GitHub 네트워크 장애 시 실패. `urlopen` timeout 파라미터 없음.
- **Anthropic API:** `generate_book_context.py`, `generate_person_traits.py`, `generate_event_verses.py`, `generate_verse_events.py` 4개 스크립트가 `ANTHROPIC_API_KEY` 필요. 현재 ADR-0006으로 우회(LLM이 직접 데이터 생성)하여 이 스크립트들은 실질적으로 실행 불가 상태.

---

## 6. 누락된 에러 처리

### 6-1. generate_person_event_verses.py — 실패한 챕터 재시도 불가

**파일:** `/Users/calmonion/Project/BibleMap/backend/scripts/generate_person_event_verses.py`

`fetch_chapter()` 네트워크 실패 시 해당 chapter를 None으로 처리하고 계속 진행. 멱등 로직(`books` 필드 있으면 스킵)으로 인해 실패한 항목은 재실행해도 스킵됨 → 실패한 챕터가 영구 누락될 수 있음.

### 6-2. authored Place 노드 name 미설정 재발 가능성

레트로(`2026-06-20-person-activity-range-1of2-place-coords.md`) — `enrich_place_coords.py`가 authored Place 노드 생성 시 `title`만 설정하고 `name` 미설정하는 버그. Neo4j 직접 패치로 수정됐으나 스크립트 자체는 수정 여부 미확인. 재실행 시 재발 가능성.

### 6-3. /node/{node_id} — node_id 포맷 검증 없음

**파일:** `/Users/calmonion/Project/BibleMap/backend/app/routes/nodes.py`

`node_id` 포맷 검증 없음. 존재하지 않는 ID는 404 반환되나, 임의 문자열 입력에 대한 방어 없음.

### 6-4. /event/{event_id}/verses — 빈 응답 처리

**파일:** `/Users/calmonion/Project/BibleMap/backend/app/routes/events.py`

존재하지 않는 `event_id`에 대해 `{}` (빈 books)를 200 OK로 반환. 클라이언트가 유효하지 않은 ID와 구절 없는 이벤트를 구분 불가.

---

## 7. 데이터 품질 이슈

### 7-1. lru_cache — DB 변경 시 즉시 반영 안 됨

**파일:** `/Users/calmonion/Project/BibleMap/backend/app/overlays.py`, `/Users/calmonion/Project/BibleMap/backend/app/routes/events.py`

Neo4j 데이터 변경(스크립트 재실행, 직접 패치) 후 API 프로세스 재시작 없이는 캐시된 데이터가 그대로 서빙됨. 데이터 파이프라인 재실행 후 API 재시작이 필수 절차이나 문서화 없음.

### 7-2. testament 값 혼재

**파일:** `/Users/calmonion/Project/BibleMap/frontend/src/BibleOverviewView.jsx:137`

Neo4j에 '구약'/'신약'으로 저장된 값과 코드에서 'OT'/'NT'를 기대하는 부분이 공존. 방어 코드로 양방향 처리 중이나 근본 원인 미해결.

---

## 8. 테스트 부재

전체 프로젝트에 `.test.` / `.spec.` 파일 없음. `package.json`에 test 스크립트 없음. Playwright UAT는 레트로에 패턴으로 언급되나 소스에 테스트 파일 없음. 변경사항의 회귀를 자동으로 감지할 수단 없음.

---

## 9. 기타 구조적 이슈

### 9-1. 함수 내부 import

**파일:** `/Users/calmonion/Project/BibleMap/backend/app/routes/nodes.py:240`

```python
import json as _json
```

`traits` 처리 분기 내부에서 조건부 import. 기능 문제 없으나 모듈 레벨 import 규범 위반.

### 9-2. 검색 입력 길이 제한 없음

**파일:** `/Users/calmonion/Project/BibleMap/backend/app/routes/search.py`

`/search?q=` 파라미터에 공백 trim만 수행. 길이 제한 없음. 극단적으로 긴 입력이 들어올 경우 Neo4j 풀스캔 쿼리 부하 증가.
