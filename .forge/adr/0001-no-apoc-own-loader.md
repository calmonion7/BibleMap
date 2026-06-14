# ADR-0001 — APOC 없이 자체 Python 로더 사용

**상태**: 확정

## 맥락

Theographic Bible Metadata 레포의 `neo4j/import/` 디렉토리는 APOC 프로시저(`apoc.periodic.iterate`, `apoc.load.json`)에 의존하는 Cypher 스크립트를 제공한다. APOC는 Neo4j 플러그인이므로 Docker 이미지 설정이 복잡해지고, Community Edition에서의 동작을 별도로 검증해야 한다.

## 결정

Theographic의 Cypher 스크립트를 사용하지 않는다. 대신 Theographic `json/` 디렉토리의 원본 JSON을 Python에서 직접 fetch하여, 순수 Cypher(`UNWIND $rows ... MERGE`)로 적재하는 자체 로더(`backend/scripts/load_theographic.py`)를 작성한다.

## 결과

- **장점**: APOC 플러그인 불필요 → Docker 설정 단순화. 순수 `neo4j:5` 공식 이미지만 사용.
- **장점**: 로더 로직이 Python 코드로 명시적으로 관리됨. status 필터, 관계 매핑 등을 직접 제어 가능.
- **단점**: Theographic 스키마가 바뀌면 로더를 직접 수정해야 함 (upstream 스크립트 자동 추종 불가).
