# BibleMap

성경 인물·장소·사건을 그래프로 탐색하는 도구.

## 개발 환경 실행

### 사전 준비
- Docker Desktop 실행 중
- Python 3.11+
- Node.js 18+

### 1. Neo4j 기동
```bash
docker compose up -d
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
