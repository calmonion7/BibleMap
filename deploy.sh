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

log "[1/3] 프론트엔드 빌드..."
cd "$WORKTREE/frontend"
npm install --silent
npm run build --silent
log "      완료: frontend/dist/"

log "[2/3] API 이미지 빌드..."
cd "$WORKTREE"
docker compose -p biblemap build api
log "      완료."

log "[3/4] 컨테이너 재시작..."
docker compose -p biblemap up -d api nginx
log "      완료."

log "[4/4] 한글 이름 주입..."
injected=false
for i in $(seq 1 15); do
  if python3 "$WORKTREE/backend/scripts/inject_ko_names.py" 2>/dev/null; then
    injected=true
    break
  fi
  log "      Neo4j 준비 대기 중... ($i/15)"
  sleep 2
done
if [ "$injected" != true ]; then
  log "      한글 이름 주입 실패 — 15회 재시도 후에도 미성공. 배포 중단."
  exit 1
fi
log "      완료."

log "=== 배포 완료 ==="
