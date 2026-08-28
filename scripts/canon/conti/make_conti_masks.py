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

## 2026-08-28 — **볼록껍질을 폐기한다. 그것이 사용자가 지적한 두 결함의 단일 원인이었다** (라운드 9)

part 3 최종본에서 사람이 지적한 두 가지 — 골리앗이 「각진 직사각형 패치로 붙었다」와 다윗의 든 팔이
「평평한 회색 관/쐐기」 — 는 표본도 화풍도 CN·IP도 아니라 **이 마스크**가 원인이었다(`notes/ZIMAGE.md`
§9-13). 실측: 최종본에서 배경과 달라진 화소의 **96.9%가 골리앗 마스크 안**이고, 눈에 보이는 패치의
경계가 **마스크 경계와 정확히 일치**한다. 껍질은 정의상 볼록이라 팔·다리 사이를 직선으로 이어
배경을 함께 품는다 — 골리앗 껍질은 bbox의 **.8500**(거의 사각형), 다윗은 **.5491**. 인페인팅은
마스크 안을 전부 다시 그리므로 그 배경이 인물과 함께 새로 그려지고, 껍질의 직선 경계가 그대로
「각진 패치」로 남는다.

**위 위상 문제는 실재하지만 볼록껍질이 유일한 답은 아니었다.** 순서를 바꾸면 풀린다:
**닫기(closing) → 구멍 채우기 → 팽창**. 닫기가 성긴 선의 틈을 메워 몸통·머리 윤곽을 닫고,
구멍 채우기가 그 **닫힌 내부만** 채운다(다리 사이는 바깥 배경과 이어져 있으므로 채워지지 않는다 —
그것이 옳은 동작이다). 결과는 볼록이 아니라 **인물 형태를 따르는** 실루엣이고, 직선 경계가 없으므로
「각진 패치」가 생길 기하가 사라진다.

값은 **저작된 콘티에서 파생한다**(손으로 고르지 않는다):
  - 닫기 반지름 = 그 인물 획 두께(`stroke-width`) — 성긴 선의 틈은 획 두께 규모다.
  - 팽창 반지름 = **머리 원 반지름 × 0.5**. 골격선은 팔다리의 **중심**을 지나므로 반지름의 절반만큼
    부풀리면 팔 두께 ≈ 머리 반지름이 된다(사람 비례에 맞는 유일한 자연 척도이고, 머리 원은
    `<circle id="head-*">`로 저작돼 있다 — `judge_s1.conti_head_box()`가 같은 자리를 읽는다).

