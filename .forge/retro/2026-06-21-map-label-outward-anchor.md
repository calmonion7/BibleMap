# 2026-06-21 — 맵뷰 라벨 위치 기반 바깥쪽 배치 (task 75)

## 계획 vs 실제
- 계획대로(저발산): `places-label`=최근접 이웃 반대쪽(`outwardLabel`+nearest-neighbor), `event-ring`/`spider`=링 중심 radial-outward(`ringLabels`), 3개 레이어를 데이터 기반 `text-anchor`/`text-offset`로 전환(task-74 native `text-variable-anchor` 대체). 우려했던 데이터 기반 `text-offset`(배열 속성) 정상 동작.
- 검증: Playwright로 모세 선택 시 시내=왼쪽 / 바란 광야=오른쪽(헤드라인 예시 그대로), 헤브론 8-사건 링 라벨 중심 바깥 방사 확인.
- 적대적 리뷰(6렌즈+반박): 13지적, 코드 결함 0, fix-needed 확정 1건(아래 1번).

## 배운 것 / 다음엔 다르게
1. **UAT 증거는 봉인 전 `.forge/reports/`에 보존.** DoD가 "스크린샷으로 확인"을 완료조건으로 걸면, 캡처를 휘발성 job tmp에만 두지 말고 `.forge/reports/`에 저장해야 제3자 추적이 된다. 적대적 리뷰가 잡은 유일 fix-needed였고 핵심 3장(`o2_pair_tight`/`ov_moses_sinai`/`ov_hebron_ring`)을 보존해 해소. → 앞으로 시각 검증 DoD 작업은 캡처 보존을 완료조건의 일부로 취급.
2. **데이터 기반 고정 앵커의 회귀 벡터(인지).** native `text-variable-anchor`는 줌 인식 + 8슬롯 충돌-폴백이라 겹치면 다른 자리로 튕긴다. 데이터 기반 단일 고정 앵커는 그 폴백을 포기 → *진짜* 단일 슬롯 충돌 시 라벨이 대체 위치를 못 찾고 그냥 숨는다(task-74 대비 가시 라벨 감소 가능). 이번엔 outward 분산이라는 이득과 맞바꾼 의도된 트레이드오프(plan 비목표에 명시). 향후 맵 라벨 작업 시 이 회귀 가능성을 먼저 점검.
3. **정리 부채(소소, 다음 맵 터치 때).** variable-anchor 제거 후 `text-justify:'auto'`가 3개 레이어에 dead config로 잔존. `cosLat` 가드 `|| 1`은 `Math.cos(90°)=6.12e-17`(truthy)라 무효지만 데이터 위도대(26~37°N)에선 도달 불가라 실해 없음 — 둘 다 코드 스멜 수준.
4. **적대적 리뷰 비용/효용.** 86줄 변경에 6렌즈+반박(에이전트 7, ~434k 토큰)은 무거웠지만, 반박 패스가 12건의 minor 노이즈를 fix-needed에서 걸러내 실질 1건(프로세스)만 남겼다. 작은 변경일수록 반박 패스가 노이즈 억제에 특히 유효.

## 문서 업데이트
- CONTEXT.md 승급: 없음 (새 도메인 용어 없음 — 구현/프로세스 학습)
- ADR 추가: 없음 (native→데이터기반 전환은 가역 — task-74↔75 저비용 왕복이 증거, "되돌리기 어려움" 미충족; 근거는 plan.md/review.md에 보존)
- 적대적 리뷰 결과: `.forge/review.md` (봉인 시 done/으로 아카이브)
