#!/bin/bash
set -e

WORKTREE="$(cd "$(dirname "$0")" && pwd)"
LOG="/Users/calmonion/Library/Logs/com.biblemap.deploy.log"
LOCK="/tmp/biblemap-deploy.lock"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

if [ -f "$LOCK" ]; then
  log "배포 이미 진행 중 (lock 존재), 건너뜀."
  exit 1
fi
touch "$LOCK"
trap 'rm -f "$LOCK"' EXIT

log "=== BibleMap 배포 시작 ==="

# macOS 키체인 우회 (CI 환경)
TMP_DOCKER_CONFIG=$(mktemp -d)
echo '{"auths":{}}' > "$TMP_DOCKER_CONFIG/config.json"
# docker는 $DOCKER_CONFIG/cli-plugins에서 compose 플러그인을 찾으므로 기본 위치를 연결
# (이게 없으면 임시 config에 cli-plugins가 없어 `docker compose`가 인식되지 않음)
if [ -d "$HOME/.docker/cli-plugins" ]; then
  ln -sf "$HOME/.docker/cli-plugins" "$TMP_DOCKER_CONFIG/cli-plugins"
fi
export DOCKER_CONFIG="$TMP_DOCKER_CONFIG"

# .env에서 NEO4J_PASSWORD 로드 — 호스트에서 직접 실행하는 inject 스크립트가 동일 비번을 쓰도록
if [ -f "$WORKTREE/.env" ]; then
  set -a; . "$WORKTREE/.env"; set +a
fi

# 순서 근거(ADR 260801-195022): 주입은 멱등이므로 검증 **앞**에서 DB를 정본으로 되돌린 뒤 게이트가
# 판정하게 한다(뒤에 두면 아무 일도 못 한다). npm install도 게이트 앞이어야 ESLint가 스킵되지 않는다.
log "[1/7] Neo4j 도달 대기..."
ready=false
for i in $(seq 1 15); do
  if python3 -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('127.0.0.1',7687)); s.close()" 2>/dev/null; then
    ready=true
    break
  fi
  log "      Neo4j 준비 대기 중... ($i/15)"
  sleep 2
done
if [ "$ready" != true ]; then
  log "      Neo4j(127.0.0.1:7687) 미도달 — 15회 재시도 후에도 미기동. 배포 중단."
  exit 1
fi
log "      도달."

# 2>/dev/null 없음 — 예외(예: NEO4J_PASSWORD 미설정)를 대기 실패로 위장시키지 않는다.
log "[2/7] 데이터 주입 (한글 이름 · 연대 교정, 둘 다 멱등)..."
python3 "$WORKTREE/backend/scripts/inject_ko_names.py"
python3 "$WORKTREE/backend/scripts/inject_date_corrections.py"
log "      완료."

log "[3/7] 프론트엔드 의존성 설치..."
cd "$WORKTREE/frontend"
npm install --silent
log "      완료."

log "[4/7] 배포 전 검증 게이트 (데이터·ERA_BANDS 정합·커버리지·ESLint·연대, 엄격 모드)..."
cd "$WORKTREE"
CHECK_STRICT=1 bash "$WORKTREE/scripts/check.sh" 2>&1 | tee -a "$LOG"
if [ "${PIPESTATUS[0]}" -ne 0 ]; then
  log "      검증 실패 — 배포 중단 (위 ✗ 항목 수정 후 재배포)."
  exit 1
fi
log "      검증 통과."

log "[5/7] 프론트엔드 빌드..."
cd "$WORKTREE/frontend"
npm run build --silent
log "      완료: frontend/dist/"

log "[6/7] API 이미지 빌드..."
cd "$WORKTREE"
docker compose -p biblemap build api
log "      완료."

log "[7/7] 컨테이너 재시작..."
docker compose -p biblemap up -d api
# nginx는 이미지 빌드가 없고 바인드 마운트 스펙도 불변이라 nginx.conf만 바뀌면 Compose가 재생성을
# 판단하지 못해 no-op 처리된다(task#263) — 정적 서빙 컨테이너라 매 배포 강제 재생성해도 비용이 거의 없다.
docker compose -p biblemap up -d --force-recreate nginx
log "      완료."

log "=== 배포 완료 ==="
