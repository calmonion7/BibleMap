"""task 696 — 크게 다시 그리기(사람 692 「근본적으로 해결할 방법 없나?」 → 「크게 다시 그리기」): 장면 그림에서 뿔은 60~100화소라 나무판·끈 마개가
몇 화소 → 생성기가 제 버릇(열린 아가리로 붓는 나팔 뿔)으로 돌아감. 붓는 손·뿔·받는 머리 자리를 잘라 3배로 키우고, 그 크기에서 정본 뿔을 붓는 각도로 얹은 뒤
같은 생성기(Z-Image + 기름 뿔 LoRA v2)로 그 자리만 i2i로 다시 그려 원래 크기로 줄여 되붙인다(얼굴은 되붙이지 않음 — 얼굴 정본 보존).
  python3 batch/horn_hires.py <이름> prep     # 3배 크롭 + 정본 얹기 + 기름 줄기 → samples/<out>/src.png
  $VENV  batch/horn_hires.py <이름> gen      # i2i(세기 × 시드) → samples/<out>/hi-<세기>-s<시드>.png
  python3 batch/horn_hires.py <이름> back     # 줄여 되붙임 → samples/<out>/back-<세기>-s<시드>.png"""
import math, os, sys
CANON = "/Users/calmonion/Project/BibleMap/scripts/canon"
sys.path.insert(0, CANON); sys.path.insert(0, os.path.join(CANON, "batch"))
from PIL import Image, ImageDraw, ImageFilter

K = 3
SCENES = {
    # 기혼 692 s42(기계 통과) — 크롭 (420,200)~(676,456) · 3배 자리에서 끝을 솔로몬 머리 위(545,450)에, 정본을 시계 방향 40° 돌림(끝이 아래로)
    "gihon692": {"base": "samples/gihon-step23-t23/composition-A-s42.png", "box": (420, 200, 676, 456), "out": "gihon-hires-696",
                 "tip": (545, 452), "chord": 230, "ang": -40, "oil_to": (548, 508), "keep": [(150, 190, 345, 425)],
                 "prompt": "warm cream paper, soft pencil and colored-pencil storybook illustration, gentle hand-drawn lines. close view: an old priest with a long gray beard and white linen turban, "
                           "his hands gripping oilhorn_bm, a ram's horn oil flask, glossy dark brown, no metal fittings, its wide end closed flat with a round wooden disc, "
                           "tilted with the small cut tip pointing down, a thin stream of golden oil pouring from the small cut tip onto the dark hair of a kneeling young man in a deep blue robe",
                 "strengths": (0.35, 0.45, 0.55), "seeds": (42, 7), "lora": 1.0},
}
# 690 s202 — 옛 뿔이 이미 붓는 방향(넓은 쪽 위 · 가는 끝 아래, 두 손으로 쥠)이라 정본으로 덮임(692 s42는 옛 뿔이 정본 밖으로 남음 — 1판 src 두 뿔).
# 끝을 솔로몬 머리 꼭대기 위로(옛 끝은 목덜미 위) · 두 손(살빛 화소)은 정본 위로 되살림(사람 685·686 「손으로 쥐고 있지 않음」).
SCENES["gihon690"] = {**SCENES["gihon692"], "base": "samples/gihon-step23-t21/composition-A-s202.png", "box": (440, 190, 696, 446), "out": "gihon-hires-696b",
                      "mouth": (392, 258), "tip": (556, 470), "oil_to": (557, 556), "hands": [(330, 320, 415, 405), (395, 365, 475, 435)],
                      "keep": [(110, 190, 300, 430), (370, 560, 540, 768)]}


