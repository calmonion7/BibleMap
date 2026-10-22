#!/usr/bin/env python3
"""task#388 — 구도 가이드(깊이) 그림: 장면 명세의 `regions`·`guide` 두 칸에서만 결정적으로 파생한다(같은 명세 → 같은 바이트).

  python3 batch/make_guide.py [--scene <장면 id>] [--out <png>]     # 기본: 요단 귀환 → samples/jordan-guide/guide.png

깊이 그림 = 가까움 밝게 · 멂 어둡게. 선을 주지 않고(ZIMAGE §2 「콘티 되그림」) 자리·크기·멀고 가까움만 준다.
꼴(guide.shape): person(서 있는 한 사람) · person_bow(고개를 앞·아래로 숙인 서 있는 사람, restyle r5) · kneel_bow(무릎 꿇고 엉덩이 들고 머리를 왼쪽 땅에, r6) · seated(배 안에 앉은 머리·어깨 한 줄, r6) · prostrate(엎드린 낮은 몸, 머리는 왼쪽 — 다윗 쪽) · crowd(작은 실루엣 두 줄) · boat(선체) · bank(강 너머 둑).
바탕: 하늘 0 · 땅은 지평선(0.26)에서 아래로 0.12 → 0.5. 그리는 순서는 먼 것부터(깊이 오름차순)."""
import argparse, json, os

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1216, 640
HORIZON, GROUND = 0.26, (0.12, 0.5)
ROOM_WALL = 0.12   # 실내 뒷벽 깊이(바닥 시작값과 같음 — 벽과 바닥이 이어짐)
# task 400 a5 — 몸 너비(키 비율)를 카드 체격(card.silhouette)에서: guide.body = "card"일 때만(옛 가이드 바이트 유지).
# a3·a4: 카드는 넓은 어깨·통 몸통인데 가이드 몸이 기본 너비면 체격 문구가 화면 끝 셋째 인물로 그려짐.
BUILD_WIDTH = {"slight": 0.26, "lean": 0.28, "average": 0.3, "broad": 0.4, "heavy": 0.44, "giant": 0.44}
BODY = {"w": 0.3, "knee": False}   # make()가 인물마다 바꾸는 몸 너비·무릎 아래 다리 — 꼴 함수 서명(d, 상자, v)을 그대로 두려고 모듈 상태로 둠
KNEE = 0.72   # 무릎 높이(키 비율, 머리 위끝부터)


def body(d, top_l, top_r, cx, y0, y1, bw, v):
    """몸통: 어깨(top_l~top_r)에서 발까지 넓어지는 사다리꼴. BODY["knee"]면(task 402 b2) 무릎까지만 사다리꼴, 무릎 아래는 벌린 두 다리
    — b1: 바닥까지 넓어지는 사다리꼴 실루엣이 곧 긴 로브라 「무릎 길이 튜닉」 문구를 이겼다(사울 긴 망토 8/8). 다리를 굵게 해 몸 덩어리 유지."""
    h, sh = y1 - y0, top_l[1]
    if not BODY["knee"]:
        d.polygon([top_l, top_r, (cx + bw / 2, y1), (cx - bw / 2, y1)], fill=v)
        return
    ky = y0 + h * KNEE
    kw = bw * 0.5 * (ky - sh) / (y1 - sh) + abs(top_r[0] - top_l[0]) / 2 * (y1 - ky) / (y1 - sh)   # 무릎 높이에서 사다리꼴 반폭
    d.polygon([top_l, top_r, (cx + kw, ky), (cx - kw, ky)], fill=v)
    lw = bw * 0.28
    for s in (-1, 1):
        d.polygon([(cx + s * kw * 0.15 - lw / 2, ky), (cx + s * kw * 0.15 + lw / 2, ky), (cx + s * bw * 0.5 + lw / 2, y1), (cx + s * bw * 0.5 - lw / 2, y1)], fill=v)


def person(d, x0, y0, x1, y1, v):
    h, cx = y1 - y0, (x0 + x1) / 2
    bw = min(x1 - x0, h * BODY["w"])
    r = h * 0.065
    d.ellipse([cx - r, y0, cx + r, y0 + 2 * r], fill=v)
    sh = y0 + 2 * r
    body(d, (cx - bw * 0.3, sh), (cx + bw * 0.3, sh), cx, y0, y1, bw, v)


