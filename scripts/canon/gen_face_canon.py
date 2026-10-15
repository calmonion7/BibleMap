#!/usr/bin/env python3
"""task#346 S1 — Z-Image-Turbo로 사울·다윗(성인) 정면 머리 얼굴 정본 후보를 만든다.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV gen_face_canon.py [--out ~/.local/biblemap-imggen/face-canon]

후보는 레포 밖(--out/<인물>/s<시드>.png)에 둔다. 어휘는 cast/<id>.json의 era·age·hair·beard·headwear에서 따오고,
두 사람이 갈리도록 나이·얼굴형·수염 길이만 이 파일에서 더한다(사울: 장년·넓은 각진 턱, 다윗: 청년·갸름한 얼굴).
Z-Image 생성 프로세스는 batch/run_scene.py의 enc/gen 분리 워커를 그대로 쓴다. 머신에서 생성은 한 번에 하나.
"""
import argparse, os, sys

import params

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "batch"))
import run_scene

STYLE = "warm cream paper, soft pencil and colored-pencil storybook illustration, gentle hand-drawn lines"
# 인물별 구별 낱말(정본 어휘에 없는 얼굴 골격·나이 — 구별 기준 ⑤용)
LOOK = {
    "saul": "a man in his fifties with a broad square face, heavy brow and strong jaw, thick full head of dark hair, short trimmed beard",
    "david": "a lean young man in his twenties with a narrow oval face, high cheekbones, gentle eyes, short light stubble beard",
    # task#348 — 사울(장년·검은 머리·넓은 턱)과 갈리게: 아주 늙고 마른 얼굴, 머리를 덮는 백발, 가슴까지 오는 흰 수염(대머리 금지 — 346)
    "samuel": "a very old thin man in his eighties with a gaunt narrow face, hollow cheeks, deep wrinkles and sunken wise eyes, "
              "thick long white hair, very long flowing white beard down to the chest",
}


def prompt(cid):
    import json
    c = json.load(open(os.path.join(HERE, "cast", f"{cid}.json"), encoding="utf-8"))
    return (f"{STYLE}, close-up head portrait, facing forward, plain cream background. "
            f"{c['era']} {LOOK[cid]}, {c['hair']}, {c['beard']}, hair covering the whole head down to the forehead, no hat, dark wool tunic collar.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.expanduser("~/.local/biblemap-imggen/face-canon"))
    ap.add_argument("--who", nargs="+", default=["saul", "david"])
    a = ap.parse_args()
    w, h = params.FACE_CANON_SIZE
    for cid in a.who:
        d = os.path.join(a.out, cid)
        os.makedirs(d, exist_ok=True)
        jobs = [{"prompt": prompt(cid), "seed": s, "w": w, "h": h, "out": os.path.join(d, f"s{s}.png")}
                for s in params.FACE_CANON_SEEDS if not os.path.exists(os.path.join(d, f"s{s}.png"))]
        print(f"[{cid}] {prompt(cid)}\n  후보 {len(jobs)}장 생성", flush=True)
        if jobs:
            run_scene.gen_zimage(jobs, d)
