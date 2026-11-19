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
    # task 664 — 사람 663 「둘다(두 손) 해야하는데 구멍 뚫린쪽으로 기름이 떨어져야함」: 두 손으로 쥔 642 s7에서 · 밑동을 두 손 안에 · 끝 구멍을 칠해 보이게
    "gihon7-canon": {"base": "samples/gihon-step23-t17/composition-A-s7.png", "out": "gihon7-horn-canon", "fixed": 642, "seed": 7, "canon": True,
                     "erase": [[(522, 318), (560, 308), (590, 290), (612, 294), (616, 336), (608, 366), (596, 366), (588, 336), (540, 345), (522, 345)],
                               [(188, 408), (222, 408), (222, 446), (188, 446)], [(184, 384), (196, 384), (201, 410), (189, 410)]],
                     "horn": ((505, 343), (538, 302), (567, 334)), "r": 12, "hole": True, "oil": ((567, 335), (569, 343)), "oil_w": 3,
                     # 옛 금빛 나팔 입(540~608, 297~340) 자리를 번지게 메우면 다시 그릴 때 나팔 입이 되살아남(664 1·2판) → 위 모래 바탕 조각으로 덮음(머리 위 336부터는 메움 그대로)
                     "patch": [((552, 290, 614, 335), (640, 292))],   # 위쪽 조각은 언덕 능선이 딸려 와 회색 줄(664 3판) → 오른쪽 모래
                     "front": (494, 332, 526, 356),   # 뿔을 위에서 감싼 손가락(원본) — 밑동을 얹으면 덮여 손이 하나만 보임(664 4판) → 살빛 화소를 뿔 앞에 다시 얹음
                     "local_box": (470, 270, 640, 420), "strengths": (0.2,),   # 나단 병 자리도 되붙이면 지운 얼룩이 i2i 0.2에 안 메워져 번진 채 남음(664 7판) → 나단은 원본(병 남음)
                     "prompt_sub": [("a curved, ridged and streaked ram's horn shorter than a man's forearm, its wide end sealed with a wooden plug, "
                                     "tapering to a narrow tip with a small spout, filled with oil,",
                                     "a thick, gently curved natural ram's horn, glossy dark brown with pale amber streaks, its wide end closed, "
                                     "narrowing to a blunt tip with a small spout, filled with oil,")]},
    # task 665 — 새 구도(두 손 어깨 높이 pour_high) 665 s42에서: 두 손 사이 밑동 → 머리 위 끝(틈 약 26화소)
    "gihon18-canon": {"base": "samples/gihon-step23-t18/composition-A-s42.png", "out": "gihon18-horn-canon", "fixed": 665, "seed": 42, "canon": True,
                      "erase": [[(586, 342), (598, 342), (598, 354), (588, 354)]],   # 옛 기름 줄기(머리카락 위 356 전까지)
                      "patch": [((534, 266, 580, 308), (640, 250)), ((572, 292, 614, 346), (620, 292)), ((550, 300, 580, 330), (650, 300))],   # 옛 뿔 가는 끝 · 넓은 입 · 몸통
                      # task 675 — 거울 없이 정본 휨 그대로: 밑동을 두 손 위로 올리고 끝을 머리 위로 내림(현 각도 약 53° — 끝 접선이 아래를 향해야 기름이 끝에서 떨어짐)
                      "keep_curve": True, "horn": ((548, 305), (530, 330), (582, 350)), "r": 12, "hole": True, "oil": ((582, 351), (583, 360)), "oil_w": 3,
                      "front": (508, 316, 562, 348), "local_box": (480, 250, 650, 410), "strengths": (0.2,)},
    # task 666 — 베들레헴 새 구도 666 s5에서: 두 손 오른쪽 밑동 → 꿇고 올려다보는 다윗 머리 위 끝
    "bethlehem15-canon": {"base": "samples/bethlehem-step23-t15/composition-A-s5.png", "out": "bethlehem15-horn-canon", "fixed": 666, "seed": 5, "canon": True,
                          # 옛 넓은 입·몸통은 둘레 화소로 메움(하늘 조각은 지평선 아래 들판에 네모로 보임 · 같은 높이 들판은 언덕이 솟아 안 맞음) · 옛 기름 방울
                          "erase": [[(430, 210), (482, 210), (512, 236), (524, 282), (506, 298), (478, 262), (430, 262)], [(524, 316), (534, 316), (534, 326), (524, 326)]],
                          "patch": [((500, 282, 542, 318), (546, 282))],   # 깔때기(뒤 형 회색 옷 — 옷 오른쪽 조각)
                          "horn": ((470, 268), (500, 242), (528, 290)), "r": 12, "hole": True, "oil": ((528, 291), (532, 312)), "oil_w": 3,
                          "front": (430, 245, 482, 296), "local_box": (410, 190, 580, 350), "strengths": (0.2,)},
    # task 676 — 확정 B1(베들레헴)의 곧은 원통 뿔을 정본으로: 사람 674 B1 「끝부분이 안닮았고 줄도없음 줄에 묶인 마개도 없고」 — 끝만 고치면 굵은 끝이 남음 → 정본을 바른 방향(keep_curve)으로 칠해 얹고 klein --ref(horn_scene_edit bethlehem15b1g)
    "bethlehem-b1": {"base": "samples/bethlehem15-horn-edit/edit-ref-s1.png", "out": "bethlehem-b1-canon", "fixed": 666, "seed": 5, "canon": True, "keep_curve": True,
                     "erase": [[(448, 232), (452, 215), (470, 211), (485, 222), (502, 258), (537, 291), (528, 303), (511, 291)]],
                     "horn": ((465, 224), (480, 270), (527, 293)), "r": 12, "hole": True, "oil": ((527, 294), (530, 318)), "oil_w": 3,
                     "hang": ((519, 287), (513, 299)), "front": (430, 240, 492, 290), "strengths": (0.2,)},
}
CANON_HORN = "frozen/props/oil-horn.png"
CANON_MOUTH, CANON_TIP = (352, 234), (1028, 130)   # 정본 1216×640에서 넓은 밑동(바닥판) 가운데 · 끝 마개 끝(task 673 정본 — 옛 661은 968,238)


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
        a[(yy > 330) & (lum > 90) & (sat < 60), 3] = 0   # 아래 회색 그림자(673 정본은 그림자가 330부터)
        import cv2   # 뿔 몸통의 옅은 호박색 줄무늬도 그림자 문턱에 걸려 구멍 — 바깥에서 닿지 않는 구멍은 다시 메움
        keep = (a[:, :, 3] > 128).astype("uint8") * 255
        ff = keep.copy(); cv2.floodFill(ff, np.zeros((ff.shape[0] + 2, ff.shape[1] + 2), "uint8"), (0, 0), 128)
        a[(ff == 0) & (yy > 300), 3] = 255   # 위쪽 끈 고리 안(종이)은 메우지 않음
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
    if cfg.get("keep_curve"):   # task 675 — 거울로 뒤집지 않고 돌리기만(사람 674 「기름뿔 뒤집힘」 — 정본은 배가 처진 U, 거울이면 위로 불룩한 ∩)
        side = 1
    arch = (base[0] - side * u[1], base[1] + side * u[0])          # 장면의 굽음 점 쪽
    M = cv2.getAffineTransform(np.float32([m, (m[0] + v[0] * k, m[1] + v[1] * k), sag]), np.float32([base, tip, arch]))
    layer = cv2.warpAffine(np.asarray(small), M, im.size, flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    out = im.convert("RGBA")
    out.alpha_composite(Image.fromarray(layer))
    return out.convert("RGB")


def tip_hole(im, cfg, k=4):
    """task 664 — 줄인 정본은 끝 구멍이 1화소로 사라짐(사람 663 「구멍 뚫린쪽으로 기름이 떨어져야함」) → 끝에 잘린 면(뿔 색)과 짙은 구멍을 칠하고 기름을 구멍에서 시작.
    화소로 바로 칠하면 검은 덩이·계단 진 줄(664 3판) → k배 크기 층에 그려 줄여 얹음."""
    import math
    base, ctrl, tip = cfg["horn"]
    (tx, ty), (ox, oy) = cfg["oil"]
    x0, y0 = int(min(tip[0], ox)) - 12, int(min(tip[1], ty)) - 12
    x1, y1 = int(max(tip[0], ox)) + 12, int(max(tip[1], oy)) + 12
    lay = Image.new("RGBA", ((x1 - x0) * k, (y1 - y0) * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    P = lambda x, y: ((x - x0) * k, (y - y0) * k)
    ang = math.atan2(tip[1] - ctrl[1], tip[0] - ctrl[0])   # 끝이 향하는 쪽
    ca, sa = math.cos(ang + math.pi / 2), math.sin(ang + math.pi / 2)
    def ell(cx, cy, rx, ry, n=40):   # rx = 잘린 면 너비(축에 수직) · ry = 축 방향 두께
        return [P(cx + rx * math.cos(t) * ca + ry * math.sin(t) * math.cos(ang), cy + rx * math.cos(t) * sa + ry * math.sin(t) * math.sin(ang))
                for t in (2 * math.pi * i / n for i in range(n))]
    w = cfg.get("oil_w", 3)
    d.line([P(tx, ty), P(ox, oy - 1)], fill=(206, 160, 38, 235), width=round(w * k * 0.8))   # 구멍에서 떨어지는 기름(가늘게)
    d.ellipse([*P(ox - 1.6, oy - 1.6), *P(ox + 1.6, oy + 1.8)], fill=(214, 168, 40, 240))   # 머리에 닿는 방울
    d.polygon(ell(*tip, 2.6, 1.3), fill=(118, 82, 48, 255), outline=(52, 34, 18, 255))      # 잘린 면(뿔 색)
    d.polygon(ell(*tip, 1.1, 0.7), fill=(20, 12, 5, 255))                                  # 주둥이 구멍
    small = lay.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    rgba = im.convert("RGBA")
    rgba.alpha_composite(small, (x0, y0))
    im.paste(rgba.convert("RGB"))
    return im


def front_hand(im, cfg):
    """원본에서 cfg front 상자 안 살빛 화소(g < 0.8r · r > 120 — 크림 바탕은 g/r≈0.94라 빠짐)를 뿔 위에 다시 얹음 → 손이 뿔 앞에."""
    import numpy as np
    if not cfg.get("front"):
        return im
    x0, y0, x1, y1 = cfg["front"]
    o = np.asarray(Image.open(os.path.join(CANON, cfg["base"])).convert("RGB")).astype(int)[y0:y1, x0:x1]
    m = ((o[:, :, 1] < 0.8 * o[:, :, 0]) & (o[:, :, 0] > 120)).astype("uint8") * 255
    from PIL import ImageFilter
    mk = Image.fromarray(m).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    im.paste(Image.fromarray(o.astype("uint8")), (x0, y0), mk)
    return im


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
        im = front_hand(paste_canon(im, cfg), cfg)
        if cfg.get("hang"):   # task 676 — 끝 아래 몸통에서 늘어진 끈과 매달린 마개(붓는 중이라 뺌)
            (hx0, hy0), (hx1, hy1) = cfg["hang"]
            dd = ImageDraw.Draw(im)
            dd.line([(hx0, hy0), ((hx0 + hx1) / 2 - 1, (hy0 + hy1) / 2 + 2), (hx1, hy1)], fill=(140, 86, 44), width=2, joint="curve")
            dd.rounded_rectangle([hx1 - 3, hy1, hx1 + 3, hy1 + 7], radius=2, fill=(210, 174, 124), outline=(110, 74, 40))
        if cfg.get("hole"):
            tip_hole(im, cfg)
            im.save(os.path.join(out, "src.png")); print("[HornCompose]", os.path.join(out, "src.png")); return
        if True:   # 끝 구멍은 다시 그린 뒤(repaste)에만 칠함 — 다시 그리기 전에 칠하면 생성기가 짙은 구멍을 나팔 입으로 키움(664 1판)
            d = ImageDraw.Draw(im)
            (tx, ty), (ox, oy) = cfg["oil"]
            d.line([(tx, ty), (ox, oy)], fill=(214, 168, 40), width=round(cfg.get("oil_w", 3)))   # 끝 주둥이에서 머리로 떨어지는 금빛 기름
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
    im = front_hand(im, cfg)
    if cfg.get("hole"):
        tip_hole(im, cfg)
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


def local(cfg, box=None):
    """task 663 — 그림 전체 i2i가 멀리 있는 시위대 팔을 바꿈(t.arm-length·t.hands-clear-guards 새로 걸림) → 다시 그린 뿔 둘레(box, 흐린 경계)만 원본에 되붙임."""
    from PIL import ImageFilter
    box = box or cfg.get("local_box", (470, 270, 650, 430))
    out = os.path.join(CANON, "samples", cfg["out"])
    first = cfg["strengths"][0]
    base = Image.open(os.path.join(CANON, cfg["base"])).convert("RGB")
    new = Image.open(os.path.join(out, f"src2-{first}.png")).convert("RGB")
    m = Image.new("L", base.size, 0)
    for b in (box if isinstance(box, list) else [box]):
        ImageDraw.Draw(m).rounded_rectangle([b[0] + 12, b[1] + 12, b[2] - 12, b[3] - 12], radius=20, fill=255)
    res = Image.composite(new, base, m.filter(ImageFilter.GaussianBlur(10)))
    res.save(os.path.join(out, f"local-{first}.png"))
    print("[HornCompose]", os.path.join(out, f"local-{first}.png"))


if __name__ == "__main__":
    {"compose": compose, "redraw": redraw, "repaste": repaste, "local": local}[sys.argv[2]](SCENES[sys.argv[1]])
