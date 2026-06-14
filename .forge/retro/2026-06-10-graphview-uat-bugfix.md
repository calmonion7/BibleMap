# 2026-06-10 — GraphView compound 그루핑 UAT + tap 가드 재수정

## 계획 vs 실제

- 계획대로 간 것: UAT 실행, Playwright로 동작 확인, 버그 수정 후 푸시.
- 발산:
  1. **이전 tap 가드(`isParent()`)가 런타임에서 작동 안 함** — `collapseAll()` 이후 expand-collapse 플러그인이 자식을 그래프에서 제거하므로 `isParent() === false`. 이전 `graphview-parent-tap-guard` 작업의 검증이 "번들에 `isParent` 포함 여부"만 확인하고 실제 클릭 동작은 확인하지 않아 통과로 기록됨 → 프로세스 문제.
  2. **expand 후 re-fit 없음** — compound 그룹이 펼쳐질 때 뷰가 재조정되지 않아 화면이 깨짐. 코드 리뷰로는 예측 불가, 런타임에서 직접 보고서야 발견.

## 학습

- **번들 포함 여부 != 런타임 동작 확인.** 코드가 배포됐다는 사실만 검증하는 건 충분하지 않다. 인터랙티브 동작(클릭, expand/collapse 등)은 실제로 실행해서 봐야 한다.
- **compound expand처럼 레이아웃이 동적으로 바뀌는 동작은 런타임 전에 예측하기 어렵다.** 정적 분석/코드 리뷰로는 잡기 어려운 버그 유형.
- 다음에 다르게 할 것:
  - 인터랙티브 UI 작업 플랜에 **Playwright 검증 단계를 명시적으로 포함**한다.
  - 특히 클릭·hover·expand/collapse 등 사용자 인터랙션이 있는 기능은 "번들 포함"이 아닌 "Playwright로 동작 확인"을 검증 기준으로 설정한다.

## 문서 업데이트

- CONTEXT.md 승격: 없음
- ADR 추가: 없음
