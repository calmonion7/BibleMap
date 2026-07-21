# 2026-07-21 — 투어 재생 엔진·스키마 이관·다윗 파일럿 (1/3) [일괄 승급]

## Plan vs actual
- What went as planned: 9투어 stops 객체 이관, 다윗 18 해설, 재생 엔진(시퀀서·점진 경로선·해설 카드·컨트롤), Playwright 21항목. 계획 슬라이스 그대로.
- Divergences: ① 백엔드 파싱은 **코드** 변경인데 계획이 `restart api`라 적어 500 발생 — rebuild로 즉시 해소. ② 밧모 사건은 계획 서술("좌표만 없음")과 달리 `occursAt` 자체가 비어 있었음 — 장소 노드 연결부터 보강.

## Learnings
- Do differently next time:
  - **계획에 반영 명령을 적을 때 데이터/코드를 구분해 명시** — 데이터만이면 `restart`(볼륨 마운트+lru_cache), 코드가 섞이면 `up -d --build`. "restart면 된다"는 서술이 계획에 있으면 실행 때 그대로 밟는다.
  - **저작 데이터 공백은 "값이 비었다"가 아니라 "연결 자체가 없다"일 수 있다** — 보강 전에 공급 경로(place_coords 오버레이 → enrich 스크립트 → Neo4j → occursAt 참조)를 처음부터 따라가 실제 결손 지점을 특정할 것.
  - 재생 카메라는 신규 로직 대신 **기존 activeStopIdx→easeTo 경로 재사용**이 정답이었다(모바일 오프셋·배지 강조 공짜 획득). 기존 상호작용 위에 모드를 얹을 땐 구동 프리미티브를 먼저 찾기.

## Doc updates
- CONTEXT.md promotion: none
- ADR added: none
