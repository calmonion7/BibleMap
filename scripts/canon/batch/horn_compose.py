"""task 645 — 뿔을 직접 칠해 얹은 뒤 같은 생성기(Z-Image img2img)로 그림 전체를 가볍게 다시 그림.
뿔만 따로 생성하거나 문구·가이드로 방향을 주면 생성기가 넓은 입으로 붓는 꼴로 되돌림(베들레헴 639·641·644 · 기혼 640·642) —
꼴은 손으로 정하고 화풍은 생성기가 입힌다. 세기 0.35 이상은 생성기가 뿔을 넓은 입 쪽으로 다시 뒤집음(task 645).
task 646 — 장면별 설정 · 짧고 굵은 원뿔꼴(사람 645 「기름뿔 모양 이상함」 — 길고 가는 뿔은 상아·낫처럼 보임).
task 663 — `"canon": True`면 칠하지 않고 지물 정본을 오려 얹음(paste_canon).
쓰기: venv314 python horn_compose.py <scene> compose  → samples/<out>/src.png
      venv314 python horn_compose.py <scene> redraw   → samples/<out>/out-<strength>.png"""
import os, sys
from PIL import Image, ImageDraw

CANON = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENES = {
    # base: 출발 그림 · fixed: 장면 문구를 읽을 고정 절 · seed · erase: 지울 옛 뿔·잔·기름 다각형들 · horn: (밑동, 굽음, 끝) · r: 밑동 반지름 · oil: 끝에서 머리까지
    "bethlehem": {"base": "samples/bethlehem-step23-t9/composition-A-s202.png", "out": "bethlehem-horn-i2i", "fixed": 639, "seed": 202,
                  "erase": [[(436, 318), (434, 300), (468, 254), (484, 246), (500, 248), (514, 258), (514, 300), (500, 306), (470, 300), (450, 330)]],
                  "horn": ((443, 318), (477, 260), (502, 286)), "r": 9, "oil": ((503, 289), (505, 300)), "strengths": (0.2, 0.28, 0.35)},
    "gihon": {"base": "samples/gihon-step23-t15/composition-A-s101.png", "out": "gihon-horn-i2i", "fixed": 642, "seed": 101,
              "erase": [[(516, 352), (522, 330), (540, 304), (558, 296), (586, 298), (594, 322), (582, 372), (570, 374), (540, 350)],
                        [(530, 368), (558, 366), (558, 404), (532, 406)]],   # 옛 뿔·기름 줄기 · 왼손의 잔(붓는 그릇이 둘)
              "horn": ((523, 374), (552, 326), (579, 361)), "r": 12, "oil": ((580, 364), (583, 377)), "oil_w": 5, "strengths": (0.2,)},   # task 646 b: 밑동을 두 손 사이(손이 비면 잔을 다시 쥐여 줌) · 기름 굵게(가는 줄은 흰 줄·검은 선으로 읽힘)
    # task 647 — 사람 결정 「1」: 사독이 두 손으로 뿔 하나만 쥔 장(642 s7)에서 출발 · 나단 주머니(붓는 이 하나 문항)도 지움
    "gihon7": {"base": "samples/gihon-step23-t17/composition-A-s7.png", "out": "gihon-horn-i2i-s7", "fixed": 642, "seed": 7,
               "erase": [[(522, 318), (560, 308), (590, 290), (612, 294), (616, 336), (608, 366), (596, 366), (588, 336), (540, 345), (522, 345)],
                         [(188, 408), (222, 408), (222, 446), (188, 446)], [(184, 384), (196, 384), (201, 410), (189, 410)]],
               "horn": ((514, 337), (546, 306), (563, 327)), "r": 12, "oil": ((564, 330), (566, 343)), "oil_w": 5, "strengths": (0.2, 0.25)},
    # task 663 — 칠하지 않고 지물 정본(frozen/props/oil-horn.png)을 오려 얹음(사람 649 「사물을 먼저 따로그리고 비교도구로」) · 자리는 gihon과 같음
    "gihon-canon": {"base": "samples/gihon-step23-t15/composition-A-s101.png", "out": "gihon-horn-canon", "fixed": 642, "seed": 101, "canon": True,
                    "erase": [[(516, 352), (522, 330), (540, 304), (558, 296), (586, 298), (594, 322), (582, 372), (570, 374), (540, 350)]],
                    # 아래 주먹이 쥔 둘째 흰 뿔(사람 616 「뿔이 두개임」) — 번지게 메우면 생성기가 잔으로 다시 그림(646·663 1판) → 옆 모래 바탕 조각을 옮겨 붙임
                    "patch": [((538, 371, 563, 396), (585, 330))],
                    # 문구 「holding in both hands」면 빈 아래 주먹에 물건(두루마리·잔)을 다시 그림(663 2판) → 다시 그리기 문구만 한 손 · 사전 지금 L2 꼴
                    "prompt_sub": [("holding in both hands a curved, ridged and streaked ram's horn shorter than a man's forearm, its wide end sealed with a wooden plug, "
                                    "tapering to a narrow tip with a small spout, filled with oil,",
                                    "holding up in his right hand a thick, gently curved natural ram's horn, glossy dark brown with pale amber streaks, its wide end closed, "
                                    "narrowing to a blunt tip with a small spout, filled with oil, his left hand hanging open and empty at his side,")],
                    # 칠할 때 자리(밑동 374 · 끝 361)는 끝이 밑동보다 높아 기름이 끝으로 못 나옴 → 밑동을 위쪽 손 높이로(끝과 같은 높이 · 굽어 끝이 아래로)
                    "horn": ((519, 352), (548, 320), (577, 353)), "r": 12, "oil": ((574, 354), (579, 369)), "oil_w": 4, "strengths": (0.2,)},
}
CANON_HORN = "frozen/props/oil-horn.png"
CANON_MOUTH, CANON_TIP = (352, 234), (968, 238)   # 정본 1216×640에서 입구(마개) 가운데 · 잘린 끝 주둥이


