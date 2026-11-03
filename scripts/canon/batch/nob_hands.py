#!/usr/bin/env python3
"""놉 t19 s9(손질본) — 세 사람의 손 자리만 같은 생성기(Z-Image img2img)로 키워 다시 그려 줄여 붙인다(task 567 · 사람 판정 562 「도엑 오른손이 안보여서 이상함」 ·
문항 t.hands-visible 0/3 「제사장의 한 손이 등 뒤로 · 다윗의 먼 쪽 손도 가려짐」). 갓 침 손질(.forge/scratch/gath_drool.py)과 같은 길 — 작은 부위만, 얼굴·머리는 원본.

    $VENV batch/nob_hands.py        → ~/.local/biblemap-imggen/nob-hands/parts · 사람마다 되붙인 판 samples/nob-hands/<who>-s<seed>-<세기>.png
    $VENV batch/nob_hands.py pick doeg=<key> priest=<key> david=<key>   → samples/nob-hands/composition-A-s9.png(세 자리를 함께 되붙임)
    $VENV batch/nob_hands.py r2   → 제사장·다윗 팔을 아래팔째(task 570 · 사람 567 짧은 팔) · samples/nob-hands2/<who>2-s<seed>-<세기>.png
    $VENV batch/nob_hands.py pick2 priest2=<key> david2=<key>   → samples/nob-hands2/composition-A-s9.png
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


# task 570 r2 — 사람 567 「손이 너무 짧잖아」: 자리를 아래팔까지 넓혀(어깨 아래 ~ 허벅지 중간) 팔 길이째 다시 그림 · 도엑은 r1 그대로
R2 = {
    "priest": {"region": (200, 270, 420, 490), "mask": (238, 300, 336, 478),
               "prompt": f"{ds.ST} view of an ancient Israelite priest in a long deep blue mantle over a white linen robe, "
                         "his free arm hanging straight down at his side in front of the mantle, the hand reaching down to the middle of his thigh, natural arm length."},
    # r3: 제사장 팔을 내리면 겉옷에 가려 손이 허리 높이(r2 6판 모두) → 굽힌 팔로 가슴께 겉옷 자락을 쥠(내린 팔 없음)
    "priest3": {"region": (200, 270, 420, 490), "mask": (238, 290, 336, 430),
                "prompt": f"{ds.ST} view of an ancient Israelite priest in a long deep blue mantle over a white linen robe, "
                          "his free hand raised to his chest, holding the edge of his blue mantle, the hand clearly visible."},
    "david": {"region": (680, 270, 900, 490), "mask": (786, 300, 862, 478),
              "prompt": f"{ds.ST} view of a lean young man in a deep red wool tunic with a plain leather belt, "
                        "his free arm hanging straight down at his side, the hand reaching down to the middle of his thigh, natural arm length."},
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
    if len(sys.argv) > 1 and sys.argv[1] == "r3":
        BASE = os.path.join(PASTE, "composition-A-s9.png")
        PARTS = {"priest32": R2["priest3"]}
        PASTE = os.path.join(HERE, "samples", "nob-hands2")
        STRENGTHS, SEEDS = (0.65, 0.75, 0.85, 0.9), (42, 7, 5)   # 0.65·0.75는 6판 모두 손이 허리 높이 그대로 → 0.85·0.9 더함
        gen()
    elif len(sys.argv) > 1 and sys.argv[1] == "r2":   # 바탕 = r1 되붙임본(도엑 손 포함) · 제사장·다윗 팔 길이째
        BASE = os.path.join(PASTE, "composition-A-s9.png")
        PARTS = {f"{k}2": v for k, v in R2.items() if k != "priest3"}
        PASTE = os.path.join(HERE, "samples", "nob-hands2")
        STRENGTHS, SEEDS = (0.65, 0.75), (42, 7, 5)
        gen()
    elif len(sys.argv) > 1 and sys.argv[1] == "pick2":
        PARTS = {f"{k}2": v for k, v in R2.items()}
        dst = os.path.join(HERE, "samples", "nob-hands2", "composition-A-s9.png")
        paste(Image.open(os.path.join(PASTE, "composition-A-s9.png")).convert("RGB"), dict(a.split("=", 1) for a in sys.argv[2:])).save(dst)
        print(f"[NobHands] {dst}")
    elif len(sys.argv) > 1 and sys.argv[1] == "pick":
        picks = dict(a.split("=", 1) for a in sys.argv[2:])
        dst = os.path.join(PASTE, "composition-A-s9.png")
        paste(Image.open(BASE).convert("RGB"), picks).save(dst)
        print(f"[NobHands] {dst} ← {picks}")
    else:
        gen()
