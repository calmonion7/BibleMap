# 2026-07-24 — 검증·정합 deploy.sh 로컬 게이트 (task#255) [일괄 승급]

## Plan vs actual
- validate_* 12종 + ESLint + ERA_BANDS 3곳 정합을 `scripts/check.sh`로 묶어 deploy.sh 빌드 전 배선. 세부는 `.forge/done/260724-110719-predeploy-validation-gate/run.md`.

## Learnings
- Do differently next time:
  - **배포 전 검증 게이트 패턴**: 흩어진 검증을 단일 `scripts/check.sh`로 묶어 deploy.sh 빌드 **앞단**에 배선(실패 시 빌드·배포 차단). 환경 의존 항목(Neo4j 127.0.0.1:7687·frontend/node_modules)은 가드로 **스킵-경고**하되 파일 기반 검증은 하드 게이트. `tee -a $LOG` 후 `PIPESTATUS[0]`로 종료코드 포착(set -e·비-pipefail 환경).
  - **신규 validate_* 추가 시 반드시 check.sh 목록에도 등록** — 안 하면 게이트가 안 잡는다.
  - **배포 footgun**: deploy.sh가 check.sh를 부르므로, 신규 스크립트(check.sh·validate_*)는 **deploy.sh 변경과 반드시 함께 커밋**. 러너 체크아웃에 파일이 없으면 게이트가 파일부재로 배포를 막는다.
  - **ERA_BANDS 3벌 중복(TimelineView·persons.py·stats.py + covenants.json)** 은 근본 해소(공유 설정) 대신 정합 검증 게이트로 드리프트 차단. source 정규식 파싱 시 `float("-inf")`는 첫 `)`에서 잘리므로 "inf" 부분문자열 검출로 정규화.

## Doc updates
- CONTEXT.md: none. ADR: none (게이트 도입은 deploy.sh 호출 한 줄 제거로 되돌릴 수 있어 3요건 미충족 — 회고에 보존).
