#!/usr/bin/env python3
"""cast/*.jsx의 export const AXES 5축 조합이 서로 겹치지 않는지 단정한다(task#314 S2, 구별성 1단).
eco: 가장 짧은 형태 — cast/ 파일이 늘어날 때마다 그대로 재사용."""
import glob
import os
import re

_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend/src/sketches/cast")
_AXES = re.compile(r"export const AXES\s*=\s*\{([^}]*)\}")
_KV = re.compile(r"(\w+)\s*:\s*'([^']*)'")

seen = {}
for path in sorted(glob.glob(os.path.join(_DIR, "*.jsx"))):
    src = open(path, encoding="utf-8").read()
    m = _AXES.search(src)
    if not m:
        continue
    axes = tuple(v for _, v in _KV.findall(m.group(1)))
    name = os.path.basename(path)
    if axes in seen:
        raise SystemExit(f"구별성 위반: {name}과 {seen[axes]}이 5축 조합이 같다 {axes}")
    seen[axes] = name
    print(f"{name}: {axes}")

print(f"PASS — {len(seen)}건, 조합 중복 0")
