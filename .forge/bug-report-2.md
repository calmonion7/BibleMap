# BibleMap 버그 리포트 — 2차 사이클 (task#263)

작성: 2026-08-02 · 대상 HEAD `2602b50`(작업트리에 `frontend/src/PersonMiniCard.jsx`·`mapGeo.js`·`mapLayers.js` 변경 있음 — 이번 리포트가 인용하는 파일들과는 무관, 인용 라인은 모두 HEAD 기준)
방법: 6렌즈 finder 병렬 발굴(원시 6건) → dedup(4건, 중복 2건 제외) → finding별 독립 적대적 검증(코드 재추적 + Neo4j/curl/Playwright 라이브 실측) → **confirmed 4건** + task#262에서 이미 재현 확인된 1건(데스크톱 자기시트 leak, HIGH)을 이관 수록 = **confirmed 총 5건** · refuted 0건
규칙: confirmed는 캡 없이 전건 수록(이번 사이클 5건 전부). task#262 이관분 중 MEDIUM/LOW 4건(모바일 관계뷰 시트 미닫힘·`parseYear` 숫자입력·`TimelineView` 동명 함수·스윕 커버리지 공백)은 이미 판정이 가볍거나(비버그·미발현) 정밀한 파일:줄 근거가 부족해 정식 상세 절 대신 말미 백로그 후보 목록으로 정리했다(고치지 않는다). 이 리포트는 발견·검증·보고만 — 코드 수정은 finding별 후속 태스크.

## 요약