def person_bow(d, x0, y0, x1, y1, v):
    """restyle r5 — 고개를 앞(화면 오른쪽)·아래로 숙인 서 있는 사람: 몸은 person과 같고 머리 원이 어깨선 앞·아래, 목이 앞으로 기욺."""
    h, cx = y1 - y0, (x0 + x1) / 2
    bw = min(x1 - x0, h * BODY["w"])
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


def kneel_bow(d, x0, y0, x1, y1, v):
    """restyle r6 — 무릎 꿇고 엎드려 절함(누움 아님): 엉덩이가 가장 높고(오른쪽), 등이 왼쪽 아래로 기울어 머리가 땅에 닿고, 정강이는 엉덩이 밑 땅에."""
    h, w = y1 - y0, x1 - x0
    d.polygon([(x0 + w * 0.2, y1 - h * 0.08), (x0 + w * 0.3, y1 - h * 0.5), (x0 + w * 0.58, y0), (x0 + w * 0.8, y0 + h * 0.08),
               (x0 + w * 0.84, y1 - h * 0.1), (x0 + w * 0.55, y1)], fill=v)                     # 등·엉덩이·허벅지
    d.polygon([(x0 + w * 0.55, y1 - h * 0.12), (x1, y1 - h * 0.1), (x1, y1), (x0 + w * 0.55, y1)], fill=v)  # 땅에 댄 정강이·발(오른쪽)
    r = h * 0.17
    d.ellipse([x0, y1 - 2 * r, x0 + 2 * r, y1], fill=v)                                         # 땅에 댄 머리(왼쪽)


def seated(d, x0, y0, x1, y1, v):
    """restyle r6 — 배 안에 앉은 사람들: 머리·어깨만 한 줄(뱃전 위로 보이는 몫). 상자 아래 끝 = 뱃전."""
    h = y1 - y0
    r, step = h * 0.22, h * 0.62
    n = max(1, int((x1 - x0) / step))
    for i in range(n):
        cx = x0 + step * (i + 0.5)
        d.ellipse([cx - r, y0, cx + r, y0 + 2 * r], fill=v)
        d.polygon([(cx - r * 1.3, y0 + 2 * r), (cx + r * 1.3, y0 + 2 * r), (cx + r * 1.6, y1), (cx - r * 1.6, y1)], fill=v)


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


def leaning(d, x0, y0, x1, y1, v, lean):
    """몸통을 lean(키 비율, 음수 = 화면 왼쪽)만큼 위쪽을 기울인 사람 — 머리·어깨가 옮겨지고 두 발은 벌림. → (어깨 가운데 x, 머리 반지름)."""
    h, cx = y1 - y0, (x0 + x1) / 2
    bw, r, dx = min(x1 - x0, h * BODY["w"]), h * 0.065, h * lean
    hx = cx + dx
    d.ellipse([hx - r, y0, hx + r, y0 + 2 * r], fill=v)
    sh = y0 + 2 * r
    # a4: person과 같은 넓은 사다리꼴 몸을 위쪽만 옮겨 통째로 기울임 — a3 가는 몸통·막대 다리는 「가는 사람」으로 읽혀
    #     카드 체격 문구(넓은 어깨·통 몸통)가 화면 끝에 셋째 인물로 그려졌다(8/8). 발치는 person보다 조금 넓게(벌린 발).
    body(d, (hx - bw * 0.3, sh), (hx + bw * 0.3, sh), cx, y0, y1, bw * 1.2, v)
    return hx, r


def person_dodge(d, x0, y0, x1, y1, v):
    """task 400 a3 — 날아오는 것을 피하는 사람: 위몸을 화면 왼쪽(벽 쪽)으로 젖히고 두 발을 벌림."""
    leaning(d, x0, y0, x1, y1, v, -0.3)   # a5: 0.1은 곧게 펴짐(a4 순간 0) · b2: 0.18도 곧게 선 꼴(b1 피함이 보임 0) → 0.3


