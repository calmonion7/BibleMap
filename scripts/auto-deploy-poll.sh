#!/bin/bash
# 2분마다 GitHub를 폴링해 새 커밋이 있으면 자동 배포.

set -e

WORKTREE="/Users/calmonion/Project/BibleMap/.claude/worktrees/wise-sprouting-hellman"
BRANCH="worktree-wise-sprouting-hellman"
LOG="/Users/calmonion/Library/Logs/com.biblemap.auto-deploy-poll.log"
LOCK="/tmp/biblemap-deploy.lock"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"; }

if [ -f "$LOCK" ]; then
  log "배포 진행 중 (lock 존재), 건너뜀."
  exit 0
fi

cd "$WORKTREE"

git fetch origin "$BRANCH" --quiet 2>/dev/null || { log "git fetch 실패, 건너뜀."; exit 0; }

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")

if [ "$LOCAL" = "$REMOTE" ]; then
  exit 0
fi

log "새 커밋 감지: $LOCAL -> $REMOTE. 배포 시작..."
touch "$LOCK"
trap 'rm -f "$LOCK"' EXIT

git reset --hard "origin/$BRANCH" >> "$LOG" 2>&1
bash "$WORKTREE/deploy.sh" >> "$LOG" 2>&1

log "배포 완료."
