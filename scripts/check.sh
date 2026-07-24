#!/bin/bash
# 배포 전 검증 게이트 (task#255) — 데이터 검증 + ERA_BANDS 3곳 정합 + 비유↔연표 커버리지 + ESLint.
# 하나라도 하드 항목 실패 시 비0 종료. 환경 의존 항목은 미충족 시 스킵-경고(하드 게이트 유지):
#   - Neo4j 연대 정합: 127.0.0.1:7687 미기동 시 스킵
#   - ESLint: frontend/node_modules 부재 시 스킵
# deploy.sh가 빌드 전 호출하며, 단독 실행도 가능(AI 불요 CI 게이트).
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
fail=0
OUT=/tmp/biblemap-check.$$.out

run() {  # run <라벨> <명령...>
  local label="$1"; shift
  if "$@" >"$OUT" 2>&1; then
    echo "  ✓ $label"
  else
    echo "  ✗ $label"; tail -8 "$OUT" | sed 's/^/      /'; fail=1
  fi
}

echo "=== check: 파일 기반 데이터 검증 (12종) ==="
for s in covenants messianic_prophecies parables_miracles topical_verses pm_map_coverage \
         chapter_sections chapter_summaries quotations person_context god_reliance traits \
         era_bands_consistency; do
  run "validate_$s" python3 -m "backend.scripts.validate_$s"
done

echo "=== check: ESLint ==="
if [ -d "$ROOT/frontend/node_modules" ]; then
  run "eslint src" bash -c "cd '$ROOT/frontend' && npx --no-install eslint src"
else
  echo "  ⊘ eslint 스킵 — frontend/node_modules 부재"
fi

echo "=== check: 연대 정합 (Neo4j) ==="
if [ -f "$ROOT/.env" ]; then set -a; . "$ROOT/.env"; set +a; fi
if python3 -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('127.0.0.1',7687)); s.close()" 2>/dev/null; then
  NEO4J_URI="${NEO4J_URI:-bolt://localhost:7687}" NEO4J_USER="${NEO4J_USER:-neo4j}" \
    run "validate_event_chronology" python3 -m backend.scripts.validate_event_chronology
else
  echo "  ⊘ validate_event_chronology 스킵 — Neo4j(127.0.0.1:7687) 미기동"
fi

rm -f "$OUT"
if [ "$fail" -ne 0 ]; then
  echo "=== check FAILED — 위 ✗ 항목 수정 후 재시도 ==="
  exit 1
fi
echo "=== check PASS ==="
