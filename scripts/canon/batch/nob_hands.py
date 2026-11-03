#!/usr/bin/env python3
"""놉 t19 s9(손질본) — 세 사람의 손 자리만 같은 생성기(Z-Image img2img)로 키워 다시 그려 줄여 붙인다(task 567 · 사람 판정 562 「도엑 오른손이 안보여서 이상함」 ·
문항 t.hands-visible 0/3 「제사장의 한 손이 등 뒤로 · 다윗의 먼 쪽 손도 가려짐」). 갓 침 손질(.forge/scratch/gath_drool.py)과 같은 길 — 작은 부위만, 얼굴·머리는 원본.

    $VENV batch/nob_hands.py        → ~/.local/biblemap-imggen/nob-hands/parts · 사람마다 되붙인 판 samples/nob-hands/<who>-s<seed>-<세기>.png
    $VENV batch/nob_hands.py pick doeg=<key> priest=<key> david=<key>   → samples/nob-hands/composition-A-s9.png(세 자리를 함께 되붙임)
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import derive_scene as ds  # noqa: E402
import gen_face_detail as fd  # noqa: E402

BASE = os.path.join(HERE, "samples", "nob-step23-t19e", "composition-A-s9.png")
OUT = os.path.expanduser("~/.local/biblemap-imggen/nob-hands")
PASTE = os.path.join(HERE, "samples", "nob-hands")
FEATHER = 5
SEEDS, STRENGTHS = (42, 7), (0.6, 0.7)
# 자리(정사각 잘라 냄) · 되붙일 타원(손·허리만 — 얼굴·가리키는 손·뻗은 손 밖) · 문구
PARTS = {
    "doeg": {"region": (990, 300, 1150, 460), "mask": (998, 335, 1142, 440),
             "prompt": f"{ds.ST} close view of the torso of an ancient Edomite herdsman in a plain gray-brown wool tunic with a leather belt, "
                       "standing with both hands clasped together in front of his belly, both hands clearly visible."},
    "priest": {"region": (220, 300, 380, 460), "mask": (240, 345, 335, 450),
               "prompt": f"{ds.ST} close view of the torso of an ancient Israelite priest in a long deep blue mantle over a white linen robe, "
                         "his free hand hanging relaxed at his side in front of the mantle, the hand clearly visible."},
    "david": {"region": (700, 300, 860, 460), "mask": (742, 345, 850, 450),
              "prompt": f"{ds.ST} close view of the torso of a lean young man in a deep red wool tunic with a plain leather belt, "
                        "his free hand hanging relaxed at his side, the hand clearly visible."},
}


def gen():
    os.makedirs(os.path.join(OUT, "parts"), exist_ok=True)
    os.makedirs(PASTE, exist_ok=True)
    im = Image.open(BASE).convert("RGB")
    jobs = []
    for who, P in PARTS.items():
        src = os.path.join(OUT, f"src-{who}.png")
        im.crop(P["region"]).resize((fd.params.FACE_DETAIL_SIZE,) * 2, Image.LANCZOS).save(src)
        jobs += [{"key": f"{who}-s{sd}-{st}", "src": src, "region": P["region"], "prompt": P["prompt"], "ver": None, "who": who,
                  "seed": sd, "strength": st, "out": os.path.join(OUT, "parts", f"{who}-s{sd}-{st}.png")}
                 for st in STRENGTHS for sd in SEEDS]
    path = os.path.join(OUT, "jobs.json")
    json.dump(jobs, open(path, "w"), ensure_ascii=False, indent=1)
    if not all(os.path.exists(j["out"]) for j in jobs):
        for m in ("enc", "gen"):
            subprocess.run([sys.executable, fd.__file__, "worker-" + m, path], check=True)
    for j in jobs:
        paste(im, {j["who"]: j["key"]}).save(os.path.join(PASTE, f"{j['key']}.png"))
        print(f"[NobHands] {j['key']} 되붙임", flush=True)


def paste(im, picks):
    out = im.copy()
    for who, key in picks.items():
        P = PARTS[who]
        reg = P["region"]
        layer = out.copy()
        layer.paste(Image.open(os.path.join(OUT, "parts", f"{key}.png")).convert("RGB").resize((reg[2] - reg[0],) * 2, Image.LANCZOS), tuple(reg[:2]))
        hard = Image.new("L", im.size, 0)
        ImageDraw.Draw(hard).ellipse(P["mask"], fill=255)
        out = Image.composite(layer, out, hard.filter(ImageFilter.GaussianBlur(FEATHER)))
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "pick":
        picks = dict(a.split("=", 1) for a in sys.argv[2:])
        dst = os.path.join(PASTE, "composition-A-s9.png")
        paste(Image.open(BASE).convert("RGB"), picks).save(dst)
        print(f"[NobHands] {dst} ← {picks}")
    else:
        gen()
