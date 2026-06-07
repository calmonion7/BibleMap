---
last_mapped_commit: no-commits-yet
mapped: 2026-06-08
---

# 코딩 컨벤션

> 소스 코드 미존재 단계. CLAUDE.md 및 BIBLEMAP_PLAN.md에서 도출한 규칙을 기록.

## 일반 원칙 (CLAUDE.md)

- **단순성 우선**: 요청된 것만 구현. 추측성 기능·추상화 금지.
- **외과적 변경**: 건드려야 할 것만 수정. 인접 코드 정리 금지.
- **목표 기반 실행**: 검증 기준을 먼저 정의하고 통과할 때까지 루프.

## 데이터 식별자 규칙

- **`theographic_id`**: 모든 엔티티의 안정적 기본 키 (영문명은 동명이인 중복 존재 → 키로 부적합)
- Cypher 패턴: `MATCH (p:Person { theographic_id: row.id })`

## 한글 필드 규칙

- `nameKo`: 기본 표시명 (개역개정 기준)
- `aliasesKo`: 검색용 이형·별칭 배열
- `nameKoMissing: true`: 매핑 없는 엔티티에 설정
- API 응답: `nameKo` 있으면 반환, 없으면 `name`(영문) + `nameKoMissing: true`

## Neo4j 연결 규칙

- FastAPI → Neo4j 연결: `bolt://neo4j:7687` (compose 내부 서비스명, 호스트 IP 금지)
- 포트 바인딩: `127.0.0.1:7474:7474`, `127.0.0.1:7687:7687` (localhost only)
- 외부 터널은 FastAPI 포트(8000)만 대상으로 함

## 한글 매핑 파일 위치

- `data/names_ko/people.json` — 인물 한글명
- `data/names_ko/places.json` — 지명 한글명
- `data/names_ko/events.json` — 사건 제목
- `data/names_ko/periods.json` — 시대 제목
- 형식: `{ "<theographic_id>": { "ko": "모세", "alias": ["모세스"] } }`

## Neo4j Cypher 패턴

### 한글명 주입 (idempotent, APOC 불필요)
```cypher
UNWIND $rows AS row
MATCH (p:Person { theographic_id: row.id })
SET p.nameKo = row.ko, p.aliasesKo = row.alias;
```

### 전문검색 인덱스
```cypher
CREATE FULLTEXT INDEX entityKo IF NOT EXISTS
FOR (n:Person|Place|Event|Period)
ON EACH [n.nameKo, n.name, n.aliasesKo];
```
인덱스명: `entityKo`, 한글·영문·별칭 동시 검색.

## 네이밍 규칙 (계획)

- Python (백엔드): `snake_case`
- JavaScript/TypeScript (프론트엔드): `camelCase`
- 컴포넌트: `PascalCase`
- 환경변수: `UPPER_SNAKE_CASE`
