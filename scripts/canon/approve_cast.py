#!/usr/bin/env python3
"""사람이 고른 인물 판 결정을 정본에 옮겨 적는다 (task 331 S4). GPU 0.

  approve_cast.py <id> --seed 11 --anchor on|off [--label a] [--why "한 줄 근거"]
  approve_cast.py <id> --hold "보류 사유"

  · `cast/<id>.json`의 `plate`(seed·anchor·ipScale·approved·approvedOn)를 채운다
  · 승인이면 `<label>-face-s<seed>.png`를 `frozen/<id>.png`로 복사하고 `frozen/FROZEN.md`에 선택 근거 행을 붙인다
판정 자체는 사람이 한다 — 이 스크립트는 사람이 말한 값만 적는다(값을 고르지 않는다).
"""
import argparse
import datetime
import json
import os
import shutil
import sys

import params

CAST_DIR = os.path.join(params.CANON_DIR, "cast")
OUT = os.path.join(params.OUT_ROOT, "cast")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cast")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--anchor", choices=["on", "off"])
    ap.add_argument("--label", default="a")
    ap.add_argument("--why", default="")
    ap.add_argument("--hold", default=None, help="보류 사유 — 승인 대신 기록만")
    a = ap.parse_args()
    path = os.path.join(CAST_DIR, f"{a.cast}.json")
    with open(path, encoding="utf-8") as fh:
        c = json.load(fh)
    today = datetime.date.today().isoformat()
    if a.hold:
        c["plate"].update({"approved": f"보류: {a.hold}", "approvedOn": today})
    else:
        if a.seed is None or a.anchor is None:
            sys.exit("--seed와 --anchor가 필요하다(또는 --hold)")
        face = os.path.join(OUT, a.cast, f"{a.label}-face-s{a.seed}.png")
        if not os.path.exists(face):
            sys.exit(f"얼굴 크롭이 없다: {face}")
        c["plate"].update({"seed": a.seed, "anchor": a.anchor == "on", "label": a.label,
                           "approved": "승인", "approvedOn": today})
        shutil.copy(face, os.path.join(params.FROZEN, f"{a.cast}.png"))
        with open(os.path.join(params.FROZEN, "FROZEN.md"), "a", encoding="utf-8") as fh:
            fh.write(f"\n### {a.cast} seed {a.seed} · 앵커 {'켬 ' + str(c['plate']['ipScale']) if a.anchor == 'on' else '끔'} "
                     f"· 문구 {a.label} ({today}, 판 경로 · ADR 260904-055320)\n\n"
                     f"- 출처 `cast/{a.cast}/{a.label}-P1-s{a.seed}.png` 머리 크롭(몸 bbox 위 20%) → `frozen/{a.cast}.png`\n"
                     f"- 선택 근거(사람 육안): {a.why or '(미기재)'}\n")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(c, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"{a.cast}: {c['plate']}")


if __name__ == "__main__":
    main()
