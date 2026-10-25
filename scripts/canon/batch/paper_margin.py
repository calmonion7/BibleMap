#!/usr/bin/env python3
"""task 422 — 그림 둘레 미색 종이 여백(규칙 generate.trim-paper-margin): 재고, 생성 뒤 잘라 원래 크기로.

  python3 batch/paper_margin.py measure <그림…>   # 장마다 왼·위·오른·아래 여백(px) + 띠 있는 장 수

화풍 머리 「warm cream paper」가 그림 둘레에 고른 미색 띠를 남긴다(task 421 s11 — 사람은 채택, 가드 문항은 「종이 테두리」로 떨굼).
여백 = 가장자리에서 안쪽으로 「종이 줄」(줄 화소의 97% 넘게가 그 줄 가운데 밝은 미색 빛에 모임)이 이어지는 폭.
가장자리 줄이 종이가 아니면(그림이 가장자리까지 — 그린 틀 포함) 0. 잘라낼 때는 띠 + 번짐 2px를 자르고 원래 비율을 지켜(남는 쪽 가운데로 더 자름) 원래 크기로 키운다.
안쪽에 그린 틀·액자는 띠가 아니라 그대로 남는다 — 가드 문항이 계속 잡는다.
종이 여백은 세 변 이상에 고르게 남는다 — 한두 변만 종이 빛이면 야외 빈 하늘·빈 벽·지물 시트라 자르지 않고(task 425 — 승인 13장 띠 8장이 모두 위쪽만 = 하늘),
세 변 이상이어도 한 변이 다른 띠 변 가운데값의 WIDE배를 넘으면 여백 + 빈 면으로 보고 그 배까지만 자른다."""
import statistics
import sys

import numpy as np
from PIL import Image

TOL = 14          # 종이 빛과의 채널 차 상한
LINE = 0.97       # 줄이 종이일 화소 비율
MIN_BAND = 2      # 이보다 얇으면 띠 아님(잡음)
CAP = 0.2         # 한 변 여백 상한(그림 크기 비율) — 넘으면 띠가 아니라 빈 그림 면으로 봄
FADE = 2          # 띠 안쪽 번짐 줄
SIDES = 3         # 띠가 이만큼 변에서 잡혀야 종이 여백(task 425)
WIDE = 3          # 한 변 띠가 다른 띠 변 가운데값의 이 배를 넘으면 그 배까지만(여백 + 빈 하늘)


def paper_line(line):
    """줄 하나가 종이인가 — 줄 화소의 LINE 넘게가 그 줄 가운데 빛에 TOL 안으로 모이고, 그 빛이 밝은 미색.
    빛을 줄마다 따로 잡는다: 여백은 바깥(흰빛) → 안쪽(미색)으로 빛이 변해 둘레 빛 하나로는 띠를 덜 잰다(task 422 s202 곁 장면 7px/30px)."""
    c = np.median(line, axis=0)
    if not (c[0] >= 228 and c[1] >= 218 and c[2] >= 180):
        return False
    return (np.abs(line - c) <= TOL).all(axis=1).mean() >= LINE


def measure(im):
    """→ (왼, 위, 오른, 아래) 잘라낼 종이 여백 px — bands에 세 변 규칙·넓은 변 상한을 건 값."""
    m = bands(im)
    if sum(1 for v in m if v) < SIDES:
        return (0, 0, 0, 0)
    out = []
    for i, v in enumerate(m):
        rest = [x for j, x in enumerate(m) if x and j != i]
        out.append(min(v, int(WIDE * statistics.median(rest))) if v else 0)
    return tuple(out)


def bands(im):
    """→ (왼, 위, 오른, 아래) 종이 빛 띠 px(잰 값 그대로 — 빈 하늘·빈 벽도 잡힘). 세로줄은 이미 잡은 위·아래 띠를 빼고, 가로줄은 왼·오른 띠를 빼고 잰다(옆 띠가 줄을 흐림) — 안정될 때까지."""
    a = np.asarray(im.convert("RGB")).astype(int)
    h, w, _ = a.shape

    def band(get, cap):
        n = 0
        while n < cap and paper_line(get(n)):
            n += 1
        return n if MIN_BAND <= n < cap else 0
    m = (0, 0, 0, 0)
    for _ in range(4):
        l, t, r, b = m
        rows, cols = slice(t, h - b), slice(l, w - r)
        new = (band(lambda i: a[rows, i], int(w * CAP)), band(lambda i: a[i, cols], int(h * CAP)),
               band(lambda i: a[rows, w - 1 - i], int(w * CAP)), band(lambda i: a[h - 1 - i, cols], int(h * CAP)))
        if new == m:
            break
        m = new
    return m


def trim(im, passes=5):
    """여백이 있으면 잘라 원래 크기로(비율 지킴), 없으면 그대로 같은 그림. 자른 뒤 번지는 가장자리가 새 띠로 잡히면 다시(최대 passes번 — 출생 16장은 4번 안에 0)
    — 생성(run_scene)과 합성(inset_try comp)에서 두 번 불려도 같은 그림이 되게."""
    for _ in range(passes):
        out = trim_once(im)
        if out is im:
            return im
        im = out
    return im


def trim_once(im):
    l, t, r, b = measure(im)
    if not any((l, t, r, b)):
        return im
    W, H = im.size
    x0, y0 = l + FADE if l else 0, t + FADE if t else 0
    x1, y1 = W - (r + FADE if r else 0), H - (b + FADE if b else 0)
    cw, ch = x1 - x0, y1 - y0
    if cw * H > ch * W:   # 남는 가로를 가운데로 더 자름
        k = cw - round(ch * W / H)
        x0, x1 = x0 + k // 2, x1 - (k - k // 2)
    else:
        k = ch - round(cw * H / W)
        y0, y1 = y0 + k // 2, y1 - (k - k // 2)
    return im.convert("RGB").crop((x0, y0, x1, y1)).resize((W, H), Image.LANCZOS)


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "measure":
        sys.exit(__doc__)
    hit = 0
    for f in sys.argv[2:]:
        m = measure(Image.open(f))
        hit += any(m)
        print(f"{f}\t{' '.join(map(str, m))}")
    print(f"[PaperMargin] 띠 있음 {hit}/{len(sys.argv) - 2}")
