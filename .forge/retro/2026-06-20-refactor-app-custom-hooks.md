# 2026-06-20 — App.jsx 커스텀 훅 추출 (useNodeSelection + useSearch)

## 계획 vs 실제
- 계획대로: S1(useNodeSelection), S2(useSearch) 추출, App.jsx 377→278줄, 빌드·UAT 통과
- Divergence 1: `handleSearchKeyDown` — useSearch 반환값 포함 계획, 실제 App.jsx 잔류
- Divergence 2: `selectNodeFresh` 추가 — 계획에 없던 함수, `closePanel + selectNode` 대안 대신 채택

## 학습
- 다음에 다르게 할 것:
  - **훅 간 브리지 함수 설계 시 콜백 방향 먼저 확인**: `handleSearchKeyDown → handleSelectResult → clearSearch(훅반환)`처럼 브리지가 훅 반환값에 의존하면 훅 안으로 넣을 수 없다. 계획 단계에서 "이 핸들러가 누구의 setter를 호출하는가"를 체크해 처음부터 브리지 위치를 App.jsx로 명시하면 divergence 없이 실행 가능.
  - **React useRef 동기화 타이밍**: `useEffect(() => { ref.current = state }, [state])`는 렌더 후 비동기 업데이트 — 동일 이벤트 핸들러에서 setState + ref 의존 함수 연속 호출 시 ref가 stale. 히스토리 리셋처럼 "새 컨텍스트 선택"이 필요할 때는 `selectNodeFresh` 같은 전용 함수가 안전.

## Doc 업데이트
- CONTEXT.md 승급: 없음 (React 구현 세부사항)
- ADR 추가: 없음 (3조건 미충족)
