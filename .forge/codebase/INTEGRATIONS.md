---
last_mapped_commit: 4ed4d876d7fa3b06a8eb1647b5b50ed73f906b25
mapped: 2026-06-19
---

# 외부 연동

## 데이터베이스

### Neo4j (그래프 DB)

| 항목 | 값 |
|------|-----|
| 종류 | Neo4j 5 (그래프 DB) |
| 드라이버 | `neo4j==6.2.0` (Python 공식 드라이버) |
| 프로토콜 | Bolt (`bolt://neo4j:7687`) |
| 인증 방식 | 사용자명/비밀번호 (`neo4j` / `NEO4J_PASSWORD`) |
| 연결 설정 위치 | `backend/app/db.py` — `os.getenv("NEO4J_URI")`, `os.getenv("NEO4J_USER")`, `os.environ["NEO4J_PASSWORD"]` |
| 환경변수 출처 | `docker-compose.yml` (`NEO4J_URI=bolt://neo4j:7687`) + `.env` (`NEO4J_PASSWORD`) |
| 인덱스 자동 생성 | 앱 시작 시 `lifespan`에서 Person·Place·Event·PeopleGroup·Book 노드의 `theographic_id` 필드에 인덱스 생성 (`backend/app/main.py`) |
| 데이터 볼륨 | `neo4j_data` Docker named volume |

## 외부 API

### Anthropic Claude API (빌드타임 스크립트 전용)

| 항목 | 값 |
|------|-----|
| 사용 목적 | 성경 데이터 LLM 생성 (권별 배경·주제, 사건별 구절, 인물 특성, 사건-구절 역방향 매핑) |
| 모델 | `claude-haiku-4-5-20251001` |
| 인증 방식 | API Key (`ANTHROPIC_API_KEY` 환경변수, 실행 시 CLI에서 전달) |
| SDK | `anthropic` Python 패키지 (`backend/requirements.txt`에 미포함 — 스크립트 실행 환경에서 별도 설치) |
| 호출 파일 | `backend/scripts/generate_book_context.py`, `backend/scripts/generate_book_events.py`, `backend/scripts/generate_person_traits.py`, `backend/scripts/generate_verse_events.py` |
| 런타임 호출 여부 | **없음** — 데이터 생성 스크립트에서만 호출, 결과는 `data/` 디렉터리 JSON으로 사전 저장됨 |

### getbible API (빌드타임 스크립트 전용)

| 항목 | 값 |
|------|-----|
| 사용 목적 | 성경 구절 원문 텍스트 조회 (한국어 `korean` 번역 + 영어 `kjv` 번역) |
| 엔드포인트 패턴 | `https://api.getbible.net/v2/{slug}/{bookOrder}/{chapter}.json` |
| 인증 방식 | 없음 (공개 API) — User-Agent 헤더 필요 (`Mozilla/5.0 ...`, Python-urllib UA는 403 반환) |
| 호출 파일 | `backend/scripts/generate_verse_text.py` |
| 런타임 호출 여부 | **없음** — 빌드타임에 구절 텍스트를 `data/` JSON에 미리 저장(ADR-0003) |

### Theographic Bible Metadata (빌드타임 스크립트 전용)

| 항목 | 값 |
|------|-----|
| 사용 목적 | 성경 메타데이터 소스 (사람·장소·사건·권별·구절·인물그룹 JSON) |
| 출처 | GitHub raw 파일: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/` |
| 제공 파일 | `books.json`, `events.json`, `verses.json`, `people.json`, `places.json`, `peopleGroups.json` |
| 인증 방식 | 없음 (공개 GitHub raw) |
| 호출 파일 | `backend/scripts/load_theographic.py`, `backend/scripts/load_books.py`, `backend/scripts/generate_book_context.py`, `backend/scripts/generate_event_verses.py`, `backend/scripts/generate_verse_events.py` |
| 런타임 호출 여부 | **없음** — Neo4j 초기 데이터 로드 시에만 사용 |

## 인증 / 인가

런타임 사용자 인증 없음. API는 CORS `allow_origins=["*"]`, `allow_methods=["GET"]`로 읽기 전용 공개 서빙 (`backend/app/main.py`).

## 웹훅 / 이벤트 스트림

없음.

## 3rd-party 서비스 (기타)

없음. 모든 외부 API 호출은 데이터 생성 단계(빌드타임)에서만 발생하며 런타임에는 Neo4j + 정적 JSON 파일만 사용한다.
