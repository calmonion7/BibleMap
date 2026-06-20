---
last_mapped_commit: ff728ccaffbb9b4e38f1f8f32859a50d3555b515
mapped: 2026-06-20
---

# 외부 연동

## 데이터베이스

### Neo4j 5
- **연결**: Bolt 프로토콜, `bolt://neo4j:7687` (Docker 내부망) / `bolt://localhost:7687` (로컬 직접)
- **인증**: 사용자 `neo4j`, 비밀번호 환경변수 `NEO4J_PASSWORD`
- **드라이버**: `neo4j` Python 패키지 6.2.0, 싱글턴 패턴 (`backend/app/db.py`)
- **접근 방법**: 백엔드 API(읽기), 데이터 파이프라인 스크립트(쓰기/읽기) 모두 동일 드라이버

## 지도 타일 서버

### ESRI ArcGIS Online (NatGeo World Map)
- **URL 패턴**: `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}`
- **타일 크기**: 256px
- **인증**: 없음 (공개 엔드포인트)
- **사용처**: `frontend/src/MapView.jsx` — MapLibre GL `raster` 소스 `esri`

## 지도 폰트 서버

### Protomaps Basemaps Assets
- **URL**: `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf`
- **사용 폰트**: `Noto Sans Regular`
- **인증**: 없음
- **사용처**: `frontend/src/MapView.jsx` — MapLibre GL `glyphs` 설정, 지도 라벨 렌더링

## 외부 데이터 소스 (파이프라인 전용)

### Theographic Bible Metadata (GitHub Raw)
- **리포지터리**: `robertrouse/theographic-bible-metadata`
- **엔드포인트들**:
  - `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/people.json`
  - `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/places.json`
  - `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/events.json`
  - `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/peopleGroups.json`
- **인증**: 없음
- **사용처**: `backend/scripts/load_theographic.py` — Neo4j 초기 데이터 적재 시 1회 사용 (`urllib.request.urlopen`)
- **비고**: 앱 런타임에는 호출하지 않음. 파이프라인 스크립트 실행 시에만 사용

## 내부 API (프론트↔백엔드)

- **통신 방식**: REST HTTP GET, JSON 응답
- **프로덕션 경로**: 프론트 `VITE_API_URL=/api` → nginx `/api/` 프록시 → `api:8000`
- **개발 경로**: `http://localhost:8000` (직접)
- **인증**: 없음
- **엔드포인트 목록**:
  - `GET /node/{id}` — 노드 상세 + 이웃
  - `GET /node/{id}/places` — 노드 관련 장소 좌표
  - `GET /node/{id}/neighbors/grouped` — 이웃 노드 타입별 그룹
  - `GET /person/{id}/event-ids` — 인물의 사건 ID 목록
  - `GET /events` — 타임라인 사건 전체 (`Cache-Control: max-age=300`)
  - `GET /event/{id}/verses` — 사건의 근거 구절 (`Cache-Control: max-age=300`)
  - `GET /books` — 타임라인용 책 목록 (`Cache-Control: no-store`)
  - `GET /books-overview` — 개요 뷰용 책 목록 (`Cache-Control: no-store`)
  - `GET /search?q=` — 이름 검색 (최대 20건)

## 인증 공급자

없음. 인증 레이어 미적용.

## 웹훅

없음.

## 환경변수 (런타임)

| 변수 | 기본값 | 사용처 |
|---|---|---|
| `NEO4J_PASSWORD` | 필수 | 백엔드 API, 모든 파이프라인 스크립트 |
| `NEO4J_URI` | `bolt://localhost:7687` | 백엔드 API, 파이프라인 스크립트 |
| `NEO4J_USER` | `neo4j` | 백엔드 API, 파이프라인 스크립트 |
| `DATA_DIR` | `/app/data` | `backend/app/overlays.py` — 오버레이 JSON 탐색 경로 |
| `VITE_API_URL` | `http://localhost:8000` | 프론트 빌드타임, `.env.production`에서 `/api`로 고정 |
