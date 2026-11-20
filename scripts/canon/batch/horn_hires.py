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


def prep_recolor(c):
    """task 699 — 정본이 없는 지물(양각): 생성기가 금속 나팔로 그린 금빛 화소를 짐승 뿔 빛깔(갈색·황갈색, 밝기 결 유지)로 바꾼 바탕 → i2i로 그 자리만 다시 그림."""
    import numpy as np
    out = os.path.join(CANON, "samples", c["out"]); os.makedirs(out, exist_ok=True)
    x0, y0, x1, y1 = c["box"]
    big = Image.open(os.path.join(CANON, c["base"])).convert("RGB").crop(c["box"]).resize(((x1 - x0) * K, (y1 - y0) * K), Image.LANCZOS)
    big.save(os.path.join(out, "crop.png"))
    a = np.asarray(big).astype(float); sel = np.zeros(a.shape[:2], bool)
    for bx0, by0, bx1, by1 in c["recolor"]:
        r, g, b = a[by0:by1, bx0:bx1, 0], a[by0:by1, bx0:bx1, 1], a[by0:by1, bx0:bx1, 2]
        sel[by0:by1, bx0:bx1] = (r > 120) & (g > 80) & (r - b > 85) & (g - b > 40)   # 금빛·황동(모래 비탈은 r-b 약 60이라 빠짐)
    lum = a.mean(2)
    horn = np.stack([lum * 0.62 + 30, lum * 0.48 + 22, lum * 0.34 + 14], 2)   # 짙은 갈색~옅은 황갈색(밝기 결 그대로)
    a[sel] = horn[sel]
    src = Image.fromarray(a.clip(0, 255).astype("uint8")); src.save(os.path.join(out, "src.png"))
    m = Image.fromarray((sel * 255).astype("uint8")).filter(ImageFilter.MaxFilter(15))
    m.save(os.path.join(out, "mask-obj.png")); Image.new("L", big.size, 0).save(os.path.join(out, "mask-erase.png")); m.save(os.path.join(out, "mask.png"))
    print("[HornHires] 색 바꾼 바탕", os.path.join(out, "src.png"), int(sel.sum()), "화소")