def canon_cut():
    """정본 뿔을 종이에서 오려 낸 RGBA(Vision 전경 마스크 · 아래 그림자는 옅고 빛깔 없는 화소로 지움) — samples/prop-oil-horn-lying/canon-cut.png에 둠."""
    import subprocess
    import numpy as np
    out = os.path.join(CANON, "samples", "prop-oil-horn-lying", "canon-cut.png")
    if not os.path.exists(out):
        vision = os.path.expanduser("~/.local/biblemap-manimgx/.venv/bin/python")
        subprocess.run([vision, os.path.join(CANON, "batch", "fg_mask.py"), os.path.join(CANON, CANON_HORN), out], check=True, capture_output=True)
        a = np.asarray(Image.open(out).convert("RGBA")).copy()
        rgb = a[:, :, :3].astype(int)
        lum, sat = rgb.mean(2), rgb.max(2) - rgb.min(2)
        yy = np.arange(a.shape[0])[:, None]
        a[(yy > 380) & (lum > 110) & (sat < 60), 3] = 0
        Image.fromarray(a).save(out)
    return Image.open(out).convert("RGBA")


def paste_canon(im, cfg):
    """정본 뿔을 밑동(입구) → cfg horn[0], 끝 → horn[2]에 맞춰 줄이고 돌려 얹음. 정본은 아래로 처진 꼴이라 굽은 쪽이 horn[1](굽음 점) 쪽을 향하게 뒤집음."""
    import cv2
    import numpy as np
    base, ctrl, tip = cfg["horn"]
    cut = canon_cut()
    v = (CANON_TIP[0] - CANON_MOUTH[0], CANON_TIP[1] - CANON_MOUTH[1])
    u = (tip[0] - base[0], tip[1] - base[1])
    k = (u[0] ** 2 + u[1] ** 2) ** 0.5 / (v[0] ** 2 + v[1] ** 2) ** 0.5
    small = cut.resize((round(cut.width * k), round(cut.height * k)), Image.LANCZOS)
    m = (CANON_MOUTH[0] * k, CANON_MOUTH[1] * k)
    sag = (m[0] - v[1] * k, m[1] + v[0] * k)                      # 정본의 처진 쪽(아래)
    side = 1 if (ctrl[0] - base[0]) * u[1] - (ctrl[1] - base[1]) * u[0] < 0 else -1
    arch = (base[0] - side * u[1], base[1] + side * u[0])          # 장면의 굽음 점 쪽
    M = cv2.getAffineTransform(np.float32([m, (m[0] + v[0] * k, m[1] + v[1] * k), sag]), np.float32([base, tip, arch]))
    layer = cv2.warpAffine(np.asarray(small), M, im.size, flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    out = im.convert("RGBA")
    out.alpha_composite(Image.fromarray(layer))
    return out.convert("RGB")


def bez(p0, c, p1, n=24):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]) for t in (i / n for i in range(n + 1))]


