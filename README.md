# BibleMap

성경 인물·장소·사건을 그래프로 탐색하는 도구.

## 개발 환경 실행

### 사전 준비
- Docker Desktop 실행 중
- Python 3.11+
- Node.js 18+

### 1. Neo4j 기동
운영 스택은 taebro-infra 표준 배포가 `~/runtime/biblemap/{prod,dev}/`에서 띄운다(호스트 bolt: prod `127.0.0.1:7687`, dev `127.0.0.1:7688`).
아래 스크립트는 기본값으로 prod(7687)를 본다. 작업 폴더에서 따로 띄울 때는 `.env`에 `NEO4J_BOLT_PORT`·`NEO4J_HTTP_PORT`를 두고:
```bash
docker compose up -d neo4j   # 프로젝트명 biblemap-local — prod 와 포트가 겹치지 않게 둘 것
```

### 2. 데이터 적재 (최초 1회)
```bash
pip install neo4j
python3 backend/scripts/load_theographic.py
python3 backend/scripts/inject_ko_names.py
python3 backend/scripts/inject_date_corrections.py
```

> theographic 원본은 Ussher 연대계라 저작 레이어(보수 연대계)와 충돌하는 연대가 있다(ADR-0014).
> `inject_date_corrections.py`가 `data/date_corrections/`의 교정 테이블을 DB에 SET한다 — `load_theographic.py`로
> 원본을 재적재할 때마다(업스트림 갱신 등) **반드시 재실행**해야 한다(멱등, 재실행 안전).
> 배포(`deploy/pre-deploy.sh` → taebro-infra `bin/deploy`)는 검증 게이트 앞에서 주입 2종을 그 env의 Neo4j에 자동 재적용한다. 그래프 적재(`load_theographic.py`)는
> 자동화하지 않는다 — 로더가 교정을 덮어쓰기 때문(ADR `260801-195022`).

### 3. API 서버
```bash
pip install -r backend/requirements.txt
python3 -m uvicorn backend.app.main:app --reload
# http://localhost:8000
```

> `uvicorn` 직접 호출 시 PATH 문제가 생길 수 있음 — `python3 -m uvicorn` 사용.

### 4. 프론트엔드
```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

## 환경변수

`.env.example` 참고. Neo4j 비밀번호는 `.env`에 설정.