def prep(c):
    if c.get("recolor"):
        return prep_recolor(c)
    import horn_compose as H
    out = os.path.join(CANON, "samples", c["out"]); os.makedirs(out, exist_ok=True)
    x0, y0, x1, y1 = c["box"]
    big = Image.open(os.path.join(CANON, c["base"])).convert("RGB").crop(c["box"]).resize(((x1 - x0) * K, (y1 - y0) * K), Image.LANCZOS)
    big.save(os.path.join(out, "crop.png"))
    erase = Image.new("L", big.size, 0)
    if c.get("erase"):   # 드러날 옛 지물·기름을 지움 — 상자마다 차례로, 결을 가져올 방향(shift)이 있으면 옆 바탕을 옮겨 메움
        import cv2, numpy as np
        em = np.zeros((big.height, big.width), "uint8")
        for e in c["erase"]:
            x0e, y0e, x1e, y1e, kind = e[:5]
            a = np.asarray(big).astype(int)
            r, g, b = a[y0e:y1e, x0e:x1e, 0], a[y0e:y1e, x0e:x1e, 1], a[y0e:y1e, x0e:x1e, 2]
            sel = {"dark": (r < 150) & (r + g + b < 380), "oil": (r > 170) & (g > 120) & (r - b > 70),
                   "gold": (r > 140) & (g > 95) & (r - b > 60) & (g - b > 30),   # 699 — 금빛 나팔 꼴 옛 기름 뿔
                   "brown": (r - b > 45) & (r + g + b < 560)}[kind]   # brown — 옛 뿔 굽이·관 끝 테의 옅은 갈색(697 1판 남음)
            one = np.zeros_like(em); one[y0e:y1e, x0e:x1e] = (sel * 255).astype("uint8")
            one = cv2.dilate(one, np.ones((9, 9), "uint8"))
            if len(e) > 5:   # 698 — 매끈히 메운 칸은 i2i가 옅은 판으로 그림 → 옆 바탕 결(산비탈 줄무늬)을 옮겨 메움
                dx, dy = e[5]
                moved = big.transform(big.size, Image.AFFINE, (1, 0, dx, 0, 1, dy))
                big = Image.composite(moved, big, Image.fromarray(one))
                rim = cv2.dilate(one, np.ones((5, 5), "uint8")) - cv2.erode(one, np.ones((5, 5), "uint8"))
                big = Image.fromarray(cv2.inpaint(np.asarray(big), rim, 3, cv2.INPAINT_TELEA))
            else:
                big = Image.fromarray(cv2.inpaint(np.asarray(big), one, 7, cv2.INPAINT_TELEA))
            em |= one
        erase = Image.fromarray(em)
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
    orig = Image.open(os.path.join(out, "crop.png")).convert("RGB")
    for b in c.get("hands", []):   # 쥔 손을 정본 위로(주먹 속을 지나는 꼴) — 지우기 전 원본 손에서, 살빛 + 맞닿은 윤곽선까지(698: 지운 뒤 손에서 가져오면 손가락 윤곽이 빠져 「손 뭉개짐」)
        import numpy as np
        o = np.asarray(orig.crop(b)).astype(int); r, g, bl = o[..., 0], o[..., 1], o[..., 2]
        skin = ((r > 140) & (r > g) & (g > bl) & (r - bl > 35) & (r - bl < 120) & (g > 90)).astype("uint8") * 255
        if c.get("hand_outline"):
            skin = np.asarray(Image.fromarray(skin).filter(ImageFilter.MaxFilter(c["hand_outline"])))
        src.paste(orig.crop(b), b[:2], Image.fromarray(skin).filter(ImageFilter.GaussianBlur(1)))
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
    m.filter(ImageFilter.MaxFilter(9)).save(os.path.join(out, "mask-obj.png"))   # 698 — 지물·손·기름만(다시 그린 그림에서)
    erase.save(os.path.join(out, "mask-erase.png"))                                 # 지운 배경(결 옮겨 메운 src에서 — i2i는 결을 매끈히 지움)
    m.paste(255, (0, 0), erase)
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
            if os.path.exists(os.path.join(out, "mask-obj.png")):   # 세 겹: 원본 ← 지운 배경은 src ← 지물·손·기름은 다시 그린 그림
                src = Image.open(os.path.join(out, "src.png")).convert("RGB")
                me = Image.open(os.path.join(out, "mask-erase.png")).convert("L").filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(3))
                mo = Image.open(os.path.join(out, "mask-obj.png")).convert("L")
                for b in c["keep"]:
                    ImageDraw.Draw(mo).rectangle(b, fill=0)
                mixed = Image.composite(hi, Image.composite(src, crop, me), mo.filter(ImageFilter.GaussianBlur(5)))
                mixed = mixed.resize((x1 - x0, y1 - y0), Image.LANCZOS)
            else:
                mixed = Image.composite(hi, crop, m).resize((x1 - x0, y1 - y0), Image.LANCZOS)
            res = base.copy(); res.paste(mixed, (x0, y0))
            res.save(os.path.join(out, "back-" + f[3:]))
            print("[HornHires]", os.path.join(out, "back-" + f[3:]))

# task 697 — 사람 696 「s1 · 기름이 떨어지는 위치만 맞추면됨 머리위로 떨어지게」: 끝을 솔로몬 머리 꼭대기 위(468,468)로 — 몸통은 두 손 사이를 지나게 밑동을 왼쪽 위로.
# 옮기면 드러나는 옛 뿔 끝(짙은 갈색)·옛 기름 줄기(금빛)는 먼저 지움(erase — cv2.inpaint, 되붙일 자리에도 넣음).
SCENES["gihon690b"] = {**SCENES["gihon690"], "out": "gihon-hires-697", "mouth": (338, 285), "tip": (468, 468), "oil_to": (470, 508),
                       "erase": [(330, 235, 600, 500, "dark"), (345, 240, 445, 305, "brown"), (535, 455, 580, 575, "oil")], "strengths": (0.45, 0.55, 0.65), "seeds": (42, 7)}

