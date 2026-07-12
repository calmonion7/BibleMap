# 2026-07-12 — 여정 없는 인물 25명에 근거 구절 저작·연결 (task#169)

## Plan vs actual
- What went as planned:
  - 6 슬라이스 전부 DoD 충족. person_context 35→60인, bake 0 null, validate 60명 위반 0, Neo4j 60노드 주입, API topPersons에 role/intro/verses, 프론트 📖구절 칩+양피지 모달. Playwright(모바일)로 셈·함·야벳 구절칩·모달·노아/가인 여정 유지 확인.
  - 하이브리드 실행(계획 Notes대로): S1 저작만 Dynamic Workflow(5배치 병렬·eco sonnet·25/25 성공), S2~S6 메인 세션 직접. link-verses-to-verseless-events 회고의 하이브리드 교훈 재확인.
- Divergences:
  - ref 사전 검증 단계 추가(계획 미명시): 77개 저작 ref를 정본 절 사전 대조 → 전부 해석, 수정 0. bake(getbible) 결과 0 null로 예측 적중.
  - `bake_person_context()` 직접 호출(전체 main() 아님) — main()은 book/place/traits/relations 4파일까지 재기록해 스퓨리어스 diff 유발. person_context만 굽도록 함수 직접 호출.
  - role 2건 트림(헤롯 안디바·요엘, 11자→8자 이하). topPersons가 큐레이션 인물에게도 verses 반환(여정 우선이라 미사용, 쿼리 단순성). 프론트 모달은 node.label==='Book' 가드로 책 이탈 시 자동 숨김.

## Learnings
- Do differently next time:
  - **여정(큐레이션)과 person_context(role/intro/verses)는 독립된 두 데이터 레이어다.** 큐레이션 판정은 `data/person_events/<slug>.json` 존재(→ `/persons/curated` → 프론트 curatedIds)이고, role/intro/verses는 `data/person_context/people.json`. **person_context를 저작해도 그 인물이 "큐레이션"이 되지 않는다** — 그래서 여정 없는 인물에 verses를 붙여도 여정 칩이 아니라 구절 칩이 정상. 인물 데이터를 만질 땐 이 둘을 혼동 말 것(fg-ask에서 이 사실 확인이 "구절 vs 여정 칩" 로직의 최대 리스크를 해소했다).
  - **person_context 절 본문 bake는 `generate_verse_text.py`의 `bake_person_context()`이며 `main()`에 없다 → 직접 호출.** 게다가 이 베이커는 정본 사전이 아니라 **getbible 네트워크**로 굽는다(ADR-0015가 인물 인용절을 인라인 유지로 남긴 의도적 경계). 확장 시 네트워크 필요 + refs가 getbible korean에 실재해야 함. → **저작 ref는 정본 사전(`data/bible/verses.json`) 대조로 bake 전 검증**하면 네트워크 없이 성공 예측·getbible 공백 절까지 사전 차단(link-verses-to-verseless-events의 "저작 ref 검증 감싸기" 재사용).
  - **저작 서브에이전트에 참여 사건 문맥 + 엄격한 개역 약어 집합을 주면 ref 품질이 확보된다** — 77개 ref 전부 1차 해석 성공(수정 0). 자유 저작보다 "사건 대목의 절을 고르라 + 약어 화이트리스트"가 안전.
  - **미커밋 WIP와 같은 파일을 만지는 작업은 시작 전 WIP 상태를 확인·격리하라.** 이번엔 발자취→여정 리네임 WIP가 SidePanel.jsx에서 내 변경과 물리적으로 섞여 봉인/커밋 시 `git add -p` 분리 부담이 생겼다(계획 Non-goal로 "커밋에 리네임 불포함"을 명시했음에도 물리적 혼재는 피할 수 없었음). 다음엔 착수 전 워킹트리 청결 확인.
  - **범위 확장 시 governing 문서(AUTHORING.md)의 하드 카운트/범위 문구도 함께 갱신.** validator EXPECTED_COUNT만 35→60 바꾸고 AUTHORING.md "35인"을 방치하면 문서-검증기 모순. 이번엔 둘 다 갱신.

## Doc updates
- CONTEXT.md promotion: none (레이어 독립성·bake 경로는 데이터모델/구현 개념, 도메인 용어 아님)
- ADR added: none (기존 person_context 파이프라인 확장 — ADR-0006 LLM 저작·0015 인물 인라인 경계·AUTHORING.md 관할, 되돌리기 쉬움, 새 트레이드오프 아님)
- 기타 문서: `data/person_context/AUTHORING.md` 범위 문구 갱신(큐레이션 35인 → 큐레이션+여정 없는 노출 인물), `validate_person_context.py` EXPECTED_COUNT 35→60(+docstring)
