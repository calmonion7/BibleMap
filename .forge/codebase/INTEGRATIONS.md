---
last_mapped_commit: no-commits-yet
mapped: 2026-06-08
---

# 외부 통합

## 데이터 소스

### Theographic / Viz.Bible
- 레포: `robertrouse/theographic-bible-metadata`
- 제공 포맷: JSON, CSV, Neo4j export
- **사용 포맷: `neo4j/` export** (Neo4j 확정에 따라 직접 적재)
- 라이선스: **CC-BY-SA-4.0**
  - BY: 앱 내 크레딧 페이지에 출처 표기 필수
  - SA: 데이터 가공·확장 시 동일 라이선스 공개 의무 가능성 → 독점 DB 계획이면 법률 검토 필요
- 제공 엔티티: Person, Place, Event, Period, Passage + 외부 DB 링크(Wikidata QID 포함)

### OpenBible.info Geo
- 용도: 장소(Place) 위경도 데이터
- Theographic 장소 데이터의 좌표 기반

## 데이터베이스

### Neo4j 5 (로컬 Docker)
- 연결: `bolt://neo4j:7687` (Docker Compose 내부 서비스명)
- 인증: 환경변수로 주입 (docker-compose `environment` 섹션)
- 포트 바인딩: `127.0.0.1:7474:7474`, `127.0.0.1:7687:7687` (localhost only, 퍼블릭 노출 금지)
- 드라이버: `neo4j` Python 공식 드라이버

## 배포 / 인프라

### Vercel
- 용도: React 프론트엔드 배포
- 패턴: PortfoliOn과 동일한 Vercel 배포 방식

### Cloudflare Tunnel (cloudflared)
- 용도: Mac 로컬 FastAPI를 `https://biblemap.taebro.com`으로 공개 노출
- 설정 파일: `~/.cloudflared/config.yml`
- ingress 규칙 (추가 예정):
  ```yaml
  - hostname: biblemap.taebro.com
    service: http://localhost:8000
  ```
- DNS 라우트: `cloudflared tunnel route dns <tunnel-name> biblemap.taebro.com`
- cloudflared는 outbound 연결만 → Neo4j 포트는 구조적으로 외부 차단

## 한글 매핑 보조 소스

### Wikidata (계획, Tier 2)
- 라이선스: **CC0**
- 용도: 인물·지명 한국어 라벨 일괄 생성 후 검수 (롱테일 ~2,700+ 엔티티)
- 연결 방법: Theographic이 제공하는 Wikidata QID 브리지
- 현재 상태: 미구현, Phase 0~1 이후 계획
