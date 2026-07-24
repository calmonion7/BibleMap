# 2026-07-24 — 모바일 지도 프레이밍 버그 + 위치 없는 비유 커버리지 (task#251) [일괄 승급]

## Plan vs actual
- 계획 3슬라이스 그대로. 직접 실행(eco). 세부는 `.forge/done/260724-101829-mobile-map-framing-and-parables-coverage/run.md`.

## Learnings
- Do differently next time:
  - **모바일 지도 세계축소(fitBounds가 줌을 최소로 클램프 → 적도 아프리카) 근본원인은 "패딩 과대"가 아니라 deep-link 진입 시 `map.on('load')` 시점 컨테이너가 아직 풀사이즈가 아니라 WebGL 드로잉버퍼가 작게 잡힌 것.** 수정: load 핸들러에서 `setMapLoaded` 전에 `map.resize()`로 캔버스를 실컨테이너에 동기화(프레이밍 effect보다 선행). 패딩을 컨테이너 60% 이내로 제한하는 clampPadding은 소형/가로 폰 방어로 보조(표준 390×844에선 거의 무작동).
  - **before/after로 확증**: MapView 변경만 `git stash`→빌드→프리픽스 캡처("Kinshasa·Tanzania")→복원→수정본("네겝"). 빌드 ~200ms라 저렴. 지도 프레이밍처럼 "육안이 유일 판정"인 버그는 프로그램 타일 분석보다 스크린샷 before/after가 신뢰 가능.
  - **위치 없는 "가르침" 비유(17건)는 지도에 못 얹음 — 좌표 날조 금지.** 대신 UI 안내("위치 없는 비유 N건은 연표에서") + 커버리지 검증 스크립트(route의 placeId→place_coords 해석 로직과 동일하게 계산)로 지도↔연표 간극을 명시화.
- 관찰: 모바일 지도 상단이 여정 시트 위로 어둡게 렌더되는 선재 현상(OLD/NEW 동일) — 이번 무관, 별건 후보.

## Doc updates
- CONTEXT.md: none. ADR: none (되돌리기 쉬운 타이밍 수정 — 3요건 미충족).
