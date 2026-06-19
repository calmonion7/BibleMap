---
last_mapped_commit: 9f47b78ed927ef302cefffb5b62ef71885b6aa94
mapped: 2026-06-19
---

# CONCERNS — 기술 부채·버그·보안·성능·취약 영역

---

## 1. 보안

### [높음] `.env` 평문 약한 비밀번호
- `/Users/calmonion/Project/BibleMap/.env`: `NEO4J_PASSWORD=biblemap123` 평문 저장
- `.gitignore`에 `.env`가 있어 커밋 차단은 되어 있으나, 로컬 파일시스템 접근 시 평문 노출
- `biblemap123`은 사전 공격에 취약한 약한 비밀번호

### [중간] CORS `allow_origins=["*"]`
- `/Users/calmonion/Project/BibleMap/backend/app/main.py` 27행: 모든 오리진 허용
- 현재 `allow_methods=["GET"]` 전용이라 즉각 위협은 제한적이나, 향후 쓰기 엔드포인트 추가 시 무방비

### [낮음] `main.py` lifespan에서 f-string 레이블 삽입
- `/Users/calmonion/Project/BibleMap/backend/app/main.py` 14~17행: `f"CREATE INDEX {label.lower()}_tid..."` 패턴
- `label`은 하드코딩 리스트(`['Person', 'Place', 'Event', ...]`)에서만 오므로 실제 injection 경로는 없음
- 그러나 Cypher parameterization 원칙에 위배 — 유지보수 중 변수 출처가 외부로 바뀌면 즉시 취약점이 됨

---

## 2. 성능

### [높음] 타임라인 전체 데이터 페이지네이션 없이 단일 fetch
- `/events` 엔드포인트가 모든 사건(~450+개)을 매번 전체 반환
- `TimelineView.jsx` 54행 `useEffect`에서 캐싱 없이 컴포넌트 마운트마다 재호출
- DOM 가상화(windowing) 없음 — 이벤트 수가 늘어날수록 DOM 노드 선형 증가
- `Cache-Control: no-store` 헤더가 명시되어 있어(`events.py` 말미) 브라우저 캐시도 비활성화

### [높음] 8MB event_verses JSON 메모리 상주
- `/Users/calmonion/Project/BibleMap/data/event_verses/events.json`: 7,991,256 bytes (~8MB)
- `events.py`의 `_load_event_verses()`가 `lru_cache(maxsize=1)`로 전체를 메모리에 상주
- 앱 재시작 없이 파일 변경이 반영되지 않음

### [중간] `TimelineView` 그룹핑 계산이 `useMemo` 없이 매 렌더마다 재실행
- `/Users/calmonion/Project/BibleMap/frontend/src/TimelineView.jsx` 64~100행: `groupMap`, `groups`, `visibleGroups`, `timeline` 계산이 `useMemo` 없이 컴포넌트 함수 본문에서 실행
- `events` 배열(~450개 항목)을 매 렌더마다 순회·정렬

### [중간] `/node/{id}` 엔드포인트 다중 `session.run()` 호출
- `/Users/calmonion/Project/BibleMap/backend/app/routes/nodes.py`의 `get_node()`: 단일 요청에 대해 노드 조회 + 이웃 조회 + 이웃 총수 + (Book인 경우) topPersons + topEvents 쿼리를 각각 별도 `session.run()`으로 실행 — 최대 5회 순차 Neo4j 왕복
- 연결 풀 설정 없음: `/Users/calmonion/Project/BibleMap/backend/app/db.py`에서 `GraphDatabase.driver()` 기본값 사용

### [중간] uvicorn 단일 워커
- `/Users/calmonion/Project/BibleMap/backend/Dockerfile`: `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]` — `--workers` 미설정
- 기본 1 워커로, I/O 블로킹(Neo4j 쿼리) 중 다른 요청 처리 불가

