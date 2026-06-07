---
last_mapped_commit: no-commits-yet
mapped: 2026-06-08
---

# 기술 스택

> 아직 소스 코드가 없는 기획 단계. `BIBLEMAP_PLAN.md` 기준으로 확정된 스택을 기록한다.

## 언어

| 영역 | 언어 |
|---|---|
| 백엔드 | Python 3.x |
| 프론트엔드 | JavaScript / TypeScript (React 19) |
| DB 쿼리 | Cypher (Neo4j) |
| 인프라 설정 | YAML (docker-compose, cloudflared) |

## 런타임 & 빌드 도구

- **프론트엔드**: Vite (React 19 + Vite 조합 확정)
- **백엔드**: Python (uvicorn + FastAPI)
- **컨테이너**: Docker, Docker Compose (`neo4j:5` 공식 이미지, arm64 네이티브)

## 프레임워크 & 핵심 라이브러리

### 백엔드

| 패키지 | 용도 |
|---|---|
| `fastapi` | HTTP API 서버 |
| `neo4j` | 공식 Python Neo4j 드라이버 |
| `uvicorn` | ASGI 서버 |

### 프론트엔드

| 패키지 | 용도 |
|---|---|
| `react` 19 | UI 프레임워크 |
| `vite` | 번들러/빌드 도구 |
| `maplibre-gl` | 지도 뷰 (오픈소스, 역사 지도 타일 오버레이 지원) |
| `react-force-graph` 또는 `cytoscape.js` | 관계도 뷰 (focus+context 지원 여부가 선택 기준) |
| `vis-timeline` 또는 D3 커스텀 | 타임라인 뷰 |

## 데이터베이스

- **Neo4j 5** (로컬 Docker self-host 확정)
- 이미지: `neo4j:5` (arm64 네이티브)
- 볼륨 마운트로 데이터 영속화
- 포트: `127.0.0.1:7474:7474` (HTTP, 로컬 관리용), `127.0.0.1:7687:7687` (Bolt, 퍼블릭 노출 금지)
- FastAPI → Neo4j 연결: compose 내부 서비스명 `bolt://neo4j:7687`

## 인프라 / 배포

| 구성요소 | 도구 | 비고 |
|---|---|---|
| 프론트엔드 호스팅 | Vercel | PortfoliOn과 동일 패턴 |
| 백엔드 공개 노출 | Cloudflare Tunnel (cloudflared) | 기존 taebro.com 터널에 ingress 규칙 추가 |
| 컨테이너 오케스트레이션 | Docker Compose | `neo4j` + `api` 두 서비스, 단일 내부 네트워크 |
| 상시 가동 | Docker Desktop 자동 시작 + `restart: unless-stopped` | 재부팅 후 자동 복구 |

## 설정 파일 (계획)

- `docker-compose.yml` — neo4j + FastAPI api 서비스 정의
- `~/.cloudflared/config.yml` — ingress 규칙 (`biblemap.taebro.com` → `http://localhost:8000`)
- `data/names_ko/` — 한글 이름 매핑 JSON (레포에서 버전 관리)
