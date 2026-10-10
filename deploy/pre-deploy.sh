#!/bin/bash
# 배포 전 단계 — deploy.yml 이 bin/deploy 앞에서 부른다. 사용: deploy/pre-deploy.sh <prod|dev>
# 순서 근거(ADR 260801-195022): 주입은 멱등이므로 검증 **앞**에서 그 env 의 DB를 정본으로 되돌린 뒤
# 게이트가 판정한다. npm ci 도 게이트 앞이어야 ESLint·vitest가 스킵되지 않는다(엄격 모드는 스킵=실패).
set -euo pipefail
ENV="${1:?사용: pre-deploy.sh <prod|dev>}"
case "$ENV" in prod|dev) ;; *) echo "[PreDeploy] env 는 prod|dev: $ENV" >&2; exit 2 ;; esac
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RT_ENV="$HOME/runtime/biblemap/$ENV/.env"
[ -f "$RT_ENV" ] || { echo "[PreDeploy] 실행 자리 .env 없음: $RT_ENV" >&2; exit 1; }
set -a; . "$RT_ENV"; set +a
export NEO4J_URI="bolt://localhost:${NEO4J_BOLT_PORT}"

echo "[PreDeploy] 1/3 프론트 의존성 (npm ci)"
(cd "$ROOT/frontend" && npm ci --silent)

echo "[PreDeploy] 2/3 데이터 주입 → $ENV neo4j (:$NEO4J_BOLT_PORT, 한글 이름 · 연대 교정, 둘 다 멱등)"
python3 "$ROOT/backend/scripts/inject_ko_names.py"
python3 "$ROOT/backend/scripts/inject_date_corrections.py"

echo "[PreDeploy] 3/3 검증 게이트 (엄격 모드)"
CHECK_STRICT=1 bash "$ROOT/scripts/check.sh"
