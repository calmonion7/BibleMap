# 2026-07-16 — 모션 개편 2/3: 허브·탐험 시그니처 (task#190, fg-next all 사후 일괄 승급)

## Plan vs actual

- 계획대로: 허브 카드 스태거(세션 1회 재생 플래그)·투어/책 어휘 통일·정차지 금색 바·매트릭스 7/7.
- 이탈: ① S3 전제 2건이 실물과 다름(여정 "아코디언"은 실제론 양피지 모달 — 1/3에서 이미 처리, "지도 DOM 마커"는 캔버스 심볼 레이어 — CSS 비대상) → 오디트 교정안(#6)대로 축소. ② **[주요] 인접 버그 수정**: 데스크톱 정차지 클릭 시 앱 전체 크래시(easeTo `offset: undefined`) 발견·수정. ③ 재생 억제 플래그를 투어·책에도 확장(빈도 원리 동일).

## Learnings

- Do differently next time:
  - **라이브러리 옵션 객체에 undefined 값 키를 명시적으로 싣지 말 것** — maplibre `easeTo`는 `extend(defaults, options)` 병합이라 `{ offset: undefined }`가 기본값(Point 0,0)을 undefined로 **덮어** `Point.convert(undefined)` throw → uncaught 효과 에러로 **React 루트 전체 언마운트**(데스크톱에서 정차지 클릭마다 화면 전멸이던 실사용 프로덕션 버그, 7/3 center-journey-stop-above-sheet에서 유입 추정). "키 생략"과 "undefined 값 전달"은 다르다 — 조건부 옵션은 `...(x ? { x } : {})` 스프레드로.
  - **pageerror는 추정하지 말고 스택부터 캡처하라** — 1/3 검증 때 이 에러를 "헤드리스 타이밍 아티팩트 추정"으로 기록하고 넘어갔다가, 2/3에서 Playwright `e.stack` 캡처 한 번으로 maplibre `convert→easeTo` 프레임이 바로 나와 루트 원인·실사용 영향까지 확정했다. 첫 관찰 때 스택을 잡았으면 태스크 하나 빨리 고쳤다.
  - **회귀/선재 판별은 `git stash → 빌드 → 동일 플로우 재생` A/B가 1분 결정타** — diff 정독보다 빠르고 확정적. 판별 후 stash pop 잊지 말 것.
  - 크래시로 UI 검증이 막히면 **같은 패턴의 지도 무관 경로로 대체 검증**하고(1/3), 크래시 자체는 별도 수정으로 — 검증과 버그픽스를 한 슬라이스에 뭉치지 않아 드라이브가 멈추지 않았다.

## Doc updates

- CONTEXT.md/ADR: 없음(버그 수정·프로세스 학습 — 코드 주석 + 본 회고 + 메모리로 충분).
- 메모리: project_biblemap_status에 easeTo undefined 함정 승급(드라이브 종료 시).
