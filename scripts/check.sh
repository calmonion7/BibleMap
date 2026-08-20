#!/bin/bash
# 배포 전 검증 게이트 (task#255) — 데이터 검증 + ERA_BANDS 3곳 정합 + 인트로↔실제 메뉴 정합 + 비유↔연표·장면 커버리지 + ESLint.
# 하나라도 하드 항목 실패 시 비0 종료. 환경 의존 항목은 미충족 시 스킵-경고(하드 게이트 유지):
#   - Neo4j 연대 정합: 127.0.0.1:7687 미기동 시 스킵
#   - ESLint: frontend/node_modules 부재 시 스킵
# CHECK_STRICT=1이면 위 두 스킵이 실패로 승격된다(task#259) — 배포 경로는 반드시 이 모드로 부른다.
# 스킵-경고 계약은 단독 개발 실행용으로 유지(Neo4j 없이 파일 검증만 돌리는 정당한 용법).
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

skip() {  # skip <라벨> <사유> — 엄격 모드에서는 스킵이 실패다
  if [ "${CHECK_STRICT:-0}" != 0 ]; then
    echo "  ✗ $1 — $2 (CHECK_STRICT: 스킵 불가)"; fail=1
  else
    echo "  ⊘ $1 스킵 — $2"
  fi
}

echo "=== check: 파일 기반 데이터 검증 (16종 + 정합 대조군) ==="
for s in covenants messianic_prophecies parables_miracles topical_verses pm_map_coverage \
         scene_coverage chapter_sections chapter_summaries quotations person_context \
         god_reliance traits era_bands_consistency approx_book_verses intro_menu_parity \
         curated_persons; do
  run "validate_$s" python3 -m "backend.scripts.validate_$s"
done
# 정합 검사 자신의 대조군(task#277·278) — 고의 드리프트 주입에 FAIL하는지 인메모리로 순회 확인.
# 기준선 PASS만으론 게이트가 살아있음을 증명하지 못한다(ADR 260820-003946).
run "validate_intro_menu_parity --selftest" python3 -m backend.scripts.validate_intro_menu_parity --selftest
run "validate_curated_persons --selftest" python3 -m backend.scripts.validate_curated_persons --selftest

echo "=== check: 영구 forge 문서 추적 (배포 차단 가드) ==="
# 데이터 검증이 아니므로 위 16종 루프에 넣지 않는다(task#279).
# 배포 경로에서도 살아있다 — task#279가 계획의 반대 사실을 실측했다. deploy.yml은 개발 트리와
# 같은 디렉터리에서 `git reset --hard origin/main` 후 deploy.sh를 부르는데, 하드리셋은 추적
# 파일만 되돌리고 미추적 파일은 남긴다(`git clean`이 아니다). 따라서 미추적 ADR·회고는 이
# 게이트에 노출되고, CHECK_STRICT=1인 배포 경로에서 **배포를 중단시킨다**(실패 메시지가
# 미추적 파일 목록을 지목하므로 무음 실패는 아니다). 이 강도가 맞는지는 사람이 정할 몫 —
# 약화하려면 이 절을 CHECK_STRICT 분기 밖으로 뺀다.
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  run "validate_forge_docs_tracked (배포 차단 가드)" python3 -m backend.scripts.validate_forge_docs_tracked
  run "validate_forge_docs_tracked --selftest (배포 차단 가드)" python3 -m backend.scripts.validate_forge_docs_tracked --selftest
else
  skip "validate_forge_docs_tracked (배포 차단 가드)" "git 미가용(작업트리 아님)"
  skip "validate_forge_docs_tracked --selftest (배포 차단 가드)" "git 미가용(작업트리 아님)"
fi

echo "=== check: 프론트 (ESLint · 유닛 테스트) ==="
if [ -d "$ROOT/frontend/node_modules" ]; then
  run "eslint src" bash -c "cd '$ROOT/frontend' && npx --no-install eslint src"
  run "vitest" bash -c "cd '$ROOT/frontend' && npm test --silent"
else
  skip "eslint src" "frontend/node_modules 부재"
  skip "vitest" "frontend/node_modules 부재"
fi

echo "=== check: 연대 정합 (Neo4j) ==="
if [ -f "$ROOT/.env" ]; then set -a; . "$ROOT/.env"; set +a; fi
if python3 -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('127.0.0.1',7687)); s.close()" 2>/dev/null; then
  NEO4J_URI="${NEO4J_URI:-bolt://localhost:7687}" NEO4J_USER="${NEO4J_USER:-neo4j}" \
    run "validate_event_chronology" python3 -m backend.scripts.validate_event_chronology
else
  skip "validate_event_chronology" "Neo4j(127.0.0.1:7687) 미기동"
fi

rm -f "$OUT"
if [ "$fail" -ne 0 ]; then
  echo "=== check FAILED — 위 ✗ 항목 수정 후 재시도 ==="
  exit 1
fi
echo "=== check PASS ==="