실측 결과: 겹침 0 · 잉크 포함률 1.0000/1.0000 유지 · bbox 채움률 **다윗 .5491 → .3244** ·
**골리앗 .8500 → .6381**.
"""
import io
import os
import re
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


def _convex_hull_mask(mask):
    """마스크 점군의 볼록껍질. **파생 경로가 아니라 「먼 비율」 기준의 음성 대조군 전용이다** —
    2026-08-28 라운드 9가 껍질을 폐기했으므로(docstring 참조) 여기 남는 이유는 오직
    「고쳐진 파생이 껍질과 실제로 다르다」를 코드가 매번 재확인하기 위한 것이다.
    모노톤 체인(Andrew's monotone chain) — scipy 없이 numpy만으로 얻는다."""
    ys, xs = np.where(mask)
    pts = sorted(set(zip(xs.tolist(), ys.tolist())))
    if len(pts) <= 2:
        return mask

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
    img = Image.new("L", params.SCENE_SIZE, 0)
    ImageDraw.Draw(img).polygon(lower[:-1] + upper[:-1], fill=255)
    return np.array(img) > 0


def _far_fraction(mask, ink, r):
    """마스크 화소 중 콘티 잉크의 **파생 팽창 반경 밖**에 있는 비율 = 「이 마스크가 그림이
    함의하지 않는 배경을 얼마나 품는가」. 2026-08-28 라운드 10에 C2(ii)를 대체한 기준이다.

    구 기준 `bbox 채움률 < 0.95`는 골리앗 볼록껍질 **.8500을 통과시켰고**, 「각진 직사각형
    패치」 결함이 그 틈으로 들어왔다(`notes/ZIMAGE.md` §9-13). bbox 채움률은 인물의 자세에
    따라 정상 범위가 달라서(다윗 .3260 ↔ 골리앗 .6387) 하나의 숫자로 두 인물을 가를 수 없다 —
    반면 이 비율은 **두 인물 모두 실루엣 .01 · 껍질 .26~.42**로 한 자리에서 갈린다.
    """
    return float((mask & ~_dilate(ink, r)).sum()) / float(mask.sum())


def _erode(mask, r):
    if r <= 0:
        return mask
    im = Image.fromarray((mask.astype(np.uint8) * 255), mode="L")
    return np.array(im.filter(ImageFilter.MinFilter(2 * r + 1))) > 0


def _fill_holes(mask):
    """닫힌 내부만 채운다 — 바깥 배경과 이어진 곳(다리 사이)은 그대로 둔다.

    `Image.fromarray`는 **읽기전용 뷰**를 주고 그 위의 `floodfill`은 조용히 실패한다(실측) —
    `.copy()`가 필수다.
    """
    img = Image.fromarray((~mask).astype(np.uint8) * 255, mode="L").copy()
    ImageDraw.floodfill(img, (0, 0), 128)
    return mask | (np.array(img) == 255)


def _head_circle(who):
    """저작된 머리 원의 (반지름, 획 두께) — 실루엣의 두 파생값이 여기서 나온다."""
    html = io.open(os.path.join(HERE, "goliath_scene.html"), encoding="utf-8").read()
    m = re.search(r'<circle\s+id="head-%s"([^/>]*)/?>' % re.escape(who), html)
    if not m:
        sys.exit(f'콘티에 머리 마커가 없다: <circle id="head-{who}">')
    at = dict(re.findall(r'([\w-]+)="([^"]+)"', m.group(1)))
    return float(at["r"]), float(at.get("stroke-width", 0))


def _silhouette(ink, who):
    """닫기 → 구멍 채우기 → 팽창. 값은 저작된 머리 원에서 파생한다(docstring 참조)."""
    r, sw = _head_circle(who)
    close_r = int(round(sw))
    dilate_r = int(round(r * 0.5))
    m = _erode(_dilate(ink, close_r), close_r)
    m = _fill_holes(m)
    return (_dilate(m, dilate_r) | ink), close_r, dilate_r


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

    # --- 실루엣 파생 (닫기 → 구멍 채우기 → 팽창; 값은 저작된 머리 원에서 나온다) ------
    final_mask, radii = {}, {}
    for n in NAMES:
        final_mask[n], close_r, dilate_r = _silhouette(ink[n], n)
        radii[n] = (close_r, dilate_r)

    # --- 완료기준을 코드가 직접 확인한다 (통과 못하면 저장하지 않는다) ----------------
    overlap_px = int((final_mask["david"] & final_mask["goliath"]).sum())
    containment = {n: float((ink[n] & final_mask[n]).sum()) / float(ink[n].sum()) for n in NAMES}
    fills = {n: _bbox_fill_ratio(final_mask[n]) for n in NAMES}

    # 「먼 비율」 임계를 **대조군에서 파생한다**(손으로 고르지 않는다):
    #   양성 = 팽창만 한 마스크(구멍 채우기 없음) — 정의상 먼 비율 0이므로 구조적으로 확정된다.
    #   음성 = 그 마스크의 볼록껍질 — 폐기된 구 파생이고, 결함이 실측된 자리다.
    #   임계 = 둘의 **산술 중점**(축 C의 `threshold_rule`과 같은 규칙 — 양성이 0이라 로그중점은
    #          퇴화한다). 인물별로 파생해 인물마다 다른 자세를 반영한다.
    far, far_thr, far_ctl = {}, {}, {}
    for n in NAMES:
        r = radii[n][1]
        pos = _far_fraction(_dilate(ink[n], r) | ink[n], ink[n], r)          # = 0
        neg = _far_fraction(_convex_hull_mask(final_mask[n]), ink[n], r)
        far_ctl[n] = (pos, neg)
        far_thr[n] = (pos + neg) / 2.0
        far[n] = _far_fraction(final_mask[n], ink[n], r)

    problems = []
    if overlap_px != 0:
        problems.append(f"두 마스크가 {overlap_px}px 겹친다 (0이어야 한다)")
    for n in NAMES:
        if containment[n] < 0.95:
            problems.append(f"{n} 잉크 포함률 {containment[n]:.4f} < 0.95")
        if fills[n][0] >= 0.95:
            problems.append(f"{n} bbox 채움률 {fills[n][0]:.4f} >= 0.95 (사각형 마스크다)")
        if far_ctl[n][1] <= far_thr[n]:
            problems.append(f"{n} 음성 대조군(볼록껍질) 먼비율 {far_ctl[n][1]:.4f}이 "
                            f"임계 {far_thr[n]:.4f}를 통과한다 — 기준이 갈라내지 못한다")
        if far[n] >= far_thr[n]:
            problems.append(f"{n} 먼비율 {far[n]:.4f} >= 임계 {far_thr[n]:.4f} "
                            f"(그림이 함의하지 않는 배경을 품는다 — ZIMAGE §9-13)")
    if problems:
        sys.exit("완료기준 미달 — 저장하지 않는다:\n  " + "\n  ".join(problems))

    os.makedirs(HERE, exist_ok=True)
    for n in NAMES:
        Image.fromarray(final_mask[n].astype(np.uint8) * 255, mode="L").save(
            os.path.join(HERE, f"mask_{n}.png"))

    print("파생: 닫기 → 구멍 채우기 → 팽창 (볼록껍질 폐기 — docstring 2026-08-28)")
    print(f"두 마스크 AND 겹침 픽셀 = {overlap_px} (기대 0)")
    for n in NAMES:
        r, sw = _head_circle(n)
        fill, bbox = fills[n]
        print(f"{n}: 머리r={r:.0f} 획={sw:.0f} → 닫기 {radii[n][0]}px · 팽창 {radii[n][1]}px  "
              f"잉크 {int(ink[n].sum())}px  마스크 {int(final_mask[n].sum())}px  bbox={bbox}  "
              f"bbox 내부 채움률 {fill:.4f} (볼록껍질: david .5491 · goliath .8500)  "
              f"잉크 포함률 {containment[n]:.4f}")
        print(f"    먼비율 {far[n]:.4f} < 임계 {far_thr[n]:.4f}  "
              f"(대조군 — 양성 팽창만 {far_ctl[n][0]:.4f} · 음성 볼록껍질 {far_ctl[n][1]:.4f})")

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