| # | 심각도 | 렌즈 | 위치 | 증상 |
|---|--------|------|------|------|
| 1 | HIGH | 백엔드 정합성 | `backend/app/routes/family.py:39-67`, `backend/app/routes/family.py:233-240` | 가계도 API가 손큐레이션 역할 라벨을 `theographic_id`가 아니라 `nameKo` 문자열만으로 매칭해, 동명이인 노드에 완전히 다른 서사의 역할이 잘못 부여된다 |
| 2 | HIGH | 프론트 상태관리 | `frontend/src/ExploreStage.jsx:56` (근본원인 `frontend/src/App.jsx:312`) | 투어 자동재생 중 헤더 리본으로 이탈했다가 뒤로가기로 복귀하면 재생 idx·playing 상태가 리셋되어 '재생 종료' 컨트롤과 진행률이 사라진다 |
| 3 | MEDIUM | 프론트 정합성(경쟁 상태) | `frontend/src/WordDistributionView.jsx:89-93` | 단어 분포 페이지에서 책을 전환하며 같은 단어를 연속 클릭하면, 이전 책의 늦은 응답이 현재 책 화면 위에 도착해 구절 레이어를 다른 책 성구로 조용히 덮어쓴다 |
| 4 | HIGH | 배포/인프라 | `deploy.sh:83`, `docker-compose.yml:25-34` | 자동 배포 경로가 `nginx.conf` 변경을 절대 반영하지 못한다 — nginx는 이미지 빌드가 없고 바인드 마운트 스펙이 불변이라 Compose가 재생성하지 않는다 |
| 5 | HIGH | 프론트 정합성(task#262 이관) | `frontend/src/useStageNavigation.js:179`, `frontend/src/useStageNavigation.js:346`, `frontend/src/App.jsx:357` | `handleSelectPerson`의 기본 view=`'map'`과 자기시트 억제 조건이 `exploreView==='intro'`에만 걸려, intro를 명시하지 않고 `selectPerson`을 호출하는 모든 경로(데스크톱)에서 목적지 화면에 자기 자신의 상세 시트가 열린다 |

---

### 1. [HIGH] `backend/app/routes/family.py:39-67`, `backend/app/routes/family.py:233-240` — 가계도 API가 nameKo만으로 매칭해 동명이인에게 다른 서사의 역할이 잘못 부여된다

- **렌즈**: 백엔드 정합성 · 적대적 검증 **CONFIRMED**
- **증상**: 가계도(`/person/{id}/family`) API가 `person_relations.json`의 손큐레이션 역할 라벨을 `theographic_id`가 아니라 `nameKo` 문자열만으로 매칭해, 동명이인 노드에게 완전히 다른 서사의 역할이 잘못 부여되고 `FamilyTree.jsx`가 이를 최우선으로 렌더링한다.
- **근거**: `backend/app/routes/family.py:39-67`(`_family_role_pairs`)이 `person_relations/relations.json`의 `endpoints`에서 `ka, kb = a.get("nameKo"), b.get("nameKo")`(59행)로 `frozenset({ka, kb})` 키를 만들고, `role`을 `m[ka] = a["role"]`(63-65행)처럼 nameKo 문자열에 그대로 붙인다 — `endpoints`에 이미 있는 `slug`(정본 식별자)는 전혀 참조하지 않는다. `get_person_family()`(`backend/app/routes/family.py:233-240`)도 재조회 시 `focus_ko = nodes.get(node_id, {}).get("nameKo")`(233행)와 `role = pairs.get(frozenset({n["nameKo"], focus_ko}), {}).get(n["nameKo"])`(240행)로 동일하게 nameKo만 쓴다. 프론트 소비처 `frontend/src/FamilyTree.jsx:115-117`(`roleLabel`)은 `if (model.roles[id]) return model.roles[id]`를 그래프 구조·gender 폴백보다 최우선으로 반환하고, `:170-171`의 앵커 칩 분기가 `tag`(=roleLabel 결과)를 그대로 화면에 출력한다.
- **재현**:
  1. cypher(읽기전용): `MATCH (p:Person) WHERE p.nameKo IS NOT NULL WITH p.nameKo AS n, collect(p.theographic_id) AS ids WHERE size(ids)>1 RETURN n, size(ids)` → 205개 이름 중 다수 중복(요셉 6명·야곱 2명 등).
  2. `curl -s localhost:8080/api/person/reco9bEDv9NKzhzvv/family`(구약 야곱) → 응답 `"roles": {"recqIoG1fkaNWJ1y0": "아버지", "recz2xTRGz9XZD6dT": "편애한 아들"}`.
  3. `recz2xTRGz9XZD6dT`의 name은 `"Joseph (Mary's Husband)"`(신약, 요셉[마리아 남편])로 구약 요셉이 아님 — 원본 `data/person_relations/relations.json`의 해당 role="편애한 아들"은 `endpoints`에 `slug:"jacob"`/`slug:"joseph"`가 명시돼 있고 phases가 창 37:3(채색옷)·37:34(애통)·46:29(재회)·48:15(축복)로 명백히 **구약 족장 야곱↔아들 요셉** 서사다.
  4. UI 경로: 신약 요셉(`joseph_of_nazareth`, curated) 가계도 → '야곱' 칩 탭 → 미니 카드 → 재중심화(`frontend/src/FamilyTree.jsx:131` 주석, `frontend/src/FamilyTree.jsx:193` `onRecenter` prop, `frontend/src/FamilyTree.jsx:476` 카드 전달) → 화면이 구약 야곱 중심 트리로 전환 → 자녀 칩 '요셉'(신약, 앵커 있음) 아래 '편애한 아들' 라벨 표시.
- **검증 요지**: 4단계 라이브 실측(cypher 동명이인 스캔 → cypher 관계 확인 → curl 실응답 → 원본 relations.json의 slug/phases 대조)이 finding의 정확한 id 2개·role 문자열·라인 전부와 100% 일치해 반증 실패. `data`에 이미 정답 식별자(`slug`)가 있는데도 `backend/app/routes/family.py:59`가 이를 버리고 nameKo만 키로 써서 유출이 발생함을 원본 데이터 레벨까지 추적 확인.
- **제안 수정방향**: `_family_role_pairs()`가 `endpoints`의 `nameKo` 대신 `slug`(이미 데이터에 존재)를 theographic_id로 해석해 frozenset 키를 만들도록 변경(`persons._build_list()`의 slug→id 테이블 재사용 등). `get_person_family()`의 룩업(:240)도 `n["nameKo"]`/`focus_ko` 대신 노드의 실제 `theographic_id`로 pairs를 조회하도록 수정.
- **수정 완료(S4)**: `backend/app/routes/family.py`의 `_family_role_pairs()`(구 39-67행)가 `_id_to_slug()`를 역인덱스(slug→id)로 뒤집어 endpoints의 `slug`를 theographic_id로 해석하도록 변경 — **양 endpoint 모두 slug가 있는 관계만** 키를 만든다(원본 데이터 실측: 가족 관계 46건 중 role이 실제로 붙은 20건은 전부 양쪽 slug가 있는 10개 관계 — slug 없는 쪽엔 role이 결코 존재하지 않아 "양쪽 slug 필수"로 좁혀도 기존 role 표시가 하나도 유실되지 않음). `get_person_family()`(구 233-240행)의 룩업도 `nameKo` 대신 노드의 실제 `theographic_id`로 `pairs`를 조회하도록 교체.
  - **변경 파일**: `backend/app/routes/family.py`(`_family_role_pairs()` 본문 + `get_person_family()`의 role 조회 블록).
  - **재현(수정 후, cypher/curl 실측)**: cypher로 재확인한 결과 신약 계보의 "야곱"(Matthew 1의 마리아 남편 요셉의 아버지, `theographic_id=reco9bEDv9NKzhzvv`)은 큐레이션 야곱(`recsU2ZSdzBvDqzgI`)과 **다른 노드**이고, 그 자손은 `recz2xTRGz9XZD6dT`("Joseph (Mary's Husband)", seal_slugs.json상 slug=`joseph_of_nazareth`)임을 확인. 수정 전엔 이 신약 계보 야곱의 `/family` 응답에 `roles: {"...": "편애한 아들"}`이 유출됐을 것(구약 야곱↔요셉 관계의 nameKo 충돌). 수정 후 `curl -s localhost:8080/api/person/reco9bEDv9NKzhzvv/family`의 `roles` 필드 = `{}`(빈 객체, 오염 없음). 반면 **진짜** 큐레이션 야곱 `curl -s localhost:8080/api/person/recsU2ZSdzBvDqzgI/family`의 `roles` = `{"recqIoG1fkaNWJ1y0": "아버지", "rechuDYJoK32gmrME": "편애한 아들"}` — `recqIoG1fkaNWJ1y0`은 큐레이션 이삭(slug=isaac, 야곱의 실제 아버지), `rechuDYJoK32gmrME`은 큐레이션 요셉(slug=joseph, 야곱의 실제 아들)의 정확한 id로, 정상 role 표시가 그대로 유지됨을 확인 — 회귀 없음.
  - **동형 버그 스캔**: `grep -rn "frozenset" backend/app/`으로 전수 확인 — 이 파일의 이 두 지점 외 동일 패턴(frozenset+nameKo 매칭) 없음. `backend/app/routes/persons.py`의 `_build_relations()`는 이미 slug 기반(`me_slug = id_to_slug.get(node_id)`)이라 동형 버그 아님.
  - **검증**: `docker compose up -d --build api` 재빌드·재시작 후 위 curl 실측. 백엔드 코드만 변경, 프론트 무변경.

### 2. [HIGH] `frontend/src/ExploreStage.jsx:56`(근본원인 `frontend/src/App.jsx:312`) — 투어 자동재생 중 이탈→뒤로가기 복귀 시 재생 상태 소실

- **렌즈**: 프론트 상태관리 · 적대적 검증 **CONFIRMED**
- **증상**: 투어 자동재생 중 헤더 리본(성경책/인물)으로 이탈했다가 브라우저 뒤로가기로 복귀하면 재생 idx·playing 상태가 리셋되어 '재생 종료' 컨트롤과 진행률이 사라지고 '투어 재생' 시작 버튼으로 되돌아간다.
- **근거**: `frontend/src/App.jsx:312` `{activeStage === 'explore' && (<ExploreStage .../>)}`가 `activeStage`가 바뀔 때마다 `ExploreStage` 전체를 마운트/언마운트한다. `frontend/src/ExploreStage.jsx:56` `const playback = useTourPlayback(journeyStops)`가 그 안에서 호출되며, `frontend/src/useTourPlayback.js:13-14` `const [idx, setIdx] = useState(null)`/`const [playing, setPlaying] = useState(false)`가 로컬 `useState`다 — App 레벨로 끌어올려진 적이 없어 언마운트 시 그대로 소실된다.
- **재현**(Playwright, `/opt/homebrew/bin/python3`):
  1. `http://localhost:8080/#/tour/david-united-kingdom` 직접 진입 → '투어 재생' 클릭 → 3.2초 대기 → 측정: exit_btn_count=1, play_btn_count=0, idx 텍스트='1/37'(해설 카드·컨트롤 4버튼 확인).
  2. 헤더 리본 '성경책' 클릭 → URL `#/books`로 이동(개요 화면 렌더 확인).
  3. `page.go_back()` → 3초 대기 → URL이 `#/tour/david-united-kingdom`으로 정확히 복귀(popstate 정상 동작).
  4. 측정: exit_btn_count=0, play_btn_count=1, idx 텍스트=None. 스크린샷(`step4_after_back.png`)은 좌측 여정 리스트·투어명은 보존된 채 지도 상단에 '투어 재생' 시작 버튼만 뜬 상태를 확인 — `journeyStops`/`activeStopIdx`(App 소유)는 생존하고 `playback`(ExploreStage 로컬 소유)만 소실됨을 시각적으로 확인. console 에러 없음(조용한 상태 유실).
- **검증 요지**: 정적 확인(`frontend/src/App.jsx:312` 조건부 마운트, `frontend/src/useTourPlayback.js:13-14` 로컬 state)과 라이브 재현이 모두 finding의 정확한 메커니즘과 일치. 반증 시도(리그레션 전/후 대조)는 옵션이라 생략했으나 현재 코드의 실측 재현만으로 판정에 충분.
- **제안 수정방향**: `useTourPlayback`의 `idx`/`playing` state를 App 레벨(`useExploreJourney` 또는 형제 훅)로 끌어올려 `journeyStops`/`activeStopIdx`와 동일한 수명 규약(ExploreStage 언마운트에도 생존)을 적용. 최소 변경: App.jsx에서 `useTourPlayback(journey.journeyStops)`를 호출해 `ExploreStage`에 `playback` prop으로 내려주고, `frontend/src/ExploreStage.jsx:56`의 로컬 호출 제거.
- **수정 완료(S4)**: 제안 수정방향대로 최소 변경 적용 — `frontend/src/App.jsx`에서 `useTourPlayback(journey.journeyStops)`를 호출해 `playback`을 `ExploreStage`에 prop으로 전달, `frontend/src/ExploreStage.jsx:56`의 로컬 `const playback = useTourPlayback(journeyStops)` 호출은 제거하고 props 구조분해로 대체(내부 `playback.idx`/`.active`/`.start` 등 소비 코드는 무변경).
  - **변경 파일**: `frontend/src/App.jsx`(import + 훅 호출 + prop 전달), `frontend/src/ExploreStage.jsx`(로컬 훅 호출 제거, prop 수신, 관련 주석 갱신).
  - **재현(수정 후, Playwright 데스크톱 1400×900 + 모바일 390×844 둘 다 확인)**: 리포트의 원 재현 절차 그대로 재실행. `#/tour/david-united-kingdom` → '투어 재생' 클릭 → 3.2초 대기(측정: exitBtnCount=1, playBtnCount=0, idx='1/37', 데스크톱·모바일 동일) → 헤더 리본 '성경책' 클릭(`#/books`로 이동, 확인) → `page.go_back()` → 3초 대기 → URL이 `#/tour/david-united-kingdom`으로 정확히 복귀 → **수정 후 측정: exitBtnCount=1, playBtnCount=0, idx='2/37'**(데스크톱·모바일 동일 결과) — '재생 종료' 컨트롤과 진행률이 그대로 살아있고, 이탈 동안에도 자동재생 타이머가 계속 돌아 idx가 1→2로 전진했음까지 확인(App이 언마운트 없이 계속 소유하고 있었다는 직접 증거). 스크린샷: `/tmp/pw263/item2_step3_after_back.png`(데스크톱, 재생 카드 "2/37 사울 야베스 길르앗 구원" + 재생/일시정지·이전/다음·종료 4버튼 모두 렌더), `/tmp/pw263/mobile_item2_step3.png`(모바일 동일 상태).
  - **검증**: `npm run build` 통과, ESLint 신규 위반 없음(`npx eslint src/App.jsx src/ExploreStage.jsx` 클린).

### 3. [MEDIUM] `frontend/src/WordDistributionView.jsx:89-93` — 책 전환 중 늦은 응답이 스테일 가드를 통과해 구절 레이어를 오염

- **렌즈**: 프론트 정합성(경쟁 상태) · 적대적 검증 **CONFIRMED**
- **증상**: 단어 분포 페이지에서 책을 전환하며 같은 텍스트의 단어(예: '하나님')를 연속 클릭하면, 이전 책에서 보낸 늦은 응답이 현재 책 화면 위에 도착해 구절 레이어를 다른 책의 성구로 조용히 덮어쓴다(헤더는 현재 책 제목 유지, 본문만 오염).
- **근거**: `openWord`(:89-93) — `apiGet(...).then(({ total, verses }) => setVerseView(v => (v && v.word === word ? { ...v, loading: false, total, verses } : v)))`(92행). 스테일 가드가 `v.word === word`로 **단어 텍스트만** 비교하고 `bookId`를 비교하지 않는다 — 두 책에 같은 단어가 있으면 늦게 도착한 이전 책 응답이 가드를 통과해 `verseView`를 덮어쓴다.
- **재현**(Playwright): `page.route('**/api/words/**/verses**', handler)`로 URL에 `/words/recIFusdNl6d8dj3L/verses`(창세기)가 포함되면 `route.continue()` 전에 2.5초 지연 주입 → `#/words/recIFusdNl6d8dj3L` 접속 → '하나님' 클릭(지연 fetch 발사) → 0.3초 후 `<select>`에서 출애굽기(`recsr5TGvFGOwA5SZ`) 선택 → 출애굽기 클라우드 재로드 후 '하나님' 재클릭(즉시 응답) → t≈0.6초 스냅샷: 본문에 '출 1:'만 존재(정상) → t≈3.1초(지연 응답 도착 후) 스냅샷: 본문이 '창 1:'로 바뀌고 '출 1:'은 사라짐, 헤더는 '출애굽기 단어 분포' 그대로. 스크립트: `/tmp/pw_word_race.py`, 스크린샷: `/tmp/pw_word_race_final.png`.
- **검증 요지**: 라이브 Playwright 재현(정적 독해가 아님)으로 이전 세션의 정적 근거를 그대로 뒷받침 — 반증 실패.
- **제안 수정방향**: `openWord`에 요청 시점의 `bookId`를 캡처해 가드에 포함(`const reqBookId = bookId; ... setVerseView(v => (v && v.word === word && reqBookId === bookId ? ... : v))`) — 또는 78-87행 effect처럼 `AbortController`로 book 전환 시 이전 `openWord` 요청도 abort. 가장 간단한 방법은 `verseView` 객체에 `bookId` 필드를 같이 저장해 가드에서 `v.bookId === bookId`도 함께 비교.

### 4. [HIGH] `deploy.sh:83`, `docker-compose.yml:25-34` — 자동 배포 경로가 nginx.conf 변경을 절대 반영하지 못한다

- **렌즈**: 배포/인프라 · 적대적 검증 **CONFIRMED**
- **증상**: `deploy.sh`의 자동 배포 경로(`docker compose up -d api nginx`)가 `nginx.conf` 변경을 절대 반영하지 못한다 — nginx는 이미지 빌드가 없고(`nginx:alpine` 고정) Compose가 서비스 정의(바인드 마운트 스펙) 불변으로 판단해 재생성하지 않는다.
- **근거**: `deploy.sh:83` `docker compose -p biblemap up -d api nginx`. `docker-compose.yml:25-34` `nginx: image: nginx:alpine ... volumes: - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro`(단일파일 바인드 마운트) — Compose는 서비스 정의(이미지 태그·마운트 스펙 문자열)가 그대로면 컨테이너를 재생성하지 않는다.
- **재현**:
  1. `gh run list --workflow=deploy.yml --limit 6` 후 최근 4건(30705594890/30699567178/30694505681/30693997655)에 대해 `gh run view <id> --log | grep -iE 'Container biblemap-(nginx|api)-1'` — 4/4 모두 nginx는 `Running`(no-op)만, api는 `Recreate→Recreated→Starting→Started` 전체 시퀀스.
  2. 결정적 사례: `30699567178`은 push에 `c8c884f`(`nginx.conf`에 gzip 블록 추가, task#260)가 포함된 실행이었는데도 로그는 `nginx-1 Running`(no-op) — 즉 nginx.conf 내용이 실제로 바뀐 배포 실행에서도 자동 경로가 nginx를 재생성하지 않음.
  3. `docker inspect biblemap-nginx-1 --format '{{.Created}}'` = `2026-08-01T11:14:41Z`, `c8c884f` 커밋 시각(`20:16:51+09:00`=UTC `11:16:51Z`)보다 **먼저** 생성됨, 해당 push(=배포 실행)는 `12:22:37Z` — nginx 컨테이너가 커밋·push보다도 먼저 만들어졌다는 것은 gzip이 반영된 계기가 이 배포가 아니라 그 이전 수동 개입(로컬에서 파일 먼저 바꾸고 `--force-recreate`로 확인 후 커밋)이라는 뜻.
  4. `crontab -l` 비어있음, `launchctl list`에도 GitHub Actions 러너 서비스만 있어 별도 nginx 재생성/reload 잡 없음(원 보고 주장대로).
- **검증 요지**: 실제 배포 실행 로그 4건 전량과 컨테이너 생성 시각 대조로 CONCERNS.md의 "해소(task#260)" 판정이 자동 파이프라인이 아닌 우연한 수동 개입 덕분이라는 finding의 승격 주장을 확정. 반증 실패.
- **제안 수정방향**: `deploy.sh:83` 뒤에 `docker compose -p biblemap up -d --force-recreate nginx` 한 줄 추가(nginx는 상태 없는 정적 서빙 컨테이너라 매 배포 강제 재생성해도 비용이 거의 없음). 또는 `nginx.conf`를 바인드 마운트 대신 커스텀 이미지 빌드(Dockerfile COPY)로 바꿔 파일 내용이 이미지 해시에 반영되게 하면 Compose가 자연히 Recreate를 트리거함.
- **수정 완료(S4)**: 제안 수정방향 중 첫 번째(최소 변경)를 그대로 적용 — `deploy.sh`의 `docker compose -p biblemap up -d api nginx` 한 줄을 `docker compose -p biblemap up -d api` + `docker compose -p biblemap up -d --force-recreate nginx` 두 줄로 분리(api는 이미지 해시 변경에 따른 기존 조건적 Recreate 그대로, nginx만 매 배포 강제 재생성). 변경 이유를 스크립트에 주석으로 남김.
  - **변경 파일**: `deploy.sh`(`[7/7] 컨테이너 재시작` 블록).
  - **재현/검증**: 이 단계 지시상 `deploy.sh` 자체 실행·커밋·push는 금지라 실제 배포 파이프라인을 라이브로 재구동해 재현하지 않았다 — `bash -n deploy.sh`로 문법 유효성만 확인(통과). `--force-recreate`는 Docker Compose 문서상 서비스 정의 diff와 무관하게 항상 컨테이너를 재생성하는 결정적 플래그라 별도 실측 없이도 "nginx.conf가 바뀌었는데 no-op으로 스킵됨" 원인(정의 불변 시 Compose가 재생성 필요성을 못 감지)을 구조적으로 우회한다. **로컬 :8080/nginx 컨테이너 자체는 이 수정과 무관하므로 재기동하지 않았다**(수정 대상은 배포 스크립트 로직이며, 이번 사이클에서 nginx.conf 자체를 바꾸지 않아 실서비스에 반영할 변경분도 없음).
  - **남은 한계**: 다음 실제 배포(push→러너)에서 로그에 `nginx-1 Recreate`가 찍히는지 확인해야 완전한 라이브 검증이 된다 — 이번 사이클은 스크립트 로직 수정 + 정적 검증까지만.

### 5. [HIGH, task#262 이관·재현확인] `frontend/src/useStageNavigation.js:179`, `frontend/src/useStageNavigation.js:346`, `frontend/src/App.jsx:357` — 데스크톱 목적지 화면에 자기 자신의 상세 시트가 열리는 leak

- **렌즈**: 프론트 정합성 · task#262에서 재현 확인(이번 사이클은 재발굴 없이 이관 수록)
- **증상**: `frontend/src/useStageNavigation.js:179` `handleSelectPerson(id, view='map')`의 기본값과 `frontend/src/App.jsx:357`의 자기시트 억제 조건이 `exploreView === 'intro'`에만 걸려 있어, intro를 명시하지 않고 `selectPerson`을 호출하는 모든 경로에서 **데스크톱 목적지 화면에 자기 자신의 상세 시트가 열린다**. 용어집 「상세 시트」의 "탐험 중인 인물 자신은 겹쳐 띄우지 않는다" 위반.
- **근거**: `frontend/src/useStageNavigation.js:179` `function handleSelectPerson(id, view = 'map') { setExploreTourId(null); selectNodeFresh(id); setExplorePersonId(id); setExploreView(view); setActiveStage('explore') }` — view 기본값이 'map'. `frontend/src/App.jsx:357` `transform: selectedNode && exploreView !== 'relations' && exploreView !== 'reliance' && !(exploreView === 'intro' && selectedNode === explorePersonId) ? 'translateX(0)' : 'translateX(100%)'` — 자기시트 억제(`selectedNode === explorePersonId`)가 `exploreView === 'intro'` 조건과 AND로 묶여 있어 map/timeline 등 다른 뷰로 진입할 때는 억제되지 않는다. `frontend/src/useStageNavigation.js:346` `const sheetOpen = selectedNode != null && selectedNode !== explorePersonId`(모바일)는 view-무관 정의라 이 leak이 없음 — **데스크톱 전용** 버그.
- **재현**: Playwright 2경로로 재현됨(task#262). (a) 허브 → 아브라함 카드(intro, 억제 정상) → 여정 탭 클릭 → 시트 h2가 뷰포트 진입. (b) `#/person/abraham/relations` → '이삭 ↗' 클릭 → `#/person/isaac` 진입 즉시 이삭 자기시트 표시.
- **검증 요지**: task#262에서 이미 라이브 Playwright로 두 경로 모두 재현 확인된 항목. 이번 2차 사이클에서는 재발굴하지 않고 CONFIRMED로 이관 수록.
- **제안 수정방향**: `frontend/src/App.jsx:357`의 자기시트 억제 조건을 `exploreView === 'intro'` 한정에서 떼어내 `selectedNode === explorePersonId`이면 view 무관하게 항상 억제하도록 변경(모바일 `sheetOpen`의 view-무관 정의와 동일 규약으로 통일).
- **수정 완료(S4)**: 제안 수정방향대로 `frontend/src/App.jsx:357`의 조건을 `!(exploreView === 'intro' && selectedNode === explorePersonId)`에서 `selectedNode !== explorePersonId`로 교체 — `exploreView !== 'relations' && exploreView !== 'reliance'` 게이트는 그대로 유지해 관계·의존 뷰의 전체화면 억제는 건드리지 않았다. 인접 주석도 새 규약을 반영해 갱신(모바일 `sheetOpen`과 동일 규약이라는 점 명시).
  - **변경 파일**: `frontend/src/App.jsx`(상세 패널 `transform` 삼항식 1줄 + 인접 주석).
  - **재현(수정 후, Playwright 데스크톱 1400×900, 리포트의 실제 재현 경로 (b)로 직접 재현)**: `#/person/abraham/relations` 진입 → 관계 카드의 "이삭" 이름 버튼(리액트 핸들러 보유 확인 후 좌표 클릭, `cursor:pointer` 상속만으로 오조준하지 않게 `__reactProps$*.onClick` 보유 지점을 DOM 전수 탐색으로 특정) 클릭 → **URL이 `#/person/isaac`로 이동, `exploreView`는 'map'(여정 탭이 활성색, '소개' 탭은 dim — intro가 아님을 직접 확인)인데도 패널 `transform`이 `matrix(1,0,0,1,360,0)`(=`translateX(100%)`, 숨김) 유지** — 수정 전 리포트가 재현했던 "즉시 이삭 자기시트 표시"가 사라짐. 스크린샷: `/tmp/pw263/c4_isaac_landing.png`(자기시트 없이 지도가 패널 없이 꽉 찬 상태).
  - **acceptance 3criteria 실측**:
    (a) 자기시트 어느 탭에서도 안 뜸 — 허브→아브라함 카드(intro 랜딩) 패널 hidden 확인 → '여정' 탭(map) 클릭 후에도 패널 hidden 유지(`matrix(...,360,0)` 그대로, view가 intro→map으로 바뀌어도 억제 지속). 관계뷰에서 "이삭" 클릭 후 `#/person/isaac`(map view) 진입 즉시도 hidden(위 항목).
    (b) 다른 대상 선택 시 뜬다(회귀 아님, task#262 계약 유지) — 아브라함 연표 탭에서 이벤트 행 "아브라함의 출생" 클릭 시 패널 `transform`이 `matrix(...,360,0)`→`matrix(1,0,0,1,0,0)`(=`translateX(0)`, 표시)로 전환 확인. `selectedNode`(이벤트 id) ≠ `explorePersonId`(아브라함)라 정상 노출.
    (c) 관계·의존 뷰 전체화면 억제 유지 — `#/person/abraham/relations` 첫 진입 시점에도 패널 `transform`은 `matrix(...,360,0)`(hidden) — `exploreView === 'relations'` 게이트가 그대로 작동.
  - **모바일 무회귀 확인**: 모바일(390×844)은 이번 변경(데스크톱 삼항식)의 대상이 아니라(모바일은 `frontend/src/useStageNavigation.js:346`의 `sheetOpen`을 그대로 씀, 무변경) 회귀 위험이 없음을 전제로, 그래도 허브→아브라함 intro→여정(map) 탭 전환 시 하단 시트 `transform`이 `matrix(1,0,0,1,0,633)`(화면 밖, hidden)로 두 뷰 모두 동일함을 실측해 재확인.
  - **검증**: `npm run build` 통과, ESLint 클린.

---

## 백로그 후보 (MEDIUM/LOW, task#262 이관 — 이번 사이클에서 고치지 않음)

task#262에서 이미 검토된 항목 중 아래 4건은 심각도가 낮거나(LOW) 이미 "비버그/미발현"으로 판정되어 정식 상세 절 대신 후보 목록으로만 정리한다. 다시 발굴하지 않았다.

- **[MEDIUM] 모바일 관계 뷰 시트 미닫힘** — 다른 화면에서 고른 노드의 하단 시트가 관계 탭으로 전환해도 닫히지 않고 관계 화면 위에 겹친다(데스크톱은 `frontend/src/App.jsx:357`이 억제 → 플랫폼 불일치). 정확한 파일:줄 근거가 task#262 인계 메모에 없어 이번 사이클에서 재확인하지 않음 — 후속 사이클에서 위치 특정 필요.
- **[LOW] `frontend/src/dates.js:6-11` `parseYear` 숫자 입력 취약** — `parseYear(1997)` 같은 숫자 인자를 넣으면 `startDate.startsWith is not a function`(6행)로 예외. 큐레이션 35인물 전수 실측상 `birthYear`/`deathYear`는 전부 문자열 또는 null이라 **현재 미발현**.
- **[LOW] `frontend/src/TimelineView.jsx:31` 동명 `fmtYear`** — `dates.js`와 이름만 같고 시그니처가 다른 함수(숫자 연도를 받아 `y < 0 ? BC ${-y} : AD ${y}`, 32행)로, `dates.js` 사본이 아니다. 버그가 아니라 이름 충돌(가독성 이슈).
- **[LOW] 스윕 커버리지 공백** — `#/stats` 책 bar row 미실측, `#/stats`·`#/topics`는 모바일 짝 없음. 실측표: `.forge/reports/click-detail-sweep.json`.

## 부록 — 적대적 검증에서 기각된 항목 (REFUTED 0건)

이번 사이클은 dedup 후 4건 전건이 검증을 통과했다 — 기각된 항목 없음.

## 자체 검증

`python3` 한 줄로 표 행수·`### ` 절수·confirmed 총건수 일치 및 모든 `파일:줄` 인용의 파일 존재·줄 범위 유효성을 확인했다(방법과 결과는 작업 로그 참조). 표 5행 == 상세 절 5개(`### ` 5회) == confirmed 5건, 인용 파일 8개 전부 존재하며 인용 줄 범위가 각 파일의 `wc -l` 이내임을 확인함.
