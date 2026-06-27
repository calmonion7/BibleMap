# 2026-06-27 — 장소 상세 보강 + 다른 인물 점프 (Part 3/3) [일괄 승급]

> fg-next all 자동 진행으로 retro skip됐던 것을 사후 일괄 승급(2026-06-27). 원천: `.forge/done/2026-06-27-person-first-map-redesign-3of3/run.md`.

## 계획 vs 실제
- 계획대로: S1(장소→13인 엔드포인트)·S2(장소 패널 배경·사건·근거구절)·S3(다른 인물 점프 칩) + C2 설계의 explorePersonId 분리(장소 선택해도 인물 여정 유지).
- 발산: 이웃 응답에 books 메타가 없어 `/event/{id}/verses`에 `bookNameKo` 필드 추가(설계 원문 밖, 권 이름 표시용).

## 배운 것 (다음에 다르게 할 것)
- **★ effect 의존성에 들어가는 콜백/객체는 반드시 참조 안정화(useCallback/useMemo).** App.jsx가 SidePanel `onNodeLoaded`를 매 렌더 새로 만드는 인라인 화살표로 넘겨, SidePanel의 `/node` fetch effect(deps에 onNodeLoaded)가 매 렌더 재실행→`setCollapsed({})`로 섹션 펼침이 즉시 리셋→"이 곳을 지난 인물" 칩 클릭 불가(점프 불능)였다. `useCallback`으로 해결. 이 프로젝트가 이미 `selectNode`(useNodeSelection)에서 지키던 규율을 **신규 콜백에도 빠짐없이** 적용해야 한다.
- **★ 워크플로 정적검증(AST/build/lint 전부 통과)은 런타임 렌더루프/상태리셋 버그를 못 잡는다.** 위 버그는 빌드·lint를 통과했고 메인 세션 Playwright 런타임 UAT에서만 드러났다. → **상태·effect·콜백을 건드리는 작업은 메인 세션 런타임 UAT(실클릭/실엔드포인트) 필수**, 정적검증만으로 "PASS" 판정 금지. (#87 컨테이너 경로 500, #88 영문 장소명에 이어 3번째 — 워크플로 검증 슬라이스 설계 시 런타임 UAT를 명시 포함시킬 것.)
- **상태 분리로 컨텍스트 보존**: "탐험 중 인물"(explorePersonId)과 "상세 대상"(selectedNode)을 분리해, 장소를 선택해도 인물 여정선/리스트/맵이 유지된다. 인물 중심 흐름에서 "보조 상세 선택"이 "주 컨텍스트"를 덮지 않게 하는 패턴.
- UX: SidePanel 섹션 기본 접힘이라 "이 곳을 지난 인물" 점프 칩 발견성이 낮음 — 이 섹션만 기본 펼침을 후속 검토 가능.

## 문서 업데이트
- CONTEXT.md 승급: 없음 (장소 상세·점프는 UI 구현; 도메인 용어는 기존 등재).
- ADR 추가: 없음 (콜백 안정화·정적검증 한계·explorePersonId 분리는 코딩 규율/프로세스이자 ADR-0007 설계의 귀결 — 코드베이스 맵 CONVENTIONS·CONCERNS에 반영, 별도 프로젝트 ADR로는 노이즈).
