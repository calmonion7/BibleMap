# 2026-07-16 — 모션 개편 3/3: 데이터 뷰 (task#191, fg-next all 사후 일괄 승급)

## Plan vs actual

- 계획대로: 도넛 스윕+카운트업·막대 bar-reveal·궤적 스태거·가계도 페이드·최종 매트릭스 7/7·실기기 확인 목록 산출.
- 이탈: ① **S2 대폭 축소** — 계획이 명시한 타임라인 행·관계 레인 모션을 오디트 기각(밀도 데이터 장식 방해·고빈도 탭)에 따라 미적용, 가계도만 축소안(재중심화 리마운트 페이드) 적용. ② 1/3 recon의 "도넛 스윕이 이미 있다"는 전제가 오류로 판명 — 교정하며 구현.

## Learnings

- Do differently next time:
  - **"transition 코드가 있다 ≠ 재생된다"** — CSS transition은 값의 *변화*에만 발동하므로, 마운트에 최종값으로 그리는 SVG 게이지(stroke-dasharray)는 입장 애니메이션이 영구히 죽어 있다. 입장 스윕은 0으로 첫 렌더 → 다음 프레임(rAF)에 목표값 설정 2단으로. recon 때 "모션 존재"는 코드 grep이 아니라 실재생 확인으로 판정할 것(1/3 오디트가 이걸 어휘 선례로 잘못 집계).
  - **reduce 대응이 토큰 붕괴로 안 covering되는 JS 애니메이션**(rAF 카운트업)은 `matchMedia('(prefers-reduced-motion: reduce)')` 분기를 직접 넣어야 한다 — CSS 가드는 CSS만 지킨다.
  - 계획 문구와 오디트 기각의 충돌은 **절제(기각) 우선**이 옳았다 — 단 이 우선순위 조항을 계획에 선언해 두는 게 다음부터의 정석(1/3 회고와 동일 결론, 계획 작성 시점 반영 사항).

## Doc updates

- CONTEXT.md/ADR: 없음.
- 오디트 보고서(.forge/reports/motion-opportunities.md)에 처리 현황 표(적용 7·기각 유지 6) 갱신 — 실행 중 완료.
