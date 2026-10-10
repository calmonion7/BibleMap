#!/bin/bash
# dev neo4j 시드 — prod 볼륨을 dev 볼륨으로 복사한다(ADR 261010-110220: dev 시드 절차는 BibleMap 몫).
# 로더(load_*)로 다시 만들지 않는 이유: 로더가 연대 교정을 덮어쓴다(ADR 260801-195022).
# prod 는 멈추지 않는다 — 배포 사이 prod 그래프는 쓰기가 없어 뜨거운 복사로 충분하고, dev neo4j 가 기동 때
# 트랜잭션 로그를 복구한다. 끝에 노드·관계 수를 prod 와 대조해 어긋나면 실패한다.
# 사용: scripts/dev-seed-neo4j.sh   (전제: ~/runtime/biblemap/dev/{.env,docker-compose.yml})
set -euo pipefail
RT="$HOME/runtime/biblemap/dev"
SRC=biblemap_neo4j_data
DST=biblemap-dev_neo4j_data
[ -f "$RT/.env" ] && [ -f "$RT/docker-compose.yml" ] || { echo "[DevSeed] 실행 자리 없음: $RT" >&2; exit 1; }
set -a; . "$RT/.env"; set +a

count() {  # count <bolt 포트> → "노드 관계"
  python3 - "$1" <<'PY'
import os, sys
from neo4j import GraphDatabase
d = GraphDatabase.driver(f"bolt://localhost:{sys.argv[1]}", auth=("neo4j", os.environ["NEO4J_PASSWORD"]))
with d.session() as s:
    n = s.run("MATCH (n) RETURN count(n)").single()[0]
    r = s.run("MATCH ()-[r]->() RETURN count(r)").single()[0]
print(n, r)
d.close()
PY
}

cd "$RT"
echo "[DevSeed] dev neo4j 정지·볼륨 준비"
TAEBRO_HTTP_PORT=8082 docker compose -p biblemap-dev stop neo4j >/dev/null 2>&1 || true
TAEBRO_HTTP_PORT=8082 docker compose -p biblemap-dev create neo4j >/dev/null
echo "[DevSeed] $SRC → $DST 복사"
docker run --rm -v "$SRC":/from:ro -v "$DST":/to alpine sh -c 'rm -rf /to/* && cp -a /from/. /to/'
echo "[DevSeed] dev neo4j 기동"
TAEBRO_HTTP_PORT=8082 docker compose -p biblemap-dev up -d --no-build neo4j >/dev/null
for i in $(seq 1 60); do count "$NEO4J_BOLT_PORT" >/dev/null 2>&1 && break; sleep 2; done
dev=$(count "$NEO4J_BOLT_PORT"); prod=$(count 7687)
echo "[DevSeed] 노드·관계 prod=($prod) dev=($dev)"
[ "$dev" = "$prod" ] || { echo "[DevSeed] 불일치 — 시드 실패" >&2; exit 1; }
echo "[DevSeed] 완료"