### [낮음] `_load_approx_book_index()` 첫 요청 시 cold start 지연
- `/events` 첫 요청에서 `lru_cache` 미스 → JSON 파일 읽기 + Neo4j 쿼리 복합 실행
- 앱 lifespan에서 미리 워밍업하지 않아 첫 사용자 요청이 느려질 수 있음

---

## 3. 기술 부채

### [높음] floating nav 바가 콘텐츠 최상단 가림 — 미근본해결 (retro 3회 반복)
- 2026-06-19 retro(`timeline-person-filter`): nav 바(48px)가 scroll container 전체를 덮는 레이아웃에서 sticky `top: 0` 배너가 가려짐. bookFilter와 personFilter 배너를 `top: 48`로 수정
- 2026-06-17 retro(`timeline-bottom-padding`): 하단 잘림 수정 시 "상단 nav 겹침"을 non-goal로 명시하고 우회
- 근본 원인(`position: absolute` floating nav가 레이아웃 흐름에 없음)은 미해결. 새 배너/고정 요소 추가마다 `top: 48` 오프셋을 수동으로 설정해야 하는 패턴이 고착됨
- Playwright 검증에서 nav 영역 클릭이 차단되어 `dispatch_event` 또는 `force: true` 우회 필요

### [중간] `eslint-plugin-react-hooks` caret 범프로 기존 코드 lint 위반 상시 위험
- `/Users/calmonion/Project/BibleMap/frontend/package.json`에 `"eslint-plugin-react-hooks": "^7.1.1"` — caret으로 마이너 자동 범프
- v7에서 `react-hooks/set-state-in-effect` 신규 룰 추가로 SidePanel 기존 패턴이 위반됨(2026-06-11 retro 기록)
- 현재는 수정됐으나, 플러그인이 다시 범프될 경우 동일 문제 재발 가능 — 버전 핀 또는 정책 결정 미완(retro 후속 항목으로만 남음)

### [중간] JSON 오버레이 파일과 Neo4j 그래프 간 동기화 무결성 보장 없음
- `data/event_verses/events.json`, `data/book_events/books.json`, `data/book_years_approx/books.json` 등이 Neo4j와 별개로 관리
- Neo4j 그래프 변경 시 JSON 파일이 함께 갱신됐는지 검증하는 메커니즘 없음
- `lru_cache`로 인해 앱 재시작 없이는 파일 변경이 API에 반영되지 않음

### [중간] `ANTHROPIC_API_KEY` 없어 generate 스크립트 실행 불가 — LLM 직접 생성 패턴 3회 반복
- 2026-06-19 retro(`verse-events-pipeline`): "S1 실행 방식: ANTHROPIC_API_KEY 없어 generate 스크립트 직접 실행 불가 → LLM이 직접 생성. task 47·48과 동일 패턴, 3회 반복"
- `/Users/calmonion/Project/BibleMap/backend/scripts/` 아래 generate 스크립트들이 실제 실행 가능한 상태인지 검증되지 않은 채 레시피 아티팩트로만 존재
- ADR-0006에서 "의도된 패턴"으로 공식화됐으나, 스크립트 코드가 실제 환경과 계속 乖離될 위험

### [중간] `throw res.status` 패턴 — 에러 정보 손실
- `/Users/calmonion/Project/BibleMap/frontend/src/api.js` 9행: `if (!res.ok) throw res.status`
- 에러가 숫자로 던져져 `catch (e)` 블록에서 `e`가 숫자인지 Error 객체인지 혼용. 응답 본문(서버 에러 메시지)은 유실
- SidePanel에서 `String(e)` 처리로 "500" 같은 문자열이 사용자에게 노출

### [낮음] `activeFilter`와 `activePersonFilter` 두 배너 동시 표시 미처리
- `/Users/calmonion/Project/BibleMap/frontend/src/TimelineView.jsx` 228~255행: bookFilter 배너와 personFilter 배너가 각각 독립적으로 표시
- 두 필터가 동시에 활성이면 배너 두 개가 타임라인 상단을 점유하는 레이아웃 미정의

