# 2026-07-18 — 마리아 여정에 베들레헴 탄생·애굽 피신·귀환 3사건 추가 (task#213) [일괄 승급]

## Plan vs actual
- What went as planned: 4슬라이스 전부 계획대로. mary.json 7사건(sortKey 정렬), event_verses 3엔트리(15 verseID 전부 `bible/verses.json` 실존 사전검증 통과), `load_person_events.py` 멱등 재적재, api 재시작 후 엔드포인트·Playwright 모바일 검증 통과. verified: yes.
- Divergences:
  - **워크플로우 대신 직접 실행** — 3사건 데이터 추가는 단일 세션으로 충분해 fg-run 비용 규칙에 따라 Dynamic Workflow 생략(서브에이전트 미사용). 더 저렴·빠름.
  - **범위 확정이 fg-ask→fg-next 사이에서 결정됨** — fg-ask는 "애굽 피신+귀환 2사건" 충실 해석 + 베들레헴 탄생은 별개 누락으로 핸드오프에 제안, 사용자가 `/fg-next 범위는 모두포함`으로 탄생 포함 지시 → 계획 3사건으로 갱신 후 실행.
  - **적재 스크립트 실행 위치** — api 컨테이너엔 `scripts/` 부재(app·data만 복사)라 호스트 python(neo4j 6.2.0) + `.env` 비밀번호로 직접 적재.

## Learnings
- Do differently next time:
  - **person_events 여정 사건은 "파일 오버레이"와 "그래프" 두 곳에 동시 공급된다.** 여정 *리스트*(`/person/{id}/journey`)는 오버레이 파일을 직접 읽어 파일 편집 + api 재시작만으로 뜨지만, 노드클릭(`/node/{id}`)·지도 핀·사건 링은 Neo4j Event 노드를 요구하므로 `load_person_events.py`(멱등 MERGE + OCCURS_AT/HAS_PARTICIPANT/CONTAINS_BOOK)를 반드시 실행해야 한다. task#203 학습(event_verses는 오버레이 전용, api 재시작만으로 반영)의 확장 — **새 여정 사건은 ①mary.json/event_verses 파일 편집 ②load_person_events.py 적재 ③api 재시작을 한 세트로.**
  - **그래프 적재 스크립트는 호스트에서 실행한다** — api 컨테이너는 `scripts/` 미포함. 호스트에 neo4j 드라이버가 있고 neo4j가 127.0.0.1:7687 노출 → `export $(grep NEO4J_PASSWORD .env) && NEO4J_URI=bolt://localhost:7687 NEO4J_USER=neo4j python3 -m backend.scripts.load_*`.
  - **요청 충실성 vs 인접 누락을 섞지 않은 게 재작업을 막았다** — fg-ask가 리터럴 요청("애굽 여정")만 계획하고 발견한 인접 누락(베들레헴 탄생)은 별도 제안으로 남겨, 사용자가 범위를 능동 확정. 프로젝트 지침(수술적 변경)과 정합.
  - **저작→검증 분리 재사용** — 15 verseID를 쓰기 전에 `bible/verses.json` 실존을 스크립트로 사전 검증(탈락 시 abort). 대량 저작뿐 아니라 소량 데이터 추가에도 값싼 안전장치.

## Doc updates
- CONTEXT.md promotion: 「저작 인물」 절 — MERGE 로더 추가·제거 비대칭 중 **추가 경로**(새 여정 사건 = 파일 편집→`load_person_events.py` 적재→api 재시작 3단 세트, 스크립트는 컨테이너 밖이라 호스트 python) 승급. *데이터 적재 파이프라인 아크 일괄 승급*으로 #218(제거 경로)과 함께 반영 — 두 회고가 MERGE 로더 계약의 양방향(추가/제거)을 이뤄 승격.
- ADR added: none (되돌리기 비용 낮음, person_events→그래프 적재는 기존 ADR-0005 범위 안 — 새 트레이드오프 아님)
