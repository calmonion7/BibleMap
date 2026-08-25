"""임의의 산출 묶음에 세 축을 걸어 표를 낸다(task#317 S1 이후 공용).

S0가 세운 자를 **그대로 쓴다** — 임계는 `notes/s0-baseline.json`에 못박힌 값을 읽고 여기서
다시 파생하지 않는다. 자를 만드는 슬라이스와 자를 쓰는 슬라이스를 가른 것이 S0가 따로 선 이유이고,
「결과가 마음에 안 든다」고 자를 바꾸는 것은 결론 선취다(ADR `260825-013557` 2026-08-25 개정 따름 정리 2).

축 B는 짝을 요구한다 — 같은 시드의 **레퍼런스 미탑재** 산출이 기준선이다. 묶음 안에 그것이 없으면
`scene/a-none-s{seed}.png`로 되돌아간다(같은 시드·같은 콘티라 짝으로 성립한다).

Usage: .../python judge_batch.py <dir> [<dir> ...] [--json OUT]
"""
import glob
import json
import os
import sys

import judge_axes as ja
import judge_metrics as jm
import judge_style as js
import params
from PIL import Image

BASE = json.load(open(os.path.join(params.NOTES, "s0-baseline.json"), encoding="utf-8"))
A_THR = BASE["axis_a"]["thresholds"]
B_THR = BASE["axis_b"]["threshold"]
C_THR = BASE["axis_c"]["threshold"]
LADDER = {float(k): v for k, v in BASE["axis_b"]["ladder"].items()}


def _seed(p):
    try:
        return int(os.path.basename(p).rsplit("-s", 1)[1].split(".")[0])
    except (IndexError, ValueError):
        return params.SEED_FIXED


def main():
    dirs = [a for a in sys.argv[1:] if not a.startswith("--")]
    paths = sorted(p for d in dirs for p in glob.glob(os.path.join(d, "*.png")))
    if not paths:
        sys.exit(f"판정할 png가 없다: {dirs}")

    person, frac = ja._person_area()
    embedder = jm.Embedder()
    box = ja.head_boxes()
    frozen = {n: embedder.embed(Image.open(os.path.join(params.FROZEN, f"{n}.png")))
              for n in ja.PEOPLE}
    base_cache = {}

    def baseline_emb(seed, who):
        if (seed, who) not in base_cache:
            bp = os.path.join(params.OUT_ROOT, "scene", f"{ja.BASELINE_COND}-s{seed}.png")
            if not os.path.exists(bp):
                sys.exit(f"축 B 짝 기준선이 없다: {bp}")
            base_cache[(seed, who)] = embedder.embed(ja.scene_image(bp).crop(box[who]))
        return base_cache[(seed, who)]

    print(f"임계 — A: ink>={A_THR['ink_min']:.4f}, p05<={A_THR['val_p05_max']:.3f}"
          f" · B: 점수>{B_THR:+.4f} · C: 농축비>{C_THR:.3f}   (전부 S0에서 파생, notes/s0-baseline.json)")
    print(f"정답지 구간 — ink {A_THR['reference_band']['ink'][0]:.3f}~{A_THR['reference_band']['ink'][1]:.3f}\n")
    print(f"{'파일':26s} {'A:ink':>7s} {'p05':>6s} {'A':>2s}  {'B:다윗':>8s} {'B:골리앗':>8s} {'B':>2s}  {'C:농축':>7s} {'C':>2s}")
    rows = []
    for p in paths:
        m = js.style_metrics(p)
        a_ok = js.passes(m, A_THR)
        e = ja._edge_energy(p)
        c = float((e[person].sum() / e.sum()) / frac)
        im = ja.scene_image(p)
        b = {}
        for who in ja.PEOPLE:
            b[who] = ja._transfer_score(embedder.embed(im.crop(box[who])),
                                        baseline_emb(_seed(p), who), frozen, who)[0]
        b_ok = all(v > B_THR for v in b.values())
        c_ok = c > C_THR
        rows.append({"file": os.path.basename(p), "ink": m["ink"], "val_p05": m["val_p05"],
                     "axis_a": a_ok, "b_david": b["david"], "b_goliath": b["goliath"],
                     "axis_b": b_ok, "enrich": c, "axis_c": c_ok})
        print(f"{os.path.basename(p):26s} {m['ink']:7.4f} {m['val_p05']:6.3f} {'✅' if a_ok else '❌'}"
              f"  {b['david']:+8.4f} {b['goliath']:+8.4f} {'✅' if b_ok else '❌'}"
              f"  {c:7.3f} {'✅' if c_ok else '❌'}")

    n3 = sum(r["axis_a"] and r["axis_b"] and r["axis_c"] for r in rows)
    print(f"\n세 축 동시 성립 {n3}/{len(rows)}")
    if "--json" in sys.argv:
        json.dump(rows, open(sys.argv[sys.argv.index("--json") + 1], "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
