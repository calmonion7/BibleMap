---
last_mapped_commit: cf024f8e79a4864f4489aca0b0fd4c84caebeaf6
mapped: 2026-07-11
---

# CONCERNS

현재 코드베이스에서 확인된 기술 부채·버그 위험·보안·성능·확장성·테스트 공백 목록.
각 항목은 HEAD(`cf024f8`)에서 실제 파일·라인, 그리고 가능한 경우 실행 중인 스택(`docker compose`, `localhost:8080`, 라이브 Neo4j)에 대한 실측으로 확인했다.

이번 갱신 배경: `cf024f8`(task#155·156)가 Night Atlas 다크 단일 디자인 리뉴얼을 전 화면에 적용했다(디자인 토큰 정본화, 무라벨 지형 지도, 양피지 구절 카드). 감사 보고서(`.forge/reports/design-audit.md`)의 HIGH·MEDIUM·LOW 항목 대부분이 해소됐으나 2건은 명시적으로 비범위 보류됐다(M4·L3, 아래 반영). 그 외 백엔드/데이터 계열 항목은 코드로 재확인해 유지했다.

---

## Tech Debt

**시드 파이프라인이 `deploy.sh`와 단절됨 (재현성 최대 리스크, 여전함):**
- `deploy.sh:37–63`의 [4/4] 단계는 `inject_ko_names.py` 하나만 재실행한다. `backend/scripts/`에는 `__init__.py` 제외 20개 스크립트가 있고, 그중 Neo4j 적재 스크립트(`load_theographic.py`, `load_authored_persons.py`, `load_authored_events.py`, `load_books.py`, `load_person_events.py`, `load_verse_events.py`)와 주입 스크립트(`enrich_place_coords.py`, `inject_book_context.py`, `inject_place_context.py`, `inject_person_traits.py`)는 배포에 포함되지 않는다.
- `.forge/adr/0012-contains-book-primary-occurrence-vs-citation.md`가 `CONTAINS_BOOK.primary` 라이브 마이그레이션을 일회성 스크립트로 적용했다고 명시("CONCERNS의 '재현 자동화 부재'는 이 태스크가 해소하지 않음") — 재시드 시 `load_books.py`/`load_person_events.py`가 `primary`를 세팅하지만 기존 라이브 데이터는 별도 마이그레이션으로만 맞춰졌다는 재현 경로가 있다.
- Neo4j 볼륨(`docker-compose.yml`의 `neo4j_data`)이 살아있는 한 재실행 불필요하지만, **볼륨 삭제·신규 서버 프로비저닝·컨테이너 재생성 시 전체 재적재 + primary 마이그레이션까지 재현해야** 한다. 정본화된 단일 실행 순서는 여전히 없다.

**시드 스크립트 실행 순서 암묵적 (여전함):**
- `load_person_events.py`는 `MATCH (b:Book ...)`, `MATCH (p:Place ...)`로 기존 노드를 참조하므로 `load_books.py`·`load_theographic.py`·`enrich_place_coords.py`·`load_authored_persons.py`가 먼저 실행돼야 관계가 생성된다. 잘못된 순서로 재시드하면 `MATCH`가 0건을 반환해 관계가 조용히 누락된다(에러 없음).

**대형 프론트엔드 컴포넌트 (라인 수 갱신):**
- `frontend/src/SidePanel.jsx` — 702줄. Person/Place/Event(간접)/Book/PeopleGroup 노드 타입 분기 렌더 + nodeId별 stale 무효화 패턴을 한 파일에서 관리(`node.label === 'Person'|'Book'|'Place'` 분기, `:305`·`:405`·`:572`).
- `frontend/src/App.jsx` — 426줄. `useStageNavigation.js`·`useNodeSelection.js`로 상태 일부 분리됐지만 여전히 상태 머신·fetch orchestration·레이아웃 분기가 공존.
- `frontend/src/TimelineView.jsx` — 358줄.
- `frontend/src/RelationsView.jsx` — 196줄. 레이아웃(레인 개요/초점 쌍/구절 모달) 3단이 한 파일에 공존하지만 각 분기가 짧고 독립적이라 SidePanel/App 수준의 복잡도는 아님.

**"큐레이션 13인" 주석이 현실과 계속 어긋남 (여전함, 신규 확인으로 범위 확대):**
- `backend/app/routes/persons.py:1`(docstring)·`:137`, `backend/app/routes/journey.py:6`·`:77`, `frontend/src/PersonHub.jsx:155`에 "13인"이 고정돼 있으나 `_ERA`는 여전히 **35개 slug**(`persons.py:20–56`), `data/person_events/`도 35개 json.
- **신규 확인**: `persons.py:211`(`_build_relations` docstring)의 "34인이면 withId를 해결"도 실제 35인과 어긋난다 — 같은 종류의 숫자 드리프트가 파일 하나에 두 번(13, 34) 서로 다른 값으로 박혀 있다. 다음 인물 추가 시마다 벌어지는 패턴이자, 이 숫자 자체가 이미 서로 안 맞는다는 신호.

**하드코딩 hex 색 잔존 (Night Atlas 토큰화 이후, 의도적 예외로 축소됨):**
- Night Atlas 토큰화(`cf024f8`) 이후 프론트 잔존 hex는 각 지점에 사유 주석이 붙은 의도적 예외들이다: 에러 적색(`frontend/src/SidePanel.jsx:123`, `frontend/src/PersonHub.jsx:206`, `frontend/src/TourList.jsx:28`, `frontend/src/BibleOverviewView.jsx:217` — 모두 "에러 색 — 방향서 토큰에 에러 시맨틱이 없어 하드코딩 유지"), 모달 스크림(`frontend/src/RelationsView.jsx:64` "전용 토큰 없어 값 유지"), Spinner color prop(`frontend/src/VerseLangTabs.jsx:19` "색상 프롭이 다양해 대비용 흰색 고정", `frontend/src/RelationsView.jsx:37` "color+'22' 문자열 결합이라 var() 미지원"). 이들 자체는 코드 리뷰 관점에서 문제라기보다, **디자인 토큰에 에러/시맨틱 적색이 정의돼 있지 않다는 소소한 부채**를 가리킨다 — 4곳에서 각자 `#f87171`/`#dc3545` 두 가지 다른 적색을 반복 정의 중이라, 토큰 하나(예: `--danger`)로 흡수하면 값 불일치(f87171 vs dc3545)도 함께 해소된다.
- `frontend/src/mapLayers.js`의 다수 hex(`:160`,`:184`,`:200-230`,`:250-440` 등)는 MapLibre GL 스타일 JSON의 paint 속성이라 CSS 변수를 못 쓰는 구조적 제약(JS 상수로 `theme.js`의 `NIGHT.gold`/`paperAccent` 등과 시각적으로는 동기화돼 있으나 import는 아님) — 별도 분류.

---

## Known Bugs

**`MapView.jsx` useEffect 의존성 경고 (HEAD 이전부터 존재, 라이브 확인):**
- `npm run lint` 실행 결과 이 저장소 유일의 ESLint 경고: `frontend/src/MapView.jsx:70` `React Hook useEffect has a missing dependency: 'onStopSelect'`. 맵 초기화 effect(`:21–70`, deps `[onSelectNode]`)가 `map.on('load', ...)` 콜백 안에서 `registerEventHandlers(..., onJourneyStopClick: onStopSelect)`(`:56`)로 `onStopSelect`를 참조하지만 deps 배열에 없다. 맵 인스턴스를 마운트당 1회만 만들려는 의도적 설계로 보이나, `eslint-disable` 주석 등으로 의도를 명시하지 않아 경고가 그대로 노출된다. 실제 동작 영향(클로저가 최신 `onStopSelect`를 못 보는 stale closure 여부)은 별도 검증 필요.

**히브리서 등 서신서의 Book 연대 범위 오표기 (라이브 확인, 수용된 한계):**
- `CONTAINS_BOOK`에 `primary`(발생 vs 인용) 구분을 도입(ADR-0012)해 사도행전·누가복음의 topEvents 오염은 해소했지만, "첫 참조=발생" 휴리스틱이 서신서의 신학적 회고 인용에는 오판정을 낳는다. 서신서는 CONTAINS_BOOK으로 연대를 정할 수 없다는 것이 근본 원인(authored_events 경로가 없는 책)이며, 별도 후속 없이는 해소 불가.

**topEvents "대표성 절단" 편향 잔존:**
- primary 필터가 다른 책의 인용 오염은 제거했지만, `backend/app/routes/nodes.py:238–260`의 정렬 로직(연도 오름차순 + `top_events[:10]` 하드 절단, `:249`)은 그대로다. 사도행전처럼 사건이 많은 책은 topEvents 10개가 전부 초반부(오순절~스데반 순교 등)에 몰리고, 후반 핵심 서사(바울 회심·선교여행·재판 등)가 절단된다. ADR-0012 Consequences에 "범위 밖(잔존)"으로 명시된 별개 curation 이슈.

**TODO/FIXME/HACK/XXX/@deprecated 마커는 `backend/app`·`backend/scripts`·`frontend/src` 전역 0건** (재확인).

---

## Design / Feature Gaps (design-audit.md 보류분)

**사건 상세 시트에 근거 구절 섹션 없음 (M4, 시각 문제가 아닌 기능 공백):**
- `frontend/src/SidePanel.jsx`는 `node.label === 'Person'`(`:305`)·`'Book'`(`:405`)·`'Place'`(`:572`) 세 분기만 있고 `'Event'` 전용 분기가 없다 — Place 시트 안에서 "이 장소의 사건" 목록을 통해서만(`:610–620`, `placeEventVerses`) 사건별 구절을 볼 수 있고, 사건 노드 자체를 선택해 시트를 열면 근거 구절이 없다(이웃 목록만). `.forge/reports/design-audit.md` M4가 "사건이 근거 구절의 척추인데 시트가 그걸 안 보여준다"고 지적했고, `.forge/retro/2026-07-10-design-renewal-1of2.md`가 "기능 추가라 이번 리뉴얼 비범위"로 명시적으로 후속 태스크 후보에 남겼다. `cf024f8` 이후도 미해결 확인됨.

**투어 카드 시각 앵커 부재 (L3, 비범위 보류):**
- `frontend/src/TourList.jsx`의 투어 카드가 텍스트만으로 구성돼 시대색 띠·아이콘 같은 시각 앵커가 없다. design-audit.md L3, 2/2 리뉴얼에서도 비범위로 남음("후속 후보").

---

## Security Considerations

**CORS `allow_origins=["*"]` (변동 없음):**
- `backend/app/main.py:44–49`. `allow_methods=["GET"]`·`allow_credentials=False`로 읽기 전용 제한. API는 nginx 뒤에서만 노출(`docker-compose.yml`에 api 서비스 host 포트 매핑 없음). 공개 읽기 API라 즉각 위험은 낮지만, 향후 인증 레이어 추가 시 명시적 오리진 화이트리스트 필요.

**Cypher 인젝션 표면 (현재 방어됨, 변동 없음):**
- `backend/app/routes/search.py:14–29`: 사용자값 `q`는 `$q` 파라미터 바인딩, f-string 삽입분은 상수 `SEARCH_LIMIT`뿐. `backend/app/routes/nodes.py`의 f-string도 상수 `NODE_NEIGHBOR_LIMIT`만 삽입. 안전.

**시크릿 취급 (현재 양호, 변동 없음):**
- `.env`는 `.gitignore:12`로 제외, git tracked인 env 파일은 `.env.example`·`frontend/.env.production`(비밀 아님)뿐. `docker-compose.yml`이 `${NEO4J_PASSWORD:?...}`로 필수화. 하드코딩된 시크릿 값 0건.

**사용자 제어 키 lru_cache — 무한 증가는 해소, 잔존 비대칭 유지:**
- `backend/app/routes/persons.py:145`(`_build_connections`)·`:208`(`_build_relations`)·`backend/app/routes/places.py:21`(`_place_to_persons`) 모두 `maxsize=256`(라이브 코드 재확인). 인증 없는 임의 문자열 대량 요청으로 인한 무한 메모리 누적(DoS)은 해소돼 있음.
- **잔존 비대칭(재확인)**: `places.py`의 정당한 key space(실제 좌표 있는 Place 노드 수)를 라이브 Neo4j로 재확인한 결과 여전히 **239개**(`MATCH (p:Place) WHERE p.latitude IS NOT NULL RETURN count(p)` → 239) — `maxsize=256`과 마진이 17뿐이라, 사용자가 여러 장소를 정상적으로 돌아다니기만 해도 캐시가 포화에 가까워지고 소수의 무의미한 id 요청만으로 정당한 항목이 축출되는 "캐시 스래싱"이 재현 가능하다(메모리 무한 증가는 아니므로 원래 DoS보다는 훨씬 약한 잔존 리스크). `persons.py`의 두 캐시는 정당한 key space가 큐레이션 35인으로 한정되어 마진이 넉넉해 이 리스크가 사실상 없다. id 검증(존재하는 Place/Person인지 확인 후에만 캐시) 없이 여전히 임의 문자열이 그대로 캐시 키가 된다는 점은 동일.

---

## Performance Bottlenecks

**9.4MB `event_verses` JSON 전체 인메모리 상주 (변동 없음):**
- `data/event_verses/events.json`가 9.4MB로, `backend/app/overlays.py:52–55`의 `event_verses()` `lru_cache(maxsize=1)`로 프로세스당 상주. `backend/Dockerfile`이 uvicorn 단일 워커(`--workers` 미지정)라 현재는 문제 잠재적이나, 워커 다중화 시 워커당 중복 배증.

**`_build_id_to_slug()`에 캐시 없음 (여전히 미해결):**
- `backend/app/routes/journey.py:18–30`: `lru_cache` 없이 요청마다 `_ERA`의 35개 slug JSON을 순회해 open/parse. `/person/{id}/journey`뿐 아니라 `tours.py`의 `_build_id_to_slug()` 재호출(`tours.py:117`)도 매 투어 상세 요청마다 이 무캐시 함수를 다시 돈다.

**places/persons 계열 lru_cache 상한 적용 확인 (변동 없음):**
- `places.py:21`·`persons.py:145`·`persons.py:208` 모두 `maxsize=256`(위 Security 섹션의 잔존 비대칭 참고).

**전역 노드 스캔 검색 (여전히 미해결):**
- `backend/app/routes/search.py:16–17`: `MATCH (n) WHERE n.nameKo CONTAINS $q OR toLower(n.name) CONTAINS toLower($q)` — 라벨·인덱스 미사용 전수 스캔.

**Esri World_Terrain_Base 고줌 열화 (신규 확인, 수용된 한계):**
- `frontend/src/MapView.jsx:34–38`: 무라벨 지형 타일 서비스는 z10 이상에서 "data not yet available" 플레이스홀더를 반환하므로 `maxzoom: 9`로 z9 타일을 오버줌 처리한다(`:37` 주석). `.forge/retro/2026-07-11-design-renewal-2of2.md`가 "타일 크기 curl 프로브(z5~10)로 플레이스홀더 경계 확정" 과정을 기록. 결과적으로 사용자가 확대할수록(z10+) 화면은 z9 타일이 흐리게 늘어난 상태로 고정되며, 이는 근본적으로 무료 Esri 서비스의 데이터 범위 한계라 프론트 코드로 해결 가능한 성능 문제가 아니라 수용된 한계다.

---

## Fragile Areas

**인물 관계가 `slug` 문자열 매칭에만 의존 — theographic_id 미사용 (변동 없음):**
- `data/person_relations/relations.json`의 각 endpoint는 `{nameKo, slug}`만 담는다. `backend/app/routes/persons.py:209–237` `_build_relations`가 `slug_to_id.get(other["slug"])`로 `withId`를 해결한다. slug 오타·drift 시 여정 점프가 `null`로 조용히 실패하지만 에러는 없다. 3중 slug 소스(파일명·`_ERA`/`_NAME_KO`·relations endpoint) 일치를 강제하는 스키마·테스트는 여전히 없다.

**관계 뷰 `type`/`valence` 값이 프론트 상수와 암묵 결합 (변동 없음):**
- `frontend/src/RelationsView.jsx:12`의 `TYPE_ICON`(9종)·`:13` `TYPE_ORDER`와 `theme.js:25`의 `VALENCE_COLOR`(3종)가 데이터 값과 하드코딩으로 짝지어져 있다. 새 `type`/`valence` 추가 시 `TypeIcon`이 `null`(`:18`)·중립색 폴백(`VALENCE_COLOR[ph.valence] ?? VALENCE_COLOR.중립`, `:70`·`:123`·`:179`)으로 조용히 뭉개지는 구조는 그대로.

**`TimelineView.personFilter`는 반드시 `Set`이어야 함 — 타입 계약 미강제 (변동 없음):**
- `frontend/src/TimelineView.jsx:103`에서 `activePersonFilter.has(ev.id)` 직접 호출. `:21–22`의 `import.meta.env.DEV` 가드는 개발 빌드에서만 `console.error`, 프로덕션 빌드에서는 Array 전달 시 여전히 크래시. `App.jsx:54–64`가 `personEventIds`를 `useState(null) + useEffect`로 명시적으로 `Set`만 만들도록 관리해 현재 호출 경로는 안전하지만, 타입 계약 자체가 코드로 강제되는 것은 아니다.

**`startDate`/연도 파싱 로직이 네 곳에 중복 (변동 없음):**
- `frontend/src/dates.js:4–12` `parseYear()`, `backend/app/routes/nodes.py:238–248`(추정 라인, `_year` 내부 헬퍼) 동일 로직, `backend/scripts/load_books.py:56–68` `_parse_year()`(같은 규칙의 세 번째 사본), `frontend/src/RelationsView.jsx:44` `const era = y => y < 0 ? \`BC ${-y}\` : \`AD ${y}\`` — approxYear가 이미 정수라 파싱 자체는 없지만 BC/AD 표기 규칙은 네 번째 사본.
- `load_books.py:65–68`에 회귀 방지 `assert` 4개(`_parse_year("-1451-01") == -1451` 등, 라이브 재확인)가 있다 — import 시점 실행, CI 아님. 이 로직을 공유 모듈로 추출하진 않아 넷 중 셋(`dates.js`/`nodes.py`/`RelationsView.jsx`)은 여전히 무보증이다.

**Neo4j 인덱스 생성 실패 시에도 서비스는 계속 기동 (변동 없음):**
- `backend/app/main.py:37–40`: `except Exception:`이 `logger.exception(...)`으로 스택트레이스를 남기지만, 인덱스 없이 계속 기동하는 동작 자체는 그대로 — 실패해도 서비스는 뜨고 전수 스캔 성능 저하만 남는다.

**프론트 stale 응답 무효화 패턴의 수동 관리 (변동 없음):**
- `frontend/src/SidePanel.jsx:68–111`: 3개의 독립된 `cancelled` 플래그 + `nodeId`/`state.id` 비교로 stale 판별(노드 fetch·장소 경유 인물·인물 연결 각각). `frontend/src/RelationsView.jsx:26–33`·`frontend/src/App.jsx:55–64`도 같은 패턴을 반복 구현. 신규 비동기 fetch 추가 시 이 패턴을 빠뜨리면 이전 노드/인물 데이터가 잠깐 노출된다 — 공유 훅으로 추출되지 않음.

---

## Deployment / Ops Risks

**프론트 `:8080`은 `frontend/dist` 정적 마운트 — HMR 아님 (변동 없음):**
- `docker-compose.yml`의 nginx 서비스 `- ./frontend/dist:/usr/share/nginx/html:ro`. 소스만 고치고 `npm run build`를 안 하면 `:8080`은 이전 빌드를 계속 서빙하며 에러 없음.

**API `:8000` 외부 미노출 (변동 없음):**
- `docker-compose.yml`에 api 서비스 host 포트 매핑 없음. `nginx/nginx.conf`의 `location /api/`로만 접근.

**nginx 속도 제한 없음 (변동 없음):**
- `nginx/nginx.conf`에 `limit_req_zone`/`limit_req` 미설정. lru_cache가 256으로 상한 설정됐어도(위 Security 참고), rate limit 부재는 places.py 캐시 스래싱류 잔존 리스크를 그대로 악화시킬 수 있는 조합이다.

---

## Scaling Limits

**단일 인스턴스 스택, 인메모리 캐시 공유 불가 (변동 없음):**
- neo4j 1 + api 1(uvicorn 단일 워커) + nginx 1 컨테이너. API의 `lru_cache`들(`overlays.py`·`persons.py`·`places.py`, 상한 1 또는 256)은 프로세스 로컬이라 다중 워커/컨테이너 확장 시 인스턴스별 중복·불일치. 무효화 수단이 앱 재시작뿐인 것도 그대로.

---

## Dependencies at Risk

**Theographic 데이터를 GitHub `master` HEAD에서 미고정 fetch (변동 없음):**
- `load_theographic.py`·`load_books.py`·`generate_event_verses.py`·`generate_verse_events.py`·`generate_book_context.py`·`generate_person_traits.py`가 `https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/*.json`을 커밋 SHA 고정 없이 직접 다운로드. 업스트림 스키마 변경 시 재시드 결과 변질 또는 `KeyError` 중단 위험.

**절 본문 프리베이크가 빌드타임 getbible 외부 호출에 의존 (변동 없음):**
- `backend/scripts/generate_verse_text.py`의 기본 UA 403 우회 로직(`_UA`)이 여전히 필요. 새 절 추가마다 getbible 가용성·정책 변경에 의존.

**Neo4j 이미지 메이저 버전만 고정 (변동 없음):**
- `docker-compose.yml`의 `image: neo4j:5`. `neo4j:5.x.y` 고정 권장.

**프론트 의존성 버전 (수치 갱신):**
- `frontend/package.json`: `react@^19.2.6`, `react-dom@^19.2.6`, `maplibre-gl@^5.24.0`, `lucide-react@^1.17.0`. `maplibre-gl`은 지도 렌더 핵심(Esri World_Terrain_Base 무라벨 타일 + 래스터 paint), `lucide-react`는 `RelationsView.jsx:12`의 관계 유형 아이콘 9종에 직접 의존. lockfile 유지로 재현성 확보 중.

---

## Missing Critical Features

**시드 전체 재현 자동화 부재 (변동 없음):**
- `deploy.sh`는 여전히 프론트 빌드·API 이미지 빌드·컨테이너 재시작·`inject_ko_names.py`만 수행. ADR-0012가 `primary` 라이브 마이그레이션도 "이 태스크가 재현 자동화를 해소하지 않음"이라고 명시적으로 남겨, 재현 갭이 줄지 않고 오히려 재현해야 할 단계(마이그레이션)가 하나 늘었음을 스스로 기록했다.

**관계·인물 데이터 정합성 검증기 부재 (자동화 여전히 없음):**
- slug 3중 소스 일치·type/valence 매칭·approxYear 정수성·tours stops 참조 무결성 등을 기계검증한 이력은 있으나(`.forge/reports/`는 git 미추적 스크래치 디렉터리), 레포에 커밋된 검증 스크립트나 CI 연동은 없다. `data/person_relations/AUTHORING.md:64` "규칙 8 검증 파이프라인"도 사람이 5단계를 수동 실행하는 체크리스트다. 다음 저작 사이클에서 slug/타입 드리프트(예: 위 "13인"/"34인" 불일치)가 재발해도 자동으로 잡히지 않는다.

**사건 시트에 근거 구절 섹션 없음 (Design/Feature Gaps 섹션 M4와 동일 항목, 상호 참조):**
- 위 "Design / Feature Gaps"에 상세 — 기능 공백으로 명시적으로 기록된 후속 태스크 후보.

---

## Test Coverage Gaps

- `*.test.*`/`*.spec.*` 파일(`node_modules` 제외) 0건, pytest/vitest/jest 설정·`conftest.py`·`pytest.ini`·`vitest.config.*` 전무(재확인). `frontend/package.json` scripts에 test 없음(dev/build/lint/preview만).
- 이 저장소에서 유일하게 존재하는 자동 검증은 `backend/scripts/load_books.py:65–68`의 `assert` 4개(`_parse_year` 회귀 방지, import 시점 실행)와 `generate_verse_text.py`의 `approxYear` 정수 assert뿐 — 둘 다 CI에 연결되지 않고, 스크립트를 수동 실행해야만 트립된다.
- 특히 위험 높은 미검증 지점:
  - `frontend/src/dates.js:4–12` `parseYear` · `backend/app/routes/nodes.py` `_year` · `frontend/src/RelationsView.jsx:44` `era` · `backend/scripts/load_books.py:56–68` `_parse_year` — BC/AD 연도 파싱·표기 로직 4중 사본 중 3곳은 assert도 없다.
  - `backend/app/routes/persons.py:209–237` `_build_relations` — slug↔id 매핑 계약, withId null 판정, note 폴백 로직 미검증.
  - `backend/app/routes/nodes.py` Book 분기 — `rel.primary` 필터·topEvents 정렬/절단 로직(서신서 엣지케이스 포함) 미검증.
  - `backend/app/routes/tours.py:56–72` `_build_event_index` — 중복 eventId 경고 가드 미검증.
  - `backend/app/overlays.py:14–31` `_resolve`/`_resolve_dir`/`_load` — 파일 부재 경로의 로깅 대칭 미검증.
  - `frontend/src/MapView.jsx` 맵 초기화/personId·selectedNode 전환/여정 정차지 프레이밍 로직(위 "Known Bugs"의 deps 경고 포함) — Playwright 수동 검증에만 의존.
- UI 검증은 Playwright 수동 실행(로컬)에만 의존, CI 미연동. BC/AD 표기 회귀, slug 3중 소스 드리프트, relations type/valence 미매칭, `rel.primary` 세팅 누락, 시드 순서 오류로 인한 관계 누락, `personFilter` 타입 계약 위반(프로덕션 빌드) 모두 자동으로 감지되지 않는다.
