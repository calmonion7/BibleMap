# 2026-07-20 — 인물 연표 "참여 사건만" 엄격 필터 + 승천 중복 제거 (task#218) [일괄 승급]

## Plan vs actual
- What went as planned: 슬라이스 3개 모두 계획대로. `elisha.json` 참여자 제거 + Neo4j 간선 삭제로 승천 중복 해소, `TimelineView.jsx` 멤버 단위 필터로 편승 차단, Playwright(데스크톱+모바일)로 엘리야 11건·"회오리바람 불수레 승천" 종료·금지 6건 미노출·다윗 회귀 정상 확인.
- Divergences (낮음):
  - 워크플로우 미사용, 직접 실행(파일 2개 규모 + eco 모드).
  - 계획의 "api 재시작"은 실은 불필요했음 — `/person/{id}/event-ids`(nodes.py)는 lru_cache 대상이 아닌 **live Neo4j 쿼리**라 간선 삭제가 즉시 반영. `/events`는 캐시되나 이번 변경으로 내용 불변. 재시작은 캐시 안전차원 무해 수행.

## Learnings
- Do differently next time:
  - **MERGE 로더는 간선을 삭제하지 않는다.** `load_person_events.py`는 `HAS_PARTICIPANT`를 MERGE만 하므로, authored 데이터의 `participants`에서 한 명을 빼도 JSON 재적재로는 기존 간선이 사라지지 않는다 → **Neo4j에서 해당 간선을 직접 DELETE**해야 반영된다(이후 재적재 시 JSON에 없으니 재생성 안 됨=멱등). 관계형 필드(participants/occursAt 등)를 "제거"하는 편집은 전부 이 함정을 동반한다.
  - **date_corrections(ADR-0014)와 타임라인 그룹 필터의 교차효과.** 왕 통치 4건(아사·여호사밧·아하시야·요람)을 보수 연대로 정렬(-913→-870 등)하면서 엘리야 저작 사건과 `startDate` 문자열이 정확히 일치하게 됐고, `TimelineView`가 startDate로 묶고 **그룹 단위**로 인물 필터를 걸어 비참여 사건이 그룹째 딸려오는 "편승"이 발생했다. 연대 교정이 무관해 보이는 필터 동작에 부작용을 낳은 사례 — 연도 오버레이를 바꿀 땐 동일-startDate 그룹핑 소비처를 함께 점검.
  - **인물 연표는 이제 멤버 단위 엄격 필터**(그 인물이 participant인 사건만; `TimelineView.jsx`의 `activePersonFilter` 분기). 헤더 "…이 언급된 사건" 문구와 정합. 향후 "그 인물 시대의 정치 배경"을 다시 보여주고 싶다면 바로 이 지점을 되돌리면 된다(별도 결정).
- 관찰(후속 후보): `authored-elisha-mantle-jordan`의 `nameKo`가 "엘리야 승천 — 겉옷으로 요단을 가르다"로 남아 **엘리사 연표**에 이 제목으로 표시됨(영문 title·context는 이미 엘리사 중심). 어색하면 fg-quick로 nameKo만 엘리사 중심 정정 검토.

## Doc updates
- CONTEXT.md promotion: 「저작 인물」 절 — MERGE 로더 비대칭 중 **제거 경로**(관계형 필드 제거는 재적재로 안 사라짐 → Neo4j 직접 DELETE, 이후 멱등) 승급. *데이터 적재 파이프라인 아크 일괄 승급*으로 #213(추가 경로)과 함께 반영. 편승·타임라인 startDate 그룹 필터 교차효과는 구현 동작이라 미승급(「사건 연대」 절 run 그룹핑이 이미 커버).
- ADR added: none (엄격 필터 결정은 유익하나 "번복 난이도"가 약해 ADR 3요건 미충족 — 회고 로그에 기록)