def person_throw(d, x0, y0, x1, y1, v):
    """task 400 — 막 던진 사람: 위몸을 화면 왼쪽(던진 쪽)으로 기울이고(a3) 어깨에서 왼쪽으로 곧게 뻗은 빈 팔(키의 0.30). 손끝 앞에 아무것도 없다(창은 따로 spear 꼴)."""
    hx, r = leaning(d, x0, y0, x1, y1, v, -0.18)   # a5: 0.1은 곧게 펴짐(a4 던진 자세 0)
    h, cx = y1 - y0, hx
    ay, arm = y0 + h * 0.2, h * 0.3   # 기운 몸만큼 팔을 줄여 손끝과 창 사이 틈을 지킴
    d.polygon([(cx, ay - r * 0.45), (cx - arm, ay - r * 0.35), (cx - arm, ay + r * 0.35), (cx, ay + r * 0.6)], fill=v)
    d.ellipse([cx - arm - r * 0.5, ay - r * 0.5, cx - arm + r * 0.5, ay + r * 0.5], fill=v)   # 편 손


def spear(d, x0, y0, x1, y1, v):
    """task 400 — 허공을 나는 창: 구역 세로 가운데 가는 자루 + 왼쪽 끝 뾰족한 촉 하나(날아가는 쪽)."""
    cy, t = (y0 + y1) / 2, max(2.0, (y1 - y0) * 0.18)
    tip = (x1 - x0) * 0.18   # a3: 촉을 키움(a2 촉 방향이 뒤집히거나 양쪽 촉)
    d.rectangle([x0 + tip, cy - t, x1, cy + t], fill=v)
    d.polygon([(x0, cy), (x0 + tip, cy - t * 3), (x0 + tip, cy + t * 3)], fill=v)


def wall(d, x0, y0, x1, y1, v):
    """task 400 — 인물 등 뒤에 붙은 옆벽: a3부터 원근 사다리꼴(가까운 왼쪽 가장자리가 위아래 끝까지, 먼 쪽은 짧게)
    — a2 화면 끝 꽉 찬 사각이 책 지면 여백·붉은 선으로 읽혔다."""
    h = y1 - y0
    d.polygon([(x0, y0), (x1, y0 + h * 0.18), (x1, y1 - h * 0.06), (x0, y1)], fill=v)


SHAPES = {"person": person, "person_throw": person_throw, "person_dodge": person_dodge, "spear": spear, "wall": wall, "person_bow": person_bow, "prostrate": prostrate, "kneel_bow": kneel_bow, "seated": seated, "crowd": crowd, "boat": boat, "bank": bank}


def make(spec):
    g, R = spec["guide"], spec["regions"]
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    hy = int(HORIZON * H)
    if g.get("backdrop") == "room":   # a3 실내 바탕: 바닥선 위를 먼 뒷벽(중간 깊이)으로 — 빈 검은 띠가 캡션 자리로 읽혔다(a2 4/8 글자)
        d.rectangle([0, 0, W, hy], fill=round(255 * ROOM_WALL))
    for y in range(hy, H):
        t = (y - hy) / (H - 1 - hy)
        d.line([(0, y), (W, y)], fill=round(255 * (GROUND[0] + t * (GROUND[1] - GROUND[0]))))
    build, knee = {}, set()
    if g.get("legs") == "costume":   # b2: 차림 문구가 무릎 길이면 그 인물 꼴에 무릎 아래 다리
        knee = {f["region"] for f in spec["figures"] if "knee-length" in (f.get("costume") or {}).get("en", "")}
    if g.get("body") == "card":
        import sys
        sys.path.insert(0, HERE)
        import derive_scene as ds
        build = {f["region"]: ds._cast_in_scene(f).get("card", {}).get("silhouette", {}).get("class") for f in spec["figures"]}
    for k in sorted(g["depth"], key=lambda k: (g["depth"][k], k)):
        x0, y0, x1, y1 = R[k]
        BODY["w"] = BUILD_WIDTH.get(build.get(k), 0.3)
        BODY["knee"] = k in knee
        SHAPES[g["shape"][k]](d, x0 * W, y0 * H, x1 * W, y1 * H, round(255 * g["depth"][k]))
    BODY["w"], BODY["knee"] = 0.3, False
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
