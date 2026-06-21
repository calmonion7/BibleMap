# 2026-06-22 — 맵 fitBounds outlier 저줌 뭉침 완화 (task 80)

## Plan vs actual
- What went as planned: `coreBounds(places)` 헬퍼(median 중심 거리 중앙값×3 임계로 outlier 제외) + `!primary` 분기 fitBounds에 `coreBounds(places) || bounds` 적용. 발산 낮음.
- Divergences: 계획의 "튜닝 가능 상수"에서 **절대 floor는 제외** — 밀집 클러스터를 과잉 제외할 위험(예: 예수 0.6° 분포가 0.5 floor에 걸려 잘못 제외). 상대 임계(medD×3)만 사용.

## Learnings
- Do differently next time:
  - **맵 framing 저줌 뭉침의 해법은 outlier를 fitBounds 범위에서 빼는 것 — maxZoom 상향이 아니다.** maxZoom은 줌 *상한* 캡이라, 문제(원거리 점이 bounds를 넓혀 *낮은* 줌으로 빠짐)를 못 고친다. outlier는 데이터·마커로는 그대로 두고 프레이밍 계산에서만 제외.
  - **robust outlier 규칙은 상대값으로.** median 중심 거리의 중앙값×K(K=3, IQR류 보수값)만 사용하고 절대 거리 floor는 쓰지 말 것 — floor는 밀집 클러스터(예수)를 오탐 제외해 과확대. 검증: 모세 줌 4.76→5.98(홍해 lat 19 제외), 예수 제외 0건 불변.
  - 임계 K는 clusterRadius처럼 향후 튜닝 여지. "맵 뭉침" 3분류 명확화: 라벨 배치(task-74/75) / 마커 클러스터(clusterRadius, loosen) / **저줌 프레이밍(이번 coreBounds)** — 셋은 독립.

## Doc updates
- CONTEXT.md promotion: 없음 (구현 휴리스틱, 새 도메인 용어 아님)
- ADR added: 없음 (가역적·튜닝 가능, 3조건 미충족)