def compose(cfg):
    import cv2
    import numpy as np
    out = os.path.join(CANON, "samples", cfg["out"])
    os.makedirs(out, exist_ok=True)
    im = Image.open(os.path.join(CANON, cfg["base"])).convert("RGB")
    mask = Image.new("L", im.size, 0)
    md = ImageDraw.Draw(mask)
    for poly in cfg["erase"]:
        md.polygon(poly, fill=255)
    a = cv2.inpaint(np.array(im)[:, :, ::-1], np.array(mask), 7, cv2.INPAINT_TELEA)   # 둘레 화소로 메움(평평한 색 덮개는 뒤 사람 위에 덩어리)
    im = Image.fromarray(a[:, :, ::-1])
    src0 = Image.open(os.path.join(CANON, cfg["base"])).convert("RGB")
    for (x0, y0, x1, y1), (sx, sy) in cfg.get("patch", []):   # 바탕 조각 옮겨 붙이기(원본에서)
        im.paste(src0.crop((sx, sy, sx + x1 - x0, sy + y1 - y0)), (x0, y0))
    if cfg.get("canon"):
        im = paste_canon(im, cfg)
        d = ImageDraw.Draw(im)
        (tx, ty), (ox, oy) = cfg["oil"]
        d.line([(tx, ty), (ox, oy)], fill=(214, 168, 40), width=cfg.get("oil_w", 3))   # 끝 주둥이에서 머리로 떨어지는 금빛 기름
        im.save(os.path.join(out, "src.png"))
        print("[HornCompose]", os.path.join(out, "src.png"))
        return
    d = ImageDraw.Draw(im)
    pts = bez(*cfg["horn"])   # 밑동(손 안) → 조금 휘어 → 뾰족한 끝(머리 위, 아래를 향함)
    n, r0 = len(pts) - 1, cfg["r"]
    for i, (x, y) in enumerate(pts):                  # 바깥 선(짙은 뼈빛) 먼저
        r = r0 * (1 - i / n) ** 0.8 + 1.2             # 밑동이 넓은 원뿔꼴(0.8제곱 — 끝 가까이에서 빨리 가늘어짐)
        d.ellipse([x - r - 1.2, y - r - 1.2, x + r + 1.2, y + r + 1.2], fill=(150, 125, 85))
    for i, (x, y) in enumerate(pts):                  # 몸통(옅은 뼈빛)
        r = r0 * (1 - i / n) ** 0.8 + 1.2
        d.ellipse([x - r, y - r, x + r, y + r], fill=(232, 218, 182))
    (tx, ty), (ox, oy) = cfg["oil"]
    d.ellipse([tx - 2.5, ty - 4.5, tx + 2.5, ty + 0.5], fill=(90, 70, 45))   # 열린 뾰족한 끝
    d.line([(tx, ty), (ox, oy)], fill=(214, 168, 40), width=cfg.get("oil_w", 3))   # 끝에서 머리로 떨어지는 금빛 기름
    im.save(os.path.join(out, "src.png"))
    print("[HornCompose]", os.path.join(out, "src.png"))


