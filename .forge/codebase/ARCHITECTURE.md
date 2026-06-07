---
last_mapped_commit: no-commits-yet
mapped: 2026-06-08
---

# 아키텍처 맵 — BibleMap

## 핵심 패턴

모노레포 구조. 프론트엔드(`frontend/`)와 백엔드(`backend/`)를 단일 레포에서 관리한다. 전체 아키텍처는 **하나의 그래프(Neo4j), 세 가지 렌더링(지도/타임라인/관계도)** 원칙을 따른다.

---

## 레이어 구조

```
[데이터 레이어]       Neo4j
                      ↑
                      Theographic neo4j/ export로 초기 적재
                      ↑
[한글 매핑 레이어]    data/names_ko/*.json → 로더가 노드 속성(nameKo)으로 주입

[API 레이어]          FastAPI (Python)
                      neo4j 공식 Python 드라이버로 연결
                      내부적으로 Cypher 쿼리 실행

[프론트엔드 레이어]   React 19 + Vite
                      세 뷰가 selectedNode 단일 상태로 동기화
```

---

## 데이터 흐름

1. Theographic `neo4j/` export → Neo4j 5 컨테이너에 적재
2. `data/names_ko/*.json` → idempotent 로더가 Neo4j 노드에 `nameKo`, `aliasesKo` 속성 주입
3. React → FastAPI Cypher 쿼리 → Neo4j → JSON 응답
4. `selectedNode` 상태 변경 → MapView / TimelineView / GraphView 동시 갱신

---

## 엔티티

| 엔티티 | 안정 키 | 주요 속성 |
|---|---|---|
| Person | `theographic_id` | name, nameKo, aliasesKo, 생몰, 성별 |
| Place | `theographic_id` | name, nameKo, lat, lng, region 분류 |
| Event | `theographic_id` | name, nameKo, 날짜, 기간, predecessors |
| Period | `theographic_id` | name, nameKo, 시작/끝 연도 |
| Passage | book+chapter+verse | references 관계로 모든 엔티티에 연결 |

`theographic_id`는 Theographic 원본 export 기준 안정 키이며, 영문명 대신 이를 조인 키로 사용한다(동명이인·중복 문제 회피).

---

## API 엔드포인트 (계획)

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/node/{id}` | 단일 노드 상세 조회 |
| GET | `/node/{id}/neighbors` | 인접 노드(1~2촌) 목록 |
| GET | `/search?q=` | 한글/영문/별칭 full-text 검색 |
| GET | `/period/{id}/events` | 시대별 사건 목록 |

FastAPI 내부에서 Cypher로 직접 실행. APOC 불필요.

---

## 프론트엔드 뷰

| 뷰 | 라이브러리 후보 | 역할 |
|---|---|---|
| MapView | MapLibre GL | 장소 노드를 지도에 핀으로 투영 |
| TimelineView | vis-timeline 또는 D3 커스텀 | 시대/사건을 시간 축에 정렬 |
| GraphView | react-force-graph 또는 Cytoscape.js | 인물·사건 관계를 focus+context로 표시 |

세 뷰는 독립적으로 렌더링되지만 `selectedNode` 하나에 의해 동시에 구동된다. 한 뷰에서 노드를 선택하면 나머지 두 뷰가 즉시 동기화된다.

---

## 상태 동기화

```
사용자 인터랙션 (클릭/검색)
    ↓
store/selectedNode 갱신
    ↓
MapView 재렌더 + TimelineView 재렌더 + GraphView 재렌더
```

`selectedNode`는 현재 선택된 엔티티의 `theographic_id`와 타입을 담는다. 각 뷰는 이 값을 구독해 독립적으로 데이터를 fetch하고 렌더링한다.

---

## 배포 토폴로지

- **프론트엔드**: Vercel 배포
- **백엔드 + DB**: Mac 로컬 Docker (`docker-compose.yml`)
  - `neo4j` 서비스: 포트 7474/7687, `127.0.0.1` 바인딩 (퍼블릭 노출 금지)
  - `api` 서비스: FastAPI, 포트 8000, Cloudflare Tunnel 대상
  - FastAPI → Neo4j 연결: compose 내부 서비스명 `bolt://neo4j:7687`
- **터널**: 기존 `cloudflared` 터널에 `biblemap.taebro.com → localhost:8000` ingress 규칙 추가

Neo4j 포트는 절대 퍼블릭에 노출하지 않는다. 터널은 `api` 포트(8000)만 가리킨다.

---

## 한글 매핑 레이어

- 기준 역본: 개역개정
- 파일 위치: `data/names_ko/` (people.json, places.json, events.json, periods.json)
- 포맷: `{ "<theographic_id>": { "ko": "...", "alias": [...] } }`
- Neo4j 반영: 로더가 `UNWIND` + `MATCH` + `SET`으로 속성 주입 (idempotent)
- 검색: `FULLTEXT INDEX entityKo` — nameKo, name, aliasesKo 동시 색인
- Fallback: `nameKo` 없으면 영문 `name` + `nameKoMissing: true` 반환

---

## 구현 단계 (Phase 계획)

| Phase | 목표 | 검증 기준 |
|---|---|---|
| 0 | Neo4j 적재 | Cypher로 임의 인물의 가계·사건·장소 조회 성공 |
| 1 | 단일 엔티티 상세 페이지 | `/node/{id}` 가 한글명 포함 이웃 목록 반환 |
| 2 | 지도 뷰 | 선택 사건의 발생지가 지도에 핀 표시 |
| 3 | 타임라인 뷰 | 시대 축에 사건 정렬, 선택 시 동기화 |
| 4 | 관계도 뷰 | 인물 선택 시 1~2촌만 표시, 털뭉치 없음 |
| 5 | 3뷰 동기화 + 검색 + 투어 | 한 노드 선택이 세 뷰 동시 갱신 |
