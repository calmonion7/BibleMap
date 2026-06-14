# 2026-06-12 — 장소 선택 시 사건 방사형 링 fly-out/in

## 계획 vs 실제

- 계획대로 간 것: event-ring-source + 3개 레이어 추가, rAF fly-out/in 400ms easeOutCubic, zoom-adaptive 반경(map.unproject 80px→degrees), 클릭 핸들러 3종(같은 장소 토글, 빈 곳 닫기, 사건 버블 onSelectNode). lint 0건, build green.
- 발산:
  1. `catch (e) {}` 빈 블록 → `catch {}` 로 단순화. `no-empty` 룰 위반. AbortError와 기타 에러 모두 `return`이므로 바인딩 없는 catch로 충분.
  2. 플랜의 `collapseRing() → expandPlace()` 순서는 두 애니메이션이 동일 GeoJSON source를 동시에 조작해 충돌. "다른 장소 클릭 = 기존 링 즉시 클리어 → 새 링 fly-out"으로 변경. "솩~" 접힘 애니메이션은 동일 장소 재클릭 / 빈 곳 클릭에서만 발동.

## 학습

- 다음에 다르게 할 것:
  - **MapLibre GeoJSON source를 여러 애니메이션이 공유할 때**: 이전 rAF 루프를 `cancelAnimationFrame`으로 취소한 뒤 source를 즉시 초기화하고 새 애니메이션을 시작할 것. 순차 실행을 가정하면 두 루프가 같은 프레임에 `setData`를 호출해 충돌한다.
  - `catch` 블록에서 분기 없이 동일하게 `return`만 할 때는 바인딩 없는 `catch {}`를 쓸 것. 빈 if 블록보다 짧고 `no-empty` 위반 없음.

## 문서 업데이트

- CONTEXT.md 승격: 없음 (구현 디테일 — 도메인 용어 아님)
- ADR 추가: 없음 (되돌리기 어렵지 않은 결정)