### [낮음] vite8/rolldown `manualChunks` 함수형만 유효
- 2026-06-16 retro(`bundle-code-splitting`): object형 `manualChunks`는 rolldown에서 `TypeError: manualChunks is not a function` 오류. 함수형만 동작
- `/Users/calmonion/Project/BibleMap/frontend/vite.config.js`에 현재 함수형으로 작성되어 있으나, vite/rolldown 문서와 다른 동작이라 향후 다른 기여자가 object형으로 변경할 위험

---

## 4. 외부 의존성 위험

### [중간] ESRI NatGeo 타일 서버 ToS 미검토
- `/Users/calmonion/Project/BibleMap/frontend/src/MapView.jsx` 47행: `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}`
- ESRI 무료 타일은 비상업 제한과 사용량 제한이 있을 수 있음. ToS 검토 기록 없음

### [중간] Theographic 데이터 파이프라인이 외부 GitHub Raw URL에 직접 의존
- `/Users/calmonion/Project/BibleMap/backend/scripts/generate_event_verses.py` 28~29행: `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/...`
- 해당 레포가 이동·삭제·브랜치 변경되면 데이터 생성 파이프라인 전체가 중단. 로컬 스냅샷 없음

### [중간] protomaps GitHub Pages CDN 글꼴 의존
- `MapView.jsx`의 maplibre 스타일 설정에서 `https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf` 사용
- GitHub Pages CDN 가용성에 의존 — 서비스 중단 시 지도 레이블 글꼴 미표시

### [낮음] maplibre-gl 청크 1,027kB — 빌드 경고 상시 발생
- `/Users/calmonion/Project/BibleMap/frontend/vite.config.js`에서 `manualChunks`로 분리했으나 maplibre 청크 자체가 1MB 초과
- 빌드마다 `>500kB` 경고 출력. 2026-06-16 retro에서 "의도적 미해결"로 기록. 신규 회귀(앱/vendor 청크 비대)와 구분이 어려워질 수 있음

---

## 5. 알려진 데이터 한계

### 사건 데이터가 AD 57에서 끊김
- 2026-06-18 retro(`post-acts-apostolic-era-events`): theographic 데이터의 사건이 사도행전 이후 미포함
- 후기 서신(바울 2차 투옥 이후), 요한계시록, 포로귀환 이후 사건 연결 불완전

### 추정책 31권 중 14권 사건 연결 없음
- 2026-06-17/18 작업에서 31권 추정책 중 17권만 사건 연결 완료 (54%)
- 나머지 14권은 타임라인에 빈 📖 칩으로 표시됨

### 한국어 구절 본문 0.12% null
- 2026-06-16 retro(`getbible-verse-text-prebake`): event_verses 한국어 17570절 중 21건 null (versification 차이)
- 프론트에서 "원문이 없습니다"로 graceful 처리 중이나 미번역/미매핑 구절 존재

---

## 6. 반복 발생 프로세스 문제 (retro 누적)

### 코드 존재가 런타임 동작 보장 아님
- 2026-06-10 retro(`graphview-uat-bugfix`): "번들 포함 여부만 검증, 실제 클릭 동작 미확인" → UAT에서 버그 발견
- 2026-06-11 retro(`frontend-fetch-error-ui`): MapView의 fetch 에러 경로가 외부 타일 서버 미응답으로 런타임 미실행 검증

### 외부 API 프로브 도구와 실행 도구 불일치
- 2026-06-16 retro(`getbible-verse-text-prebake`): `curl` 프로브는 200, `urllib` 실행은 403 — User-Agent 불일치로 프로브가 오탐

### Neo4j 스키마 사전 확인 없이 계획 수립
- 2026-06-19 retro(`verse-events-pipeline`): "계획에서 `Event.verses`, `Book.verses` 프로퍼티가 있다고 전제했으나 실제로 두 프로퍼티 모두 없음"
- retro에서 "그릴링 단계에서 `MATCH (e:Event) RETURN keys(e) LIMIT 1`로 먼저 확인할 것"을 권고했으나 다음 계획에 반영됐는지 검증 메커니즘 없음
