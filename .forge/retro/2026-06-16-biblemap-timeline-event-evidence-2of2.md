# 2026-06-16 — 타임라인 구절 근거 (Part 2/2): 권→구절 본문 드릴다운

## Plan vs actual
- What went as planned: S1~S4 전부 계획대로. S1 `generate_event_verses.py`가 theographic events.json+verses.json을 받아 사건별·권별 구절 + 연속구간 접은 `rangeLabel`을 `data/event_verses/events.json`(450 사건, 다권 75건, 최대 4권, 2.0MB)으로 생성. S2 `/event/{id}/verses`를 books.py의 `lru_cache`+`DATA_DIR→레포 폴백` 패턴 그대로 추가. S3 TimelineView 권 칩을 "Book 패널"에서 "사건 아래 인라인 구절 뷰(권 탭→인용범위→펼치면 절별 한국어 본문)"로 교체, getbible 장 fetch를 `frontend/src/getbible.js` 공유 헬퍼로 추출(SidePanel 동작 동일 위임). :8080 UAT 통과(단권·다권, 콘솔 에러 0).
- Divergences (모두 경미):
  - **verses.json `chapter`·`book`이 정수가 아니라 레코드 ID 배열.** 장/절은 `verseID`(BBCCCVVV) 슬라이스로, 책 키는 `fields.book[0]`로 도출. 플랜이 verseID 기반을 명시했으므로 접근 불변.
  - **장 경계 넘는 연속구간(`C1:Vs–C2:Ve`)은 실데이터에 안 나옴.** 장 끝(…031) 다음 절(…001)은 verseID 정수상 +1이 아니라 run이 끊김 → `1:1–31, 2:1–3`처럼 같은-장 run 여럿으로 표현됨. 그 코드 분기는 단위검증상 정상이나 **실데이터에서 미발동**(죽은 코드 아님, 방어용). 다음에 이 스크립트를 읽는 사람이 "왜 cross-chapter 라벨이 안 보이지?" 헷갈리지 않게 기록.
  - **인라인 구절 뷰를 flex 사건 행 *내부*가 아니라 행 div 바로 아래 별도 흐름 블록**(`verseBoxStyle`, marginLeft 104)으로 렌더 — 본문 길어질 때 행 레이아웃 안 깨지고, 플로팅 nav에 안 가리려면 스크롤 영역 안 흐름 블록이어야 함. Part 1 회고의 "인라인 확장 권장"과 일관.
  - api 컨테이너에 published port 없음 → 검증 curl을 `:8000`이 아니라 `:8080/api/`(nginx 프록시)로. 동일 코드라 기능 동일.

## Learnings
- Do differently next time:
  - **"한 번에 하나만 펼치는 상세 뷰 + 비동기 fetch"는 out-of-order 레이스를 기본 의심하라.** 단일 슬롯 상태(`eventVerses={id,data}`)에 in-flight 중 다른 항목을 열면, "마지막 응답 도착" 항목이 "마지막 요청" 항목을 덮어쓴다. 코드리뷰가 major로 잡아 `openEventRef`(현재 열린 id) ref를 두고 `.then/.catch` 커밋 전 대조하는 가드로 수정. SidePanel의 `state.id===nodeId` stale 패턴과 같은 뿌리 — 이 프로젝트의 비동기 상세뷰는 전부 "결과를 요청 id로 묶어 검증"이 규약. 다음에 비슷한 뷰 만들 때 처음부터 가드 포함.
  - **theographic 추가 엔티티 적재 시 `status` 필터 확인(CONTEXT.md "publish 레코드"가 명시).** verses.json 레코드에 `status:"publish"` 필드가 있는데, `generate_event_verses.py`가 verse를 status로 필터링하는지 미확인. 사건이 참조하는 구절만 오버레이에 들어가고 UAT는 정상이었으나, wip 구절 혼입 가능성은 다음에 스크립트 점검 시 확인할 항목.
  - **플로팅 nav 바가 콘텐츠 최상단 가림(3회 반복).** Part 1·이번 둘 다 Playwright에서 좌표 클릭 대신 `el.click()` JS dispatch + scrollIntoView로 우회. 미해결 칩 "MapView 에러배너 nav 뒤 가려짐"(task_c16549df)과 동일 뿌리 — nav가 absolute 오버레이. 근본 수정(콘텐츠 영역 top 오프셋 or nav를 레이아웃 흐름에) 하면 이 우회가 사라짐.
  - **(설계 결정, 기록만) 구절 근거 = Neo4j Verse 노드 런타임 쿼리가 아니라 빌드타임 오버레이 JSON.** `/books`+`book_years_approx` 선례 그대로(사전계산 파일 + `lru_cache`). 트레이드오프: 그래프에 Verse 노드 없음(구절-레벨 그래프 쿼리/검색 불가) vs 엔드포인트 단순·Neo4j 부하 0. 선례 일관이라 ADR로 승급 안 함. **다음에 "구절 검색"이나 "구절-레벨 관계 탐색"이 필요해지면 그때 Verse 노드 적재 결정을 ADR로 띄울 것.**

## Doc updates
- CONTEXT.md promotion: none (구절 근거·인용 범위는 기존 "사건의 근거" 항목이 이미 포함, getbible 실시간 fetch는 "Book Context"에 기수록; `rangeLabel`·오버레이는 구현 디테일이라 제외)
- ADR added: none (사건-근거 모델은 ADR-0002 기수록; 오버레이 사전계산은 `/books` 선례 따름 — 신규/난해 결정 아님)