def redraw(cfg):
    sys.path.insert(0, os.path.join(CANON, "batch"))
    sys.path.insert(0, CANON)
    os.chdir(CANON)
    import rule_ab as R
    import run_scene
    R.use(cfg["fixed"])
    pa, _ = R.prompts(R.FX["cases"][0])
    for a, b in cfg.get("prompt_sub", []):
        assert a in pa, a[:40]
        pa = pa.replace(a, b)
    out = os.path.join(CANON, "samples", cfg["out"])
    jobs = [{"prompt": pa, "seed": cfg["seed"], "w": 1216, "h": 640, "src": os.path.join(out, "src.png"), "strength": s,
             "out": os.path.join(out, f"out-{s}.png")} for s in cfg["strengths"]]
    tmp = os.path.expanduser(f"~/.local/biblemap-imggen/{cfg['out']}")
    os.makedirs(tmp, exist_ok=True)
    print("[HornCompose] i2i", run_scene.gen_zimage(jobs, tmp, "i2i"))


def repaste(cfg, strength=0.12):
    """task 663 — i2i 0.2가 작은 천 마개를 어두운 열린 입으로 바꿈(t.horn-canon 「밑동이 열려 보임」) → 다시 그린 그림 위에 정본을 한 번 더 얹고 아주 약하게 다듬음."""
    sys.path.insert(0, os.path.join(CANON, "batch")); sys.path.insert(0, CANON); os.chdir(CANON)
    import rule_ab as R
    import run_scene
    out = os.path.join(CANON, "samples", cfg["out"])
    first = cfg["strengths"][0]
    im = paste_canon(Image.open(os.path.join(out, f"out-{first}.png")).convert("RGB"), cfg)
    im.save(os.path.join(out, f"src2-{first}.png"))
    R.use(cfg["fixed"])
    pa, _ = R.prompts(R.FX["cases"][0])
    for a, b in cfg.get("prompt_sub", []):
        pa = pa.replace(a, b)
    jobs = [{"prompt": pa, "seed": cfg["seed"], "w": 1216, "h": 640, "src": os.path.join(out, f"src2-{first}.png"), "strength": strength,
             "out": os.path.join(out, f"out2-{first}-{strength}.png")}]
    tmp = os.path.expanduser(f"~/.local/biblemap-imggen/{cfg['out']}")
    os.makedirs(tmp, exist_ok=True)
    print("[HornCompose] 다시 얹기 i2i", run_scene.gen_zimage(jobs, tmp, "i2i"))


def local(cfg, box=(470, 270, 650, 430)):
    """task 663 — 그림 전체 i2i가 멀리 있는 시위대 팔을 바꿈(t.arm-length·t.hands-clear-guards 새로 걸림) → 다시 그린 뿔 둘레(box, 흐린 경계)만 원본에 되붙임."""
    from PIL import ImageFilter
    out = os.path.join(CANON, "samples", cfg["out"])
    first = cfg["strengths"][0]
    base = Image.open(os.path.join(CANON, cfg["base"])).convert("RGB")
    new = Image.open(os.path.join(out, f"src2-{first}.png")).convert("RGB")
    m = Image.new("L", base.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([box[0] + 12, box[1] + 12, box[2] - 12, box[3] - 12], radius=20, fill=255)
    Image.composite(new, base, m.filter(ImageFilter.GaussianBlur(10))).save(os.path.join(out, f"local-{first}.png"))
    print("[HornCompose]", os.path.join(out, f"local-{first}.png"))


if __name__ == "__main__":
    {"compose": compose, "redraw": redraw, "repaste": repaste, "local": local}[sys.argv[2]](SCENES[sys.argv[1]])