def prep(c):
    import horn_compose as H
    out = os.path.join(CANON, "samples", c["out"]); os.makedirs(out, exist_ok=True)
    x0, y0, x1, y1 = c["box"]
    big = Image.open(os.path.join(CANON, c["base"])).convert("RGB").crop(c["box"]).resize(((x1 - x0) * K, (y1 - y0) * K), Image.LANCZOS)
    big.save(os.path.join(out, "crop.png"))
    cut = H.canon_cut(); bb = cut.getbbox(); cut = cut.crop(bb)
    mouth = (H.CANON_MOUTH[0] - bb[0], H.CANON_MOUTH[1] - bb[1]); tip = (H.CANON_TIP[0] - bb[0], H.CANON_TIP[1] - bb[1])
    if c.get("mouth"):   # 밑동·끝 두 자리로 크기·돌림을 셈
        c = {**c, "chord": math.dist(c["mouth"], c["tip"]),
             "ang": math.degrees(math.atan2(tip[1] - mouth[1], tip[0] - mouth[0]) - math.atan2(c["tip"][1] - c["mouth"][1], c["tip"][0] - c["mouth"][0]))}
    k = c["chord"] / math.dist(mouth, tip)
    h = cut.resize((round(cut.width * k), round(cut.height * k)), Image.LANCZOS)
    tx, ty = tip[0] * k - h.width / 2, tip[1] * k - h.height / 2
    h = h.rotate(c["ang"], expand=True, resample=Image.BICUBIC)   # 돌리기만(거울 없음 — 사람 674)
    a = math.radians(c["ang"])
    tx, ty = tx * math.cos(a) + ty * math.sin(a) + h.width / 2, -tx * math.sin(a) + ty * math.cos(a) + h.height / 2
    ox, oy = round(c["tip"][0] - tx), round(c["tip"][1] - ty)
    src = big.convert("RGBA"); src.alpha_composite(h, (ox, oy)); src = src.convert("RGB")
    for b in c.get("hands", []):   # 쥔 손 살빛을 정본 위로(주먹 속을 지나는 꼴)
        import numpy as np
        o = np.asarray(big.crop(b)).astype(int); r, g, bl = o[..., 0], o[..., 1], o[..., 2]
        skin = (r > 140) & (r > g) & (g > bl) & (r - bl > 35) & (r - bl < 120) & (g > 90)
        src.paste(big.crop(b), b[:2], Image.fromarray((skin * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(1)))
    d = ImageDraw.Draw(src)
    (sx, sy), (ex, ey) = c["tip"], c["oil_to"]
    d.line([(sx, sy + 3), (ex, ey)], fill=(232, 178, 34), width=9)
    d.line([(sx - 1, sy + 5), (ex - 1, ey - 4)], fill=(255, 236, 150), width=3)
    src.save(os.path.join(out, "src.png"))
    # 되붙일 자리 = 얹은 정본 + 쥔 손 + 기름 줄기(넓혀서) — 상자 전체를 되붙이면 i2i가 바꾼 배경(판자·밧줄 고리)까지 들어옴(696 1판)
    m = Image.new("L", big.size, 0)
    m.paste(h.getchannel("A").point(lambda v: 255 if v > 40 else 0), (ox, oy))
    md = ImageDraw.Draw(m)
    for b in c.get("hands", []):
        md.rectangle(b, fill=255)
    md.line([(sx, sy), (ex, ey + 6)], fill=255, width=16)
    m.filter(ImageFilter.MaxFilter(21)).save(os.path.join(out, "mask.png"))
    print("[HornHires] 준비", os.path.join(out, "src.png"), "· 정본 왼쪽 위", (ox, oy), "크기", h.size)


def gen(c):
    import run_scene
    out = os.path.join(CANON, "samples", c["out"])
    W, Hh = Image.open(os.path.join(out, "src.png")).size
    jobs = [{"prompt": c["prompt"], "seed": s, "w": W, "h": Hh, "src": os.path.join(out, "src.png"), "strength": st,
             "out": os.path.join(out, f"hi-{st}-s{s}.png"), "loras": [["oil-horn-v2", c["lora"]]]}
            for st in c["strengths"] for s in c["seeds"] if not os.path.exists(os.path.join(out, f"hi-{st}-s{s}.png"))]
    tmp = os.path.expanduser(f"~/.local/biblemap-imggen/{c['out']}"); os.makedirs(tmp, exist_ok=True)
    if jobs:
        print("[HornHires] i2i", len(jobs), "장", run_scene.gen_zimage(jobs, tmp, "i2i"))


def back(c):
    out = os.path.join(CANON, "samples", c["out"])
    base = Image.open(os.path.join(CANON, c["base"])).convert("RGB")
    x0, y0, x1, y1 = c["box"]; w, h = (x1 - x0) * K, (y1 - y0) * K
    mp = os.path.join(out, "mask.png")
    m = Image.open(mp).convert("L") if os.path.exists(mp) else Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    if not os.path.exists(mp):
        d.rounded_rectangle([40, 40, w - 40, h - 40], radius=60, fill=255)   # 둘레는 원본 그대로(흐린 경계)
    for b in c["keep"]:
        d.rectangle(b, fill=0)                                        # 얼굴 자리는 원본(얼굴 정본 보존)
    m = m.filter(ImageFilter.GaussianBlur(14))
    for f in sorted(os.listdir(out)):
        if f.startswith("hi-"):
            hi = Image.open(os.path.join(out, f)).convert("RGB")
            crop = Image.open(os.path.join(out, "crop.png")).convert("RGB")
            mixed = Image.composite(hi, crop, m).resize((x1 - x0, y1 - y0), Image.LANCZOS)
            res = base.copy(); res.paste(mixed, (x0, y0))
            res.save(os.path.join(out, "back-" + f[3:]))
            print("[HornHires]", os.path.join(out, "back-" + f[3:]))


if __name__ == "__main__":
    {"prep": prep, "gen": gen, "back": back}[sys.argv[2]](SCENES[sys.argv[1]])
