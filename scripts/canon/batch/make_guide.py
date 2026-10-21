#!/usr/bin/env python3
"""task#388 — 구도 가이드(깊이) 그림: 장면 명세의 `regions`·`guide` 두 칸에서만 결정적으로 파생한다(같은 명세 → 같은 바이트).

  python3 batch/make_guide.py [--scene <장면 id>] [--out <png>]     # 기본: 요단 귀환 → samples/jordan-guide/guide.png

깊이 그림 = 가까움 밝게 · 멂 어둡게. 선을 주지 않고(ZIMAGE §2 「콘티 되그림」) 자리·크기·멀고 가까움만 준다.
꼴(guide.shape): person(서 있는 한 사람) · person_bow(고개를 앞·아래로 숙인 서 있는 사람, restyle r5) · prostrate(엎드린 낮은 몸, 머리는 왼쪽 — 다윗 쪽) · crowd(작은 실루엣 두 줄) · boat(선체) · bank(강 너머 둑).
바탕: 하늘 0 · 땅은 지평선(0.26)에서 아래로 0.12 → 0.5. 그리는 순서는 먼 것부터(깊이 오름차순)."""
import argparse, json, os

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1216, 640
HORIZON, GROUND = 0.26, (0.12, 0.5)


def person(d, x0, y0, x1, y1, v):
    h, cx = y1 - y0, (x0 + x1) / 2
    bw = min(x1 - x0, h * 0.3)
    r = h * 0.065
    d.ellipse([cx - r, y0, cx + r, y0 + 2 * r], fill=v)
    sh = y0 + 2 * r
    d.polygon([(cx - bw * 0.3, sh), (cx + bw * 0.3, sh), (cx + bw / 2, y1), (cx - bw / 2, y1)], fill=v)


def person_bow(d, x0, y0, x1, y1, v):
    """restyle r5 — 고개를 앞(화면 오른쪽)·아래로 숙인 서 있는 사람: 몸은 person과 같고 머리 원이 어깨선 앞·아래, 목이 앞으로 기욺."""
    h, cx = y1 - y0, (x0 + x1) / 2
    bw = min(x1 - x0, h * 0.3)
    r = h * 0.065
    sh = y0 + 2 * r
    d.polygon([(cx - bw * 0.3, sh), (cx + bw * 0.3, sh), (cx + bw / 2, y1), (cx - bw / 2, y1)], fill=v)
    hx, hy = cx + r * 1.3, y0 + r * 2.1                                           # 숙인 머리 가운데(앞·아래)
    d.polygon([(cx - r * 0.5, sh + r * 0.3), (cx + r * 0.5, sh), (hx + r * 0.3, hy), (hx - r * 0.5, hy + r * 0.4)], fill=v)  # 앞으로 기운 목
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=v)


def prostrate(d, x0, y0, x1, y1, v):
    h, w = y1 - y0, x1 - x0
    d.ellipse([x0 + w * 0.15, y0 + h * 0.25, x1, y1 + h * 0.2], fill=v)          # 굽힌 등·다리
    r = h * 0.22
    d.ellipse([x0, y1 - 2 * r, x0 + 2 * r, y1], fill=v)                          # 땅에 댄 머리(왼쪽)


def crowd(d, x0, y0, x1, y1, v):
    h = y1 - y0
    for row, (ph, top, val) in enumerate(((h * 0.62 * 0.9, y0, round(v * 0.92)), (h * 0.62, y1 - h * 0.62, v))):
        step = ph * 0.32
        n = max(1, int((x1 - x0 - ph * 0.3) / step))
        for i in range(n):
            x = x0 + ph * 0.15 + i * step + (step / 2 if row == 0 else 0)
            dy = (i % 3) * ph * 0.04                                              # 키 들쭉날쭉(고정 무늬)
            if x + ph * 0.15 <= x1:
                person(d, x - ph * 0.15, top + dy, x + ph * 0.15, top + ph, val)


def boat(d, x0, y0, x1, y1, v):
    h, w = y1 - y0, x1 - x0
    d.polygon([(x0, y0 + h * 0.35), (x1, y0 + h * 0.35), (x1 - w * 0.08, y1), (x0 + w * 0.08, y1)], fill=v)


def bank(d, x0, y0, x1, y1, v):
    h, w = y1 - y0, x1 - x0
    d.polygon([(x0, y1), (x0 + w * 0.2, y0 + h * 0.4), (x0 + w * 0.5, y0), (x0 + w * 0.8, y0 + h * 0.3), (x1, y0 + h * 0.5), (x1, y1)], fill=v)


SHAPES = {"person": person, "person_bow": person_bow, "prostrate": prostrate, "crowd": crowd, "boat": boat, "bank": bank}


def make(spec):
    g, R = spec["guide"], spec["regions"]
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    hy = int(HORIZON * H)
    for y in range(hy, H):
        t = (y - hy) / (H - 1 - hy)
        d.line([(0, y), (W, y)], fill=round(255 * (GROUND[0] + t * (GROUND[1] - GROUND[0]))))
    for k in sorted(g["depth"], key=lambda k: (g["depth"][k], k)):
        x0, y0, x1, y1 = R[k]
        SHAPES[g["shape"][k]](d, x0 * W, y0 * H, x1 * W, y1 * H, round(255 * g["depth"][k]))
    return img.filter(ImageFilter.GaussianBlur(3)).convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", default="authored-david-returns-jerusalem")
    ap.add_argument("--out", default=os.path.join(HERE, "samples", "jordan-guide", "guide.png"))
    a = ap.parse_args()
    spec = json.load(open(os.path.join(HERE, "scenes", f"{a.scene}.json"), encoding="utf-8"))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    make(spec).save(a.out, format="PNG")
    print(f"[MakeGuide] {a.out}")


if __name__ == "__main__":
    main()