# 697 2판 — 1판(밑동 338,285 → 끝 468,468 · 0.65-s42)은 기름이 머리 꼭대기에 떨어지나 뿔이 거의 서서 나무판이 비스듬히 「열린 입」으로 판정(t.horn-canon 2/3 틀림)·사독 손 뭉개짐 →
# 덜 세워 끝을 머리 꼭대기 뒤쪽 위(490,468)로 · 몸통은 두 손 사이.
SCENES["gihon690c"] = {**SCENES["gihon690b"], "out": "gihon-hires-697b", "mouth": (348, 288), "tip": (490, 468), "oil_to": (492, 512),
                       "strengths": (0.55, 0.65), "seeds": (42, 7, 11)}

# task 698 — 사람 697 「여전히 기름 떨어지는 위치가 안맞음」: 690 s202는 두 손 바로 아래에 머리가 있어 끝을 정수리 위에 둘 틈이 없음(끝을 옮기면 뿔이 서서 「열린 입」).
# 바탕을 690 s5로 — 두 손으로 든 뿔에서 기름이 정수리에 떨어지고 손~머리 틈이 넉넉함(옛 뿔은 넓은 관 꼴이라 정본으로 바꿈 · 옛 관 끝·옛 기름은 erase).
SCENES["gihon690s5"] = {**SCENES["gihon690"], "base": "samples/gihon-step23-t21/composition-A-s5.png", "box": (420, 180, 676, 436), "out": "gihon-hires-698",
                        "mouth": (410, 360), "tip": (545, 505), "oil_to": (550, 556), "hands": [(380, 400, 445, 470), (440, 420, 505, 480)],
                        "erase": [(380, 330, 620, 470, "dark", (0, -120)), (520, 350, 605, 430, "brown", (0, -120)), (500, 440, 580, 548, "oil", (90, 0)), (505, 545, 595, 585, "oil", (0, 24))],
                        "keep": [(230, 270, 370, 500), (470, 590, 650, 768)], "strengths": (0.55, 0.65), "seeds": (42, 7, 11)}

SCENES["gihon690s5b"] = {**SCENES["gihon690s5"], "out": "gihon-hires-698b", "hand_outline": 5, "strengths": (0.45, 0.55), "seeds": (42, 11)}   # 698 2판 — 원본 손(윤곽 포함) · 낮은 세기

# task 699 — 1:39 전체 구도 s7(기름이 머리에 · 백성 만세 · 시위대 끝 한 사람이 붊)에서 두 뿔을 고침: ① 기름 뿔(금빛 나팔 꼴·넓은 입으로 부음) → 정본 ② 양각(금속 나팔) → 짐승 뿔.
SCENES["gihon699oil"] = {**SCENES["gihon690s5b"], "base": "samples/gihon-step23-t24/composition-A-s7.png", "box": (400, 180, 656, 436), "out": "gihon-hires-699oil",
                         "mouth": (330, 330), "tip": (548, 468), "oil_to": (550, 528), "hands": [(290, 360, 385, 455), (385, 420, 470, 475)],
                         "erase": [(240, 270, 590, 470, "dark", (0, -150)), (240, 270, 590, 470, "gold", (0, -150)), (520, 440, 590, 512, "oil", (90, 0)), (520, 512, 590, 545, "oil", (0, 22))],
                         "keep": [(60, 230, 235, 470), (480, 560, 640, 700)], "strengths": (0.45, 0.55), "seeds": (42, 11)}
SCENES["gihon699sh"] = {**SCENES["gihon692"], "base": "samples/gihon-hires-699oil/pick.png", "box": (1040, 120, 1216, 376), "out": "gihon-hires-699sh",
                        "recolor": [(140, 250, 380, 480)], "keep": [],
                        "prompt": "warm cream paper, soft pencil and colored-pencil storybook illustration, gentle hand-drawn lines. a bearded soldier in a short wool tunic blowing a long curved natural ram's horn shofar raised to his lips, "
                                  "the horn mottled brown and pale tan with fine ridges, an animal horn, not metal, other soldiers standing beside him",
                        "strengths": (0.5, 0.6), "seeds": (42, 7), "lora": 0.0}


if __name__ == "__main__":
    {"prep": prep, "gen": gen, "back": back}[sys.argv[2]](SCENES[sys.argv[1]])
