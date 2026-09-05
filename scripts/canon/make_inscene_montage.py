#!/usr/bin/env python3
"""장면 안 인페인팅 3판 대조 몽타주 (task 337). GPU 0.

  make_inscene_montage.py <scene-id ...> [--seed 11]

행이 장면, 열이 **판 셋**이다 — 판 합성(A1, 4/7에서 이미 그린 것) · 장면 안 앵커 끔(IN1) ·
장면 안 앵커 켬(IS1). 대조군 없이 판정하지 않는다(ADR `260825-013557`).

산출: `.forge/reports/canon-pilot/scripture-scene/montage-inscene.png` + 같은 이름의 `.json`.
판정은 `judge_scene`을 그대로 부른다 — **임계·산식은 건드리지 않는다**. 이 묶음에서 뜻이 있는 축은
C3(이음매)뿐이다: C4 잉크는 인물이 하늘을 등지지 않으면 구역 상자의 배경 어둡기를 재기 때문이다
(4/7 「규칙 실측」 1번). 그래서 셀에는 **C3 이음매**와, 같은 산식을 붙인 자리에만 적용한
**인물 잉크(칠한 자리 기준)** 를 함께 적는다.
"""
import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw

import params
import derive_scene as ds
import judge_scene as J
from make_montage import font

OUT = os.path.join(params.OUT_ROOT, "scripture-scene")
# 판 셋 — (열 제목, 라벨 접두, figures 모드)
ARMS = [("판 합성 (4/7 기존)", "A1", "plate"),
        ("장면 안 · 앵커 끔 · s0.85", "IN1", "inscene"),
        ("장면 안 · 앵커 켬 · s0.85", "IS1", "inscene"),
        ("장면 안 · 앵커 켬 · s0.95", "IH1", "inscene")]


def _lum(p):
    return np.asarray(Image.open(p).convert("L")).astype(float) / 255.0


def figure_ink(sid, label, seed, figures):
    """**이 단계가 실제로 칠한 자리** 안에서만 잰 인물 잉크.

    구역 상자로 재면 배경이 34~96%를 먹는다(4/7 실측). 단계 직전/직후 차이가 곧 「칠한 자리」라
    두 경로(판을 얹은 자리 · 장면 안에 그린 자리)에 **같은 산식**으로 붙는다.
    판정기의 C4는 건드리지 않는다 — 이 값은 표에 함께 적는 참고 수치다."""
    spec = ds.load(sid)
    plan = [(st, kind, regs) for st, kind, regs in ds.stage_plan(spec, figures)
            if not st.get("skip")]
    ids = [st["id"] for st, _, _ in plan]
    fin = os.path.join(OUT, f"{label}-final-s{seed}.png")
    if not os.path.exists(fin):
        return {}
    lum = _lum(fin)
    out = {}
    for i, (st, kind, regs) in enumerate(plan):
        if kind not in ("plate", "scene"):
            continue
        prev = ids[i - 1] if i > 0 else None
        pf = os.path.join(OUT, f"{label}-{prev}-s{seed}.png") if prev else None
        af = os.path.join(OUT, f"{label}-{st['id']}-s{seed}.png")
        if not (pf and os.path.exists(pf) and os.path.exists(af)):
            continue
        b4, a4 = _lum(pf), _lum(af)
        bs = [J.box(r) for r in regs]
        x0, y0 = min(b[0] for b in bs), min(b[1] for b in bs)
        x1, y1 = max(b[2] for b in bs), max(b[3] for b in bs)
        ch = (np.abs(a4 - b4) > 0.02)[y0:y1, x0:x1]
        rr, cc = np.flatnonzero(ch.any(1)), np.flatnonzero(ch.any(0))
        if not rr.size:
            continue
        fm = ch[rr[0]:rr[-1] + 1, cc[0]:cc[-1] + 1]
        sub = lum[y0 + rr[0]:y0 + rr[-1] + 1, x0 + cc[0]:x0 + cc[-1] + 1]
        out["+".join(regs)] = round(float((sub[fm] < J.DARK_CUT).mean()), 3)
    return out


def cell(sid, prefix, figures, seed):
    lab = f"{prefix}-{sid.replace('authored-', '')}"
    f = os.path.join(OUT, f"{lab}-final-s{seed}.png")
    if not os.path.exists(f):
        return None, lab, "그림 없음"
    spec = ds.load(sid)
    J.configure(spec, figures)          # 판정자도 생성기와 **같은 단계 목록**을 본다
    m = J.measure(OUT, lab, seed)
    seam = m["c3_seam"]
    ink = figure_ink(sid, lab, seed, figures)
    c3 = (seam["line_rows"] <= J.THRESHOLDS["c3_line_rows_max"]
          and seam["paste_seam"] <= J.THRESHOLDS["c3_paste_seam_max"])
    txt = (f"C3 {'통과' if c3 else '낙제'} · 이음매 {seam['paste_seam']:.2f}"
           + (f" @{seam['paste_seam_at']}" if seam["paste_seam_at"] else "")
           + " · 인물잉크 " + (" ".join(f"{k} {v:.3f}" for k, v in ink.items())
                              or "못 잼(직전 단계 그림이 없다)"))
    return f, lab, txt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes", nargs="+")
    ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()
    cw, chh, head, foot = 470, 248, 30, 40
    im = Image.new("RGB", (len(ARMS) * cw, head + len(a.scenes) * (chh + foot + 20)), (255, 255, 255))
    dr = ImageDraw.Draw(im)
    dr.text((6, 6), f"장면 안 인페인팅 3판 대조 — 시드 {a.seed} · task 337",
            fill=(0, 0, 0), font=font(17))
    res = {}
    for r, sid in enumerate(a.scenes):
        y = head + r * (chh + foot + 20)
        dr.text((6, y), sid, fill=(0, 0, 0), font=font(14))
        res[sid] = {}
        for c, (title, prefix, figures) in enumerate(ARMS):
            x = c * cw
            f, lab, txt = cell(sid, prefix, figures, a.seed)
            dr.text((x + 6, y + 19), f"{title}  [{lab}]", fill=(70, 70, 70), font=font(12))
            if f:
                t = Image.open(f).convert("RGB")
                t.thumbnail((cw - 12, chh))
                im.paste(t, (x + 6, y + 36))
            for i, line in enumerate([txt[:78], txt[78:156]]):
                if line:
                    dr.text((x + 6, y + 40 + chh + i * 15), line, fill=(60, 60, 60), font=font(11))
            res[sid][prefix] = {"label": lab, "summary": txt, "exists": bool(f)}
            print(f"  {sid:<46} {title:<18} {txt}")
    p = os.path.join(OUT, "montage-inscene.png")
    im.save(p)
    json.dump(res, open(os.path.join(OUT, "montage-inscene.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n{len(a.scenes)}장면 x {len(ARMS)}판 → {p}")


if __name__ == "__main__":
    main()
