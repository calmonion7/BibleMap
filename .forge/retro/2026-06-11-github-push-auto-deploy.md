# 2026-06-11 — github main 푸시 자동 배포 복구 (task 11)

## 계획 vs 실제

- 계획대로 간 것:
  - S1 `deploy.yml` cd 경로 죽은 워크트리 → 메인 레포(`/Users/calmonion/Project/BibleMap`) 수정. S2 고아 `scripts/auto-deploy-poll.sh` 제거. S3 push→배포 트리거.
  - 최종 검증: deploy 잡 success(`gh run 27321719910`), `localhost:8080` 200, 서빙 번들 `index-Diqz6f4n.js`에 task 10 에러 UI 문자열 포함 → 최신 빌드 라이브.
- 발산:
  1. **S3 1차 실패 → deploy.sh 잠복 버그 발견·수정(비목표 침범).** 경로 수정으로 배포가 **CI에서 처음 실제 실행**되며 `docker compose -p biblemap build api`가 `unknown shorthand flag: 'p'`(exit 125)로 실패. 근본 원인: deploy.sh가 키체인 우회용 `DOCKER_CONFIG=$(mktemp -d)`로 바꾸는데 docker는 `$DOCKER_CONFIG/cli-plugins`에서 compose 플러그인을 찾음 → 임시 디렉터리엔 없어 `docker compose` 미인식. 플랜의 "deploy.sh 정상, 손대지 않음" 전제가 틀림. `$HOME/.docker/cli-plugins` 심볼릭 링크 1줄 추가로 수정.
  2. **커밋 2개·푸시 2회**(`1f0e772` 실패 → `60716ea` 성공), run.md는 단일 유지.
  3. 직전 CI 런이 전부 죽은 cd에서 즉사해서 docker 스텝이 CI에서 한 번도 안 돌았음 → 잠복 버그가 이제야 노출.

## 학습

- 다음에 다르게 할 것:
  1. **CI 파이프라인의 진입점(여기선 cd 경로)이 깨져 있으면 그 하류 스텝은 전부 "미검증"으로 취급할 것.** 진입점을 고치면 한 번도 안 돌던 하류에서 잠복 버그가 줄줄이 드러날 수 있다(여기선 docker compose 플러그인). 진입점 수정 = "이제부터 디버깅 시작"으로 보고, 한 방에 끝난다고 가정하지 말 것.
  2. **`DOCKER_CONFIG` override는 `docker compose` 플러그인 탐색을 깬다.** docker는 `$DOCKER_CONFIG/cli-plugins`(기본 `~/.docker/cli-plugins`)에서 플러그인을 찾으므로, 키체인 우회 등으로 DOCKER_CONFIG를 빈 임시 디렉터리로 바꾸면 compose 자체가 사라진다. 임시 config을 쓸 땐 cli-plugins를 같이 연결할 것.
  3. **launchd self-hosted 러너는 로그인 셸과 환경이 다르다.** 인터랙티브 셸에서 되는 docker가 러너 환경(최소 PATH, override된 DOCKER_CONFIG)에선 안 될 수 있다. CI 동작은 인터랙티브 재현이 아니라 **실제 푸시→런 관찰**로만 확정된다(이 프로젝트 누적 교훈: graphview/map 회고의 "런타임에서만 검증 가능"과 같은 결).
  4. 검증 수단으로 `gh run watch --exit-status` + 서빙 번들 grep(배포된 빌드에 기대 문자열 포함 확인)이 end-to-end 실증에 유효했다.

## 문서 업데이트
- CONTEXT.md 승격: 없음 (구현 디테일 — 글로서리 오염 방지).
- ADR 추가: 없음 (옵션 A는 1줄 가역적이라 "되돌리기 어려움" 미충족; deploy.sh 수정은 버그 픽스로 트레이드오프 결정 아님).

## 후속 (이번 범위 밖)
- `deploy.sh` 단계번호 표기(`[1/3]`→`[3/4]`) 불일치 — 로깅 화장, 미수정.
- (task 10에서 이월) react-hooks v7 `set-state-in-effect` 룰 정책 — SidePanel 기존 lint 위반 + 룰 핀/리팩터 결정.
