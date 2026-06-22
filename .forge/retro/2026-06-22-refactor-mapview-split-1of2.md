# 2026-06-22 — MapView 분할 1/2 순수 헬퍼 재배치 (task 82, part 1/2)

## Plan vs actual
- What went as planned: 모듈 헬퍼(8~418행)를 `mapGeo.js`(101)·`mapLayers.js`(313)로 이동, MapView.jsx 751→341줄. 권장 그룹핑 그대로, 동작 불변(Playwright 회귀 PASS). 발산 낮음.
- Divergences: 본 task 실행 자체는 계획대로. 단 아래 부수 발견.

## Learnings
- Do differently next time:
  1. **대규모 순수 relocation은 손 전사 말고 기계 추출.** Python으로 라인 범위를 잘라 새 파일에 쓰고 `function X(`→`export function X(` 치환으로 export만 부착하면 함수 본문 byte 무변경이 보장돼 전사 오류 0. 751줄 분할에 효과적이었음(빌드+lint+Playwright 회귀로 교차 확인).
  2. **[중요] 봉인됐는데 코드에 없는 변경이 있을 수 있다 — task-76 clusterRadius 40→18.** loosen-clustering 회고/CONCERNS는 18이라는데 코드는 40, `git log -S "clusterRadius: 18"` 결과 18은 어느 커밋에도 없음. forge 휘발 상태 모델(default 브랜치에서 plan/run/done은 gitignore)상 **코드 변경을 git 커밋하지 않은 채 봉인하면 변경이 유실될 수 있다.** 교훈: 코드 변경이 있는 task는 봉인 전/후 반드시 `git add`+commit를 확인하고, 회고/문서가 코드와 어긋나면 git으로 교차검증할 것.

## 후속 (이번 범위 밖)
- **clusterRadius 40 vs 18 결정**: task-76 의도(18, "마커 원이 실제 겹칠 때만 클러스터")를 재적용할지 / 40 수용할지. fg-quick 후보. (CONCERNS 5-1 갱신도 함께 — 현재 18로 적혀 있음.)
- **Part 2 (task 83)**: 애니메이션 컨트롤러 추출 — 백로그 대기, 회귀 위험 본 수술.

## Doc updates
- CONTEXT.md promotion: 없음 (구현 세부)
- ADR added: 없음
