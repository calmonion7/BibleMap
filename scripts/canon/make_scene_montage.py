#!/usr/bin/env python3
"""장면 몽타주 + 기계 판정 표 (task 333). GPU 0.

  make_scene_montage.py <묶음> <scene-id ...> [--label A1] [--seed 11]
  예: make_scene_montage.py A $(cat .forge/scratch/bundle-A.txt) --label A1

산출: `.forge/reports/canon-pilot/scripture-scene/montage-<묶음>.png`(3×3, 정차지 id·시드 라벨 · 판정 요약) +
      `montage-<묶음>.json`(장면별 축 수치·통과 여부 — 표에 붙일 재료).
판정은 `judge_scene`을 그대로 부른다 — 임계·산식은 코드의 공통 상수(회귀 가드), 적용 축은 명세에서 파생.
"""
import argparse
import json
import os

from PIL import Image, ImageDraw

import params
import derive_scene as ds
import judge_scene as J
from make_montage import font

OUT = os.path.join(params.OUT_ROOT, "scripture-scene")


def judge_one(sid, label, seed):
    J.configure(ds.load(sid))
    f = os.path.join(OUT, f"{label}-final-s{seed}.png")
    if not os.path.exists(f):
        return None
    m = J.measure(OUT, label, seed)
    m["verdict"] = J.verdict(m)
    m["axes"] = list(J.AXES)
    return m


def summary(m):
    if m is None:
        return "그림 없음"
    v = m["verdict"]
    inks = {k: round(x, 3) for k, x in m["c4_style"].items() if k.startswith("ink_")}
    return (f"{'통과' if all(v.values()) else '낙제'} "
            + " ".join(f"{k}{'✓' if y else '✗'}" for k, y in v.items())
            + f" · 이음매 {m['c3_seam']['paste_seam']:.2f} · 잉크 {inks} 비 {m['c4_style']['ink_ratio']:.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle")
    ap.add_argument("scenes", nargs="+")
    ap.add_argument("--label", default=None, help="라벨(기본: <묶음>1)")
    ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()
    label = a.label or f"{a.bundle}1"
    res, cells = {}, []
    for sid in a.scenes:
        # **장면마다 라벨이 달라야 한다** — 생성기 산출물 이름은 `<label>-<stage>-s<seed>.png`로 장면 id를 담지 않아,
        # 같은 라벨을 쓰면 9장면이 서로를 덮어쓴다(2026-09-04 실측, 첫 실행에서 잡았다).
        lab = f"{label}-{sid.replace('authored-', '')}"
        f = os.path.join(OUT, f"{lab}-final-s{a.seed}.png")
        m = judge_one(sid, lab, a.seed) if os.path.exists(f) else None
        res[sid] = m
        cells.append((sid, f if os.path.exists(f) else None, summary(m)))
    cw, ch = 608, 320
    cols = 3
    rows = (len(cells) + cols - 1) // cols
    im = Image.new("RGB", (cols * cw, rows * (ch + 46) + 26), (255, 255, 255))
    dr = ImageDraw.Draw(im)
    dr.text((6, 5), f"묶음 {a.bundle} — {len(cells)}장면 · 라벨 {label} · 시드 {a.seed}", fill=(0, 0, 0), font=font(16))
    for i, (sid, f, s) in enumerate(cells):
        x, y = (i % cols) * cw, 26 + (i // cols) * (ch + 46)
        if f:
            t = Image.open(f).convert("RGB")
            t.thumbnail((cw - 8, ch))
            im.paste(t, (x + 4, y + 22))
        dr.text((x + 5, y + 3), f"{i + 1}. {sid}", fill=(0, 0, 0), font=font(13))
        dr.text((x + 5, y + 26 + ch), s[:96], fill=(60, 60, 60), font=font(11))
    p = os.path.join(OUT, f"montage-{a.bundle}.png")
    im.save(p)
    json.dump(res, open(os.path.join(OUT, f"montage-{a.bundle}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"{len(cells)}장면 → {p}")
    for sid, _, s in cells:
        print(f"  {sid:<46} {s}")


if __name__ == "__main__":
    main()
