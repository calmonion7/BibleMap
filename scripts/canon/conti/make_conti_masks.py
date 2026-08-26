"""생성 전용 콘티(render_conti.py 산출)에서 다윗·골리앗 실루엣 마스크를 파생한다(task#318 S4).

make_masks.py의 BBOX_RATIONALE이 채택했던 바운딩 박스는 회고 260825-013953이 "헐겁다"(배경을
많이 품는다)고 지적한 근거를 얻어 여기서 폐기한다. 대신 **콘티 잉크 점군의 볼록껍질(convex hull)**을
실루엣으로 쓴다 — 두 인물이 화면에서 좌우로 크게 떨어져 있어(아래 실측) 껍질끼리 겹치지 않고,
껍질은 정의상 자신을 만든 점을 전부 포함하므로(포함률 100%) 팽창 없이도 완료기준을 만족한다.
그래도 값을 손으로 0으로 못박지 않고, r=0부터 실제로 검색해(아래 while 루프) 두 조건
(겹침 0 · 포함률 ≥0.95)이 껍질만으로 성립함을 코드가 직접 확인한 뒤에만 0을 채택한다 — 조건이
안 맞으면 r을 올려 PIL MaxFilter로 추가 팽창한다(ADR 260823-221839 — 임계는 정답지/대조군에서
파생하지, 손으로 고르지 않는다).

콘티의 모든 도형이 stroke-only(fill=none)라 몸통·머리는 닫힌 윤곽처럼 보여도 다리 사이 골반
아래가 열려 있어(구멍 채우기로는 안 닫힌다) 단순 팽창만으로는 성긴 선 그대로 남는다 — 볼록껍질은
이 위상 문제를 건너뛰고 사람이 보는 "실루엣"에 더 가까운 solid한 다각형을 준다.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import params  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = ("david", "goliath")


def _ink_mask(png_path):
    """make_masks.py의 _ink_mask와 같은 산식(코너=배경, |a-bg|>params.THRESHOLD=잉크) —
    같은 임계·같은 극성이어야 잉크 정의가 파이프라인 전체에서 갈리지 않는다."""
    im = Image.open(png_path).convert("L").resize(params.SCENE_SIZE, Image.LANCZOS)
    a = np.array(im).astype(int)
    bg = int(np.median(a[0:8, 0:8]))
    return np.abs(a - bg) > params.THRESHOLD


def _convex_hull(points_xy):
    """모노톤 체인(Andrew's monotone chain) — scipy 없이 numpy만으로 볼록껍질 좌표를 얻는다."""
    pts = sorted(set(map(tuple, points_xy)))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _hull_mask(ink):
    ys, xs = np.where(ink)
    hull_xy = _convex_hull(np.stack([xs, ys], axis=1))
    mask_img = Image.new("L", params.SCENE_SIZE, 0)
    ImageDraw.Draw(mask_img).polygon(hull_xy, fill=255)
    return np.array(mask_img) > 0, hull_xy


def _dilate(mask, r):
    if r == 0:
        return mask
    im = Image.fromarray((mask.astype(np.uint8) * 255), mode="L")
    return np.array(im.filter(ImageFilter.MaxFilter(2 * r + 1))) > 0


def _bbox_fill_ratio(mask):
    ys, xs = np.where(mask)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    area = (y1 - y0 + 1) * (x1 - x0 + 1)
    return float(mask.sum()) / area, (int(x0), int(y0), int(x1), int(y1))


def main():
    ink = {n: _ink_mask(os.path.join(HERE, f"{n}.png")) for n in NAMES}
    hull_mask = {}
    hull_xy = {}
    for n in NAMES:
        hull_mask[n], hull_xy[n] = _hull_mask(ink[n])

    # --- 팽창 반지름 r 탐색 (하드코딩 금지) ------------------------------------
    # r=0(껍질 그대로)부터 올리며 "겹침 0 & 포함률 ≥0.95"를 둘 다 만족하는 최소값을 찾는다.
    r = 0
    while r <= 50:
        cand = {n: _dilate(hull_mask[n], r) for n in NAMES}
        overlap_px = int((cand["david"] & cand["goliath"]).sum())
        containment = {n: float((ink[n] & cand[n]).sum()) / float(ink[n].sum()) for n in NAMES}
        if overlap_px == 0 and all(c >= 0.95 for c in containment.values()):
            break
        r += 1
    else:
        sys.exit(f"r<=50 범위에서 겹침0·포함률>=0.95를 동시에 만족하는 값을 못 찾았다 (마지막 r={r})")

    final_mask = cand
    os.makedirs(HERE, exist_ok=True)
    for n in NAMES:
        Image.fromarray(final_mask[n].astype(np.uint8) * 255, mode="L").save(
            os.path.join(HERE, f"mask_{n}.png"))

    print(f"탐색된 최소 팽창 반지름 r = {r}px (0 = 볼록껍질 자체로 이미 두 조건 충족)")
    print(f"두 마스크 AND 겹침 픽셀 = {overlap_px} (기대 0)")
    for n in NAMES:
        fill, bbox = _bbox_fill_ratio(final_mask[n])
        print(f"{n}: 잉크 {int(ink[n].sum())}px  껍질꼭짓점 {len(hull_xy[n])}개  "
              f"마스크 {int(final_mask[n].sum())}px  bbox={bbox}  "
              f"bbox 내부 채움률 {fill:.4f} (기존 bbox 마스크는 정의상 1.0000)  "
              f"잉크 포함률 {containment[n]:.4f}")

    # --- 오버레이 --------------------------------------------------------------
    base = Image.open(os.path.join(HERE, "goliath_scene.png")).convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    colors = {"david": (30, 100, 220, 90), "goliath": (220, 40, 40, 90)}
    for n in NAMES:
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        px = np.zeros((*params.SCENE_SIZE[::-1], 4), dtype=np.uint8)
        px[final_mask[n]] = colors[n]
        layer = Image.fromarray(px, mode="RGBA")
        overlay = Image.alpha_composite(overlay, layer)
    out = Image.alpha_composite(base, overlay)
    out_path = os.path.join(HERE, "mask_overlay.png")
    out.save(out_path)
    print(f"저장: mask_david.png · mask_goliath.png · {out_path}")


if __name__ == "__main__":
    main()
