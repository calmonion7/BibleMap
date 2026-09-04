#!/usr/bin/env python3
"""36행 장면 검토 표 생성 (task 332 S5). GPU 0.

  make_scene_table.py            # notes/SCENES-DAVID-TOUR.md의 「검토 표」 절을 명세에서 다시 만든다(검토 열은 기존 값 보존)
사람 관문의 4열: 장면 · 고정한 순간 · 인물+지물 · 배경 한 줄. 검토 열(✅ / 수정 요청)은 사람이 적는다 — 이 스크립트는 채우지 않는다.
"""
import glob
import json
import os
import re

import params

SCENES = os.path.join(params.CANON_DIR, "scenes")
NOTE = os.path.join(params.NOTES, "SCENES-DAVID-TOUR.md")
TOUR = os.path.join(params.REPO_ROOT, "data", "tours", "david-united-kingdom.json")
BEGIN, END = "<!-- scene-table:begin -->", "<!-- scene-table:end -->"


def rows():
    order = [s["id"] for s in json.load(open(TOUR, encoding="utf-8"))["stops"]]
    out = []
    for sid in order:
        p = os.path.join(SCENES, f"{sid}.json")
        if not os.path.exists(p) or sid == "authored-david-goliath-gath":   # 삼상17은 v41로 봉인됨 — 이 표의 관문이 아니다
            continue
        d = json.load(open(p, encoding="utf-8"))
        figs = " · ".join(f"{f['cast']}({f['prop']})" for f in d["figures"])
        bg = " · ".join(b["what"] for b in d["background"][:3])
        out.append({"id": sid, "title": d["title"], "verse": d["moment"]["verse"], "moment": d["moment"]["why"].split("—")[0].split(".")[0].strip(),
                    "figures": figs, "background": bg})
    return out


def main():
    old = {}
    if os.path.exists(NOTE):
        txt = open(NOTE, encoding="utf-8").read()
        for m in re.finditer(r"^\| \d+ \| `([a-z0-9-]+)`.*\| ([^|]*) \|$", txt, re.M):
            old[m.group(1)] = m.group(2).strip()
    else:
        txt = ("# 다윗 투어 36장면 — 명세 검토 표와 규칙 실측\n\n"
               "장면 명세는 `scripts/canon/scenes/<id>.json`(한국어가 정본, 영문 프롬프트는 `derive_scene.py`가 파생). 이 표는 사람 관문 —\n"
               "**GPU 전에 순간·인물·지물·배경을 한 번 훑는 가장 싼 관문**(PROCESS.md 「내용이 틀리면 그림 전체가 다른 장면」). 검토 열은 사람이 적는다.\n\n"
               f"## 검토 표 (3/7 · 2026-09-04)\n\n{BEGIN}\n{END}\n\n"
               "## 규칙 실측\n\n(4/7부터 채움)\n")
    r = rows()
    lines = ["| # | 장면 | 순간(절) | 인물(지물) | 배경 한 줄 | 검토 |", "|---|---|---|---|---|---|"]
    for i, x in enumerate(r, 1):
        lines.append(f"| {i} | `{x['id']}` {x['title']} | {x['verse']} — {x['moment']} | {x['figures']} | {x['background']} | {old.get(x['id'], '')} |")
    table = "\n".join(lines)
    txt = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), f"{BEGIN}\n{table}\n{END}", txt, flags=re.S)
    open(NOTE, "w", encoding="utf-8").write(txt)
    json.dump(r, open(os.path.join(params.OUT_ROOT, "scene-table.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(r)}행 → {NOTE}")


if __name__ == "__main__":
    main()
