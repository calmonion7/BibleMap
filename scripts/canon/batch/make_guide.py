#!/usr/bin/env python3
"""task#388 — 구도 가이드(깊이) 그림: 장면 명세의 `regions`·`guide` 두 칸에서만 결정적으로 파생한다(같은 명세 → 같은 바이트).

  python3 batch/make_guide.py [--scene <장면 id>] [--out <png>]     # 기본: 요단 귀환 → samples/jordan-guide/guide.png

깊이 그림 = 가까움 밝게 · 멂 어둡게. 선을 주지 않고(ZIMAGE §2 「콘티 되그림」) 자리·크기·멀고 가까움만 준다.
꼴(guide.shape): person(서 있는 한 사람) · person_bow(고개를 앞·아래로 숙인 서 있는 사람, restyle r5) · kneel_bow(무릎 꿇고 엉덩이 들고 머리를 왼쪽 땅에, r6) · seated(배 안에 앉은 머리·어깨 한 줄, r6) · sit(걸상에 앉아 왼쪽을 향한 한 사람, task 414) · prostrate(엎드린 낮은 몸, 머리는 왼쪽 — 다윗 쪽) · crowd(작은 실루엣 두 줄) · boat(선체) · bank(강 너머 둑).
바탕: 하늘 0 · 땅은 지평선에서 아래로 0.12 → 0.5. 그리는 순서는 먼 것부터(깊이 오름차순).
지평선은 눈높이 카메라(task 409, 규칙 generate.eye-level-perspective): 가장 가까운 서 있는 인물의 발 y·화면 키·키 등급에서 파생(S.scene_horizon)."""
import argparse, json, os, sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import scale as S  # noqa: E402 — task 408 크기 숫자는 크기 기준표(scale.json)에서만
W, H = 1216, 640
GROUND = (0.12, 0.5)
PERSP = {"hy": S.v("perspective.horizon_default")}   # make()가 장면 지평선(화면 높이 비)으로 바꿈 — 무리 꼴 줄 높이가 발 y에서 읽음(꼴 함수 서명 유지, BODY와 같은 까닭)
ROOM_WALL = 0.12   # 실내 뒷벽 깊이(바닥 시작값과 같음 — 벽과 바닥이 이어짐)
# task 400 a5 — 몸 너비(키 비율)를 카드 체격(card.silhouette)에서: guide.body = "card"일 때만(옛 가이드 바이트 유지).
# a3·a4: 카드는 넓은 어깨·통 몸통인데 가이드 몸이 기본 너비면 체격 문구가 화면 끝 셋째 인물로 그려짐. 너비 값은 S.build_width(크기 기준표).
BODY = {"w": S.build_width(), "knee": False}   # make()가 인물마다 바꾸는 몸 너비·무릎 아래 다리 — 꼴 함수 서명(d, 상자, v)을 그대로 두려고 모듈 상태로 둠
KNEE = S.v("body.knee")   # 무릎 높이(키 비율, 머리 위끝부터)


def body(d, top_l, top_r, cx, y0, y1, bw, v):
    """몸통: 어깨(top_l~top_r)에서 발까지 넓어지는 사다리꼴. BODY["knee"]면(task 402 b2) 무릎까지만 사다리꼴, 무릎 아래는 벌린 두 다리
    — b1: 바닥까지 넓어지는 사다리꼴 실루엣이 곧 긴 로브라 「무릎 길이 튜닉」 문구를 이겼다(사울 긴 망토 8/8). 다리를 굵게 해 몸 덩어리 유지."""
    h, sh = y1 - y0, top_l[1]
    if not BODY["knee"]:
        d.polygon([top_l, top_r, (cx + bw / 2, y1), (cx - bw / 2, y1)], fill=v)
        return
    ky = y0 + h * KNEE
    tw = abs(top_r[0] - top_l[0]) / 2                     # 어깨 반폭
    kw = tw * 1.2                                         # b5: 무릎 반폭 ≈ 어깨 — 아래로 넓어지는 사다리꼴은 판초·망토로 그려짐(b4 사울 「판초 같은 긴 겉옷」)
    d.polygon([(top_l[0] - tw * 0.25, top_l[1]), (top_r[0] + tw * 0.25, top_r[1]), (cx + kw, ky), (cx - kw, ky)], fill=v)   # 어깨·소매 조금 넓게
    lw = bw * 0.34   # b5: 곧은 몸통으로 줄어든 덩어리를 다리로 메움(몸 덩어리 규칙)
    for s in (-1, 1):
        d.polygon([(cx + s * kw * 0.15 - lw / 2, ky), (cx + s * kw * 0.15 + lw / 2, ky), (cx + s * bw * 0.5 + lw / 2, y1), (cx + s * bw * 0.5 - lw / 2, y1)], fill=v)


HEAD_R = S.guide_head_r()   # 머리 반지름 = 구역 높이 × 이 값 — 지름 ≤ 0.14(규칙 generate.guide-head-ratio, d4)


def person(d, x0, y0, x1, y1, v):
    h, cx = y1 - y0, (x0 + x1) / 2
    bw = min(x1 - x0, h * BODY["w"])
    r = h * HEAD_R["person"]
    d.ellipse([cx - r, y0, cx + r, y0 + 2 * r], fill=v)
    sh = y0 + 2 * r
    body(d, (cx - bw * 0.3, sh), (cx + bw * 0.3, sh), cx, y0, y1, bw, v)


def person_bow(d, x0, y0, x1, y1, v):
    """restyle r5 — 고개를 앞(화면 오른쪽)·아래로 숙인 서 있는 사람: 몸은 person과 같고 머리 원이 어깨선 앞·아래, 목이 앞으로 기욺."""
    h, cx = y1 - y0, (x0 + x1) / 2
    bw = min(x1 - x0, h * BODY["w"])
    r = h * HEAD_R["person"]
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
    """작은 실루엣 두 줄. 줄 높이는 발 y에서(task 409, 규칙 generate.eye-level-perspective): 보통 키 어른 화면 키 = (발 y − 지평선) ÷ 눈높이 비.
    발이 지평선 위인 줄(강 건너 둑·언덕 — 평지 눈높이 셈 밖)은 옛 상자 비(뒷줄 0.558 · 앞줄 0.62 × 상자 높이)."""
    h = y1 - y0
    for row, (foot, old, val) in enumerate(((y0 + h * 0.62 * 0.9, h * 0.62 * 0.9, round(v * 0.92)), (y1, h * 0.62, v))):
        ph = S.screen_height(foot / H, PERSP["hy"]) * H if foot / H > PERSP["hy"] else old
        top = foot - ph
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
    bw, r, dx = min(x1 - x0, h * BODY["w"]), h * HEAD_R["person"], h * lean
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


def person_duck(d, x0, y0, x1, y1, v):
    """task 402 b3 — 날아오는 것 아래로 몸을 숙여 피하는 사람: 머리를 낮게 화면 왼쪽(벽 쪽)으로, 위몸을 앞으로 굽히고 무릎을 꺾음.
    b2: 기울인 꼴(person_dodge)은 「벽에 기대 섬」으로 옮겨져 피함이 안 보임(순간 0 · 피함이 보임 0). 몸 덩어리는 person만큼."""
    h, w = y1 - y0, x1 - x0
    bw, r = min(w, h * BODY["w"] * 1.55), h * HEAD_R["person_duck"]   # d4: 0.09(지름 0.18)는 그림이 선 꼴로 옮기면 머리 큰 아이 비율(d2·d3 「10세 안팎」) — 규칙 generate.guide-head-ratio
    hx = x0 + r * 1.1
    d.ellipse([hx - r, y0, hx + r, y0 + 2 * r], fill=v)                                  # 낮춘 머리(벽 쪽)
    hip_x, hip_y = x0 + w * 0.6, y0 + h * 0.55
    d.polygon([(hx - r * 0.2, y0 + r * 1.6), (hx + r * 1.4, y0 + r * 1.2), (hip_x + bw * 0.35, hip_y), (hip_x - bw * 0.35, hip_y + h * 0.08)], fill=v)   # 굽힌 위몸
    kx, ky = x0 + w * 0.95, y0 + h * 0.75
    d.polygon([(hip_x - bw * 0.3, hip_y), (hip_x + bw * 0.3, hip_y - h * 0.04), (kx, ky - h * 0.06), (kx - bw * 0.15, ky + h * 0.06)], fill=v)            # 앞 넓적다리
    d.polygon([(kx - bw * 0.4, ky - h * 0.02), (kx, ky - h * 0.04), (kx - w * 0.05, y1), (kx - w * 0.05 - bw * 0.4, y1)], fill=v)                    # 앞 정강이
    d.polygon([(hip_x - bw * 0.4, hip_y + h * 0.05), (hip_x, hip_y), (x0 + w * 0.32, y1), (x0 + w * 0.32 - bw * 0.4, y1)], fill=v)       # 뒤 다리


def sit(d, x0, y0, x1, y1, v):
    """task 414 — 걸상에 앉아 화면 왼쪽을 향한 사람(삼상 19:9 「그 집에 앉았을 때에」): 곧은 위몸, 왼쪽으로 뻗은 넓적다리, 바닥으로 내린 정강이, 걸상.
    구역 높이 = 앉은 키(서 있는 키 × body.seated, 규칙 generate.seated-height) — 머리·몸 너비는 서 있는 키로 셈."""
    h, w = y1 - y0, x1 - x0
    hs = h / S.v("body.seated")                        # 서 있는 키
    bw, r = min(w, hs * BODY["w"]), hs * HEAD_R["person"]
    sg = -1 if BODY.get("sit_right") else 1            # task 417: 화면 오른쪽을 보는 앉은 사람은 상자 안에서 좌우를 뒤집음(곁 장면 밧세바)
    cx = x0 + w * 0.62 if sg > 0 else x1 - w * 0.62
    d.ellipse([cx - r, y0, cx + r, y0 + 2 * r], fill=v)
    seat = y1 - hs * (1 - S.v("body.knee"))            # 걸상 높이 ≈ 무릎 높이
    knee, BODY["knee"] = BODY["knee"], False           # 위몸은 무릎 아래 다리 없이(다리는 아래 넓적다리·정강이)
    body(d, (cx - bw * 0.3, y0 + 2 * r), (cx + bw * 0.3, y0 + 2 * r), cx, y0, seat, bw * 0.8, v)    # 위몸
    BODY["knee"] = knee
    kx = cx - sg * hs * 0.25
    limb(d, (cx, seat - bw * 0.2), (kx, seat - bw * 0.2), bw * 0.45, v)                              # 넓적다리
    limb(d, (kx, seat - bw * 0.2), (kx - sg * bw * 0.1, y1 - bw * 0.1), bw * 0.32, v, bw * 0.24)    # 정강이
    d.rectangle([cx - bw * 0.35, seat, cx + bw * 0.35, y1], fill=round(v * 0.85))                  # 걸상


def person_throw(d, x0, y0, x1, y1, v):
    """task 400 — 막 던진 사람: 위몸을 화면 왼쪽(던진 쪽)으로 기울이고(a3) 어깨에서 왼쪽으로 곧게 뻗은 빈 팔(키의 0.30). 손끝 앞에 아무것도 없다(창은 따로 spear 꼴)."""
    hx, r = leaning(d, x0, y0, x1, y1, v, -0.18)   # a5: 0.1은 곧게 펴짐(a4 던진 자세 0)
    h, cx = y1 - y0, hx
    ay, arm = y0 + h * 0.2, h * 0.3   # 기운 몸만큼 팔을 줄여 손끝과 창 사이 틈을 지킴
    d.polygon([(cx, ay - r * 0.45), (cx - arm, ay - r * 0.35), (cx - arm, ay + r * 0.35), (cx, ay + r * 0.6)], fill=v)
    d.ellipse([cx - arm - r * 0.5, ay - r * 0.5, cx - arm + r * 0.5, ay + r * 0.5], fill=v)   # 편 손


def limb(d, p, q, w, v, w2=None):
    """팔다리 한 마디(p→q) — 굵기 w에서 w2(없으면 w)로 가늘어짐, 양끝 둥근 마디."""
    w2 = w if w2 is None else w2
    dx, dy = q[0] - p[0], q[1] - p[1]
    n = max(1e-6, (dx * dx + dy * dy) ** 0.5)
    ux, uy = -dy / n / 2, dx / n / 2
    d.polygon([(p[0] + ux * w, p[1] + uy * w), (q[0] + ux * w2, q[1] + uy * w2), (q[0] - ux * w2, q[1] - uy * w2), (p[0] - ux * w, p[1] - uy * w)], fill=v)
    for c, cw in ((p, w), (q, w2)):
        d.ellipse([c[0] - cw / 2, c[1] - cw / 2, c[0] + cw / 2, c[1] + cw / 2], fill=v)


def person_follow(d, x0, y0, x1, y1, v):
    """task 403 — 막 던진 뒤 몸이 따라 나간 사람(화면 왼쪽으로 던짐): 몸통이 앞으로 기울고, 체중이 굽힌 앞무릎에, 뒷다리는 뒤로 뻗고,
    던진 팔은 앞·아래로 휘둘러 내려오고, 다른 팔은 뒤로. b7 person_throw(큰 직사각 몸통 + 무릎에서 컴퍼스처럼 벌린 다리 + 어깨 높이로 곧게 뻗은
    막대 팔·편 손)가 그대로 그려져 사람 「사울 몸 비율·자세가 어색함」(가는 긴 다리 · 「멈춰」 손짓)."""
    h, cx = y1 - y0, (x0 + x1) / 2
    sw, lw, aw, r = h * BODY["w"] * 0.66, h * BODY["w"] * 0.44, h * BODY["w"] * 0.22, h * HEAD_R["person"]
    hip = (cx + h * 0.05, y0 + h * 0.55)
    sh = (hip[0] - h * 0.17, y0 + h * 0.2)                                                # 약 27° 앞으로(c3 42° 구부정 · c4 15° 서서 가리킴)
    hem = y0 + h * 0.7                                                                    # 무릎 길이 옷자락
    hd = (sh[0] - h * 0.06, y0 + h * 0.02 + r)
    d.ellipse([hd[0] - r, hd[1] - r, hd[0] + r, hd[1] + r], fill=v)                                     # 앞으로 내민 머리
    limb(d, hd, (sh[0], sh[1] + h * 0.02), aw, v)                                                        # 목
    knee = (hip[0] - h * 0.19, y0 + h * 0.75)
    limb(d, (hip[0] - h * 0.04, y0 + h * 0.6), knee, lw, v, lw * 0.7)                                    # 앞 넓적다리
    limb(d, knee, (hip[0] - h * 0.13, y1 - lw * 0.2), lw * 0.66, v, lw * 0.5)                            # 앞 정강이(무릎이 발보다 앞 — 체중 실린 굽힘)
    limb(d, (hip[0] + h * 0.04, y0 + h * 0.6), (hip[0] + h * 0.2, y1 - h * 0.05), lw, v, lw * 0.5)       # 뒷다리 곧게 뻗어 뒤꿈치 듦
    d.polygon([(sh[0] + sw * 0.5, sh[1] - h * 0.01), (sh[0] - sw * 0.5, sh[1] + h * 0.01),
               (hip[0] - sw * 0.55, hem), (hip[0] + sw * 0.5, hem)], fill=v)                           # 몸통·옷
    hand = (sh[0] - h * 0.25, sh[1] + h * 0.24)
    limb(d, (sh[0] - sw * 0.25, sh[1] + h * 0.02), hand, aw, v, aw * 0.8)                                # 던진 팔: 앞·아래로 휘둘러 내림(c3 s23 던진 몸짓 맞음 · c4 수평 = 가리킴)
    d.ellipse([hand[0] - aw * 0.6, hand[1] - aw * 0.6, hand[0] + aw * 0.6, hand[1] + aw * 0.6], fill=v)
    limb(d, (sh[0] + sw * 0.4, sh[1] + h * 0.02), (sh[0] + h * 0.24, sh[1] + h * 0.26), aw, v, aw * 0.8)   # 뒤 팔: 몸 뒤 아래로(균형)


def spear(d, x0, y0, x1, y1, v):
    """task 400 — 허공을 나는 창: 구역 세로 가운데 가는 자루 + 왼쪽 끝 뾰족한 촉 하나(날아가는 쪽)."""
    cy, t = (y0 + y1) / 2, max(2.0, (y1 - y0) * 0.18)
    tip = (x1 - x0) * (0.3 if BODY.get("big_tip") else 0.18)   # a3: 촉을 키움 · b6: big_tip이면 더 크게(b5 촉이 사울 쪽으로 뒤집힘 8장 거의 전부)
    d.rectangle([x0 + tip, cy - t, x1, cy + t], fill=v)
    k = 5 if BODY.get("big_tip") else 3
    if BODY.get("leaf_tip"):   # b7: 잎 모양(마름모 — 가장 넓은 곳이 촉 뒤쪽 1/3) — 삼각형은 미늘 달린 화살촉으로 그려짐(b6 s5 단 하나의 틀림)
        d.polygon([(x0, cy), (x0 + tip * 0.62, cy - t * k * 0.8), (x0 + tip, cy), (x0 + tip * 0.62, cy + t * k * 0.8)], fill=v)
    else:
        d.polygon([(x0, cy), (x0 + tip, cy - t * k), (x0 + tip, cy + t * k)], fill=v)


def wall(d, x0, y0, x1, y1, v):
    """task 400 — 인물 등 뒤에 붙은 옆벽: a3부터 원근 사다리꼴(가까운 왼쪽 가장자리가 위아래 끝까지, 먼 쪽은 짧게)
    — a2 화면 끝 꽉 찬 사각이 책 지면 여백·붉은 선으로 읽혔다."""
    h = y1 - y0
    d.polygon([(x0, y0), (x1, y0 + h * 0.18), (x1, y1 - h * 0.06), (x0, y1)], fill=v)


# task 403 c7 — 포즈(뼈대) 제어: OpenPose 18점 규약(controlnet_aux draw_bodypose와 같은 관절 순서·팔다리 짝·색).
# 깊이 꼴은 실루엣 덩어리만 주고 관절 각도·다리 길이는 모델이 시드마다 넓은 보폭으로 되돌렸다(c1~c6).
LIMBS = [(1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7), (1, 8), (8, 9), (9, 10), (1, 11), (11, 12), (12, 13), (1, 0), (0, 14), (14, 16), (0, 15), (15, 17)]
POSE_COLORS = [(255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0), (170, 255, 0), (85, 255, 0), (0, 255, 0), (0, 255, 85), (0, 255, 170),
               (0, 255, 255), (0, 170, 255), (0, 85, 255), (0, 0, 255), (85, 0, 255), (170, 0, 255), (255, 0, 255), (255, 0, 170), (255, 0, 85)]
# 관절(키 비율 — x: 엉덩이 가운데 기준, 음수 = 화면 왼쪽 · y: 머리 위끝 0 ~ 발 1). 어른 비율(엉덩이 0.52 · 무릎 0.73 · 발목 0.95).
POSES = {
    # 막 던진 뒤 몸이 따라 나감(화면 왼쪽으로 던짐 — 투창 마무리): 몸통 약 30° · 던진 오른팔 앞·아래로 길게 뻗음 · 왼팔 뒤 위로(균형) · 굽힌 왼 앞다리 한 발로 섬
    # · 오른 뒷다리를 땅에서 들어 뒤로 올림(c8 25° 곧게 펴짐 · c9 35°+팔 내림 = 구부정히 걷는 사람 — 기울기 대신 든 뒷발로 체중을 보임) · 왼발 앞으로 내디딤(무릎 굽힘)
    # 옆얼굴이라 가까운 오른 눈·귀만.
    # · d1·d2 뼈대(손목 더 아래 · 팔다리 곧게)는 한 장 근거(c14 s5)로 만든 규칙이라 「달리는 자세」(d1)·「늘어진 팔」(d2)을 낳음 → c10 꼴로 되돌림
    #   (묶음 기록: c10 가이드 던진 몸짓 c10 3/8 · c11 2/8 · c13 3/8 — d 시도 전 가장 좋음).
    # · f3: 반대 팔을 몸 뒤 아래로(f1e·f2e 뒤 위로 든 팔 + 몸 덩어리 = 「던지기 전 와인드업」) · 든 뒷발을 앞발 쪽으로 당겨 보폭 줄임(「컴퍼스 다리」 4~5/5)
    # · g2 던진 팔 앞무릎 쪽으로 내림은 되돌림(g2e 「아래로 늘어진 팔」 5/5 — d2와 같음): 팔을 내리면 늘어짐, 앞으로 두면 가리킴
    # · h3: 보폭 줄임 — 든 뒷발을 앞쪽·낮게, 앞발을 엉덩이 쪽으로(h2e·h2e2 같은 사울 화소가 「컴퍼스 다리」 2/5 ↔ 3/5 경계)
    # · h2(스텝별 가이드로 뼈대가 먹힘): 반대 팔을 몸통을 따라 곧게 늘어뜨려 몸에 가림(h1e 몸 뒤로 뻗은 팔 = 「양팔 벌린 멈춤 손짓」 5/5)
    "throw_follow": {0: (-0.23, 0.11), 1: (-0.15, 0.18), 2: (-0.14, 0.21), 3: (-0.28, 0.3), 4: (-0.41, 0.41), 5: (-0.17, 0.21), 6: (-0.11, 0.35),
                     7: (-0.07, 0.48), 8: (-0.01, 0.52), 9: (0.08, 0.68), 10: (0.15, 0.8), 11: (0.01, 0.52), 12: (-0.13, 0.73), 13: (-0.1, 0.96),
                     14: (-0.24, 0.095), 16: (-0.17, 0.1)},
    # task 404 g2 — 벽을 등지고 허리를 깊이 숙여(약 45°) 머리를 낮추고 무릎 굽힘 · 두 손목이 가슴 앞(화면 오른쪽을 봄) — 뼈대만 가이드용
    # (g1e: 가이드 없는 다윗은 문구대로 숙였으나 벽에서 떨어져 방 가운데·수금이 류트).
    "duck_low": {0: (0.27, 0.32), 1: (0.17, 0.33), 2: (0.19, 0.35), 3: (0.2, 0.47), 4: (0.25, 0.42), 5: (0.14, 0.33), 6: (0.12, 0.46),
                 7: (0.22, 0.43), 8: (0.03, 0.55), 9: (0.12, 0.74), 10: (0.05, 0.97), 11: (-0.03, 0.55), 12: (0.06, 0.75), 13: (-0.04, 0.97),
                 14: (0.26, 0.29), 16: (0.2, 0.29)},
    # task 404 f4 — 벽 앞에서 머리를 숙여 날아오는 것을 피하며 두 손으로 지물을 가슴에 쥠(화면 오른쪽을 봄): 무릎 굽힘 · 머리 앞·아래 ·
    # 두 손목이 가슴 가운데(규칙 generate.pose-hold — 깊이 꼴 숙인 다윗은 손 자리를 못 줘 f1e~f3e 「수금이 벽에 기대 있음」 5/5).
    "duck_clutch": {0: (0.08, 0.15), 1: (0.0, 0.21), 2: (0.06, 0.23), 3: (0.13, 0.34), 4: (0.07, 0.31), 5: (-0.06, 0.23), 6: (-0.01, 0.36),
                    7: (0.04, 0.32), 8: (0.04, 0.52), 9: (0.1, 0.73), 10: (0.05, 0.96), 11: (-0.04, 0.52), 12: (-0.01, 0.74), 13: (-0.1, 0.96),
                    14: (0.1, 0.13), 16: (0.03, 0.13)},
    # task 417 — 곧게 서서 화면 오른쪽 상대에게 말을 전함: 앞 팔을 가슴 높이로 상대 쪽에 내밀어 손을 폄 · 뒤 팔은 옆에 내림
    # (시도 2 s42: 문구 「one empty hand open toward the king」만으로는 두 팔이 내려간 채 — 사람 「이야기하는 모습으로 보이려면 손짓」).
    "speak_open": {0: (0.05, 0.065), 1: (0.0, 0.14), 2: (0.05, 0.165), 3: (0.14, 0.25), 4: (0.23, 0.27), 5: (-0.05, 0.165), 6: (-0.06, 0.3),
                   7: (-0.05, 0.42), 8: (0.03, 0.52), 9: (0.03, 0.74), 10: (0.03, 0.97), 11: (-0.03, 0.52), 12: (-0.03, 0.74), 13: (-0.04, 0.97),
                   14: (0.045, 0.05), 16: (0.0, 0.055)},
    # task 417 — 곧게 서서 화면 오른쪽 상대에게 두 손을 내밀어 애원함: 두 팔을 가슴 높이로 앞으로 뻗어 두 손목을 나란히(두 여인 참 어머니 왕상 3:26 — 넓힌 pose-hold에 걸림).
    "plead_out": {0: (0.05, 0.065), 1: (0.0, 0.14), 2: (0.05, 0.165), 3: (0.13, 0.25), 4: (0.22, 0.29), 5: (-0.05, 0.165), 6: (0.06, 0.27),
                  7: (0.18, 0.31), 8: (0.03, 0.52), 9: (0.03, 0.74), 10: (0.03, 0.97), 11: (-0.03, 0.52), 12: (-0.03, 0.74), 13: (-0.04, 0.97),
                  14: (0.045, 0.05), 16: (0.0, 0.055)},
    # task 417 — 곧게 서서 화면 왼쪽 상대의 말을 들음: 두 손목을 몸 앞 허리 높이에 모음(문구 「both empty hands clasped before him」만으로는 팔이 내려감).
    # task 421 — 손목이 허리 아래(0.40)·팔꿈치가 몸에 붙은 꼴은 s42에서 한 손을 내민 손으로 그려짐 → 두 손목을 몸 앞 배 높이(0.35)에 붙이고 팔꿈치를 벌림.
    "listen_clasp": {0: (-0.05, 0.065), 1: (0.0, 0.14), 2: (-0.05, 0.165), 3: (-0.1, 0.27), 4: (-0.07, 0.345), 5: (0.05, 0.165), 6: (0.05, 0.28),
                     7: (-0.06, 0.35), 8: (-0.03, 0.52), 9: (-0.03, 0.74), 10: (-0.04, 0.97), 11: (0.03, 0.52), 12: (0.03, 0.74), 13: (0.04, 0.97),
                     14: (-0.045, 0.05), 16: (0.0, 0.055)},
    # task 424 — 걸상에 앉아 갓난 아기를 두 팔로 가슴에 안음(화면 오른쪽을 봄 · 상자 = 앉은 키, sit 꼴 sit_right와 같은 자리: 위몸 상자 가운데 −0.17 ·
    # 걸상 0.62 · 무릎 오른쪽 앞): 두 팔꿈치를 굽혀 허리 위에 두고 두 손목을 가슴 앞(0.33~0.36)에 — 사전 hold 문구만으로는 아기가 무릎·허리에 누움(곁 순간 421 2/8 · 422 4/8).
    # 고개를 숙여 아기를 내려다봄.
    "cradle_sit": {0: (-0.1, 0.115), 1: (-0.17, 0.19), 2: (-0.12, 0.22), 3: (-0.1, 0.42), 4: (-0.01, 0.36), 5: (-0.22, 0.22), 6: (-0.2, 0.4),
                   7: (-0.07, 0.33), 8: (-0.14, 0.62), 9: (0.17, 0.62), 10: (0.19, 0.97), 11: (-0.2, 0.62), 12: (0.13, 0.63), 13: (0.15, 0.97),
                   14: (-0.12, 0.09), 16: (-0.18, 0.085)},
    # task 424 — 곧게 서서 갓난 아기를 두 팔로 가슴에 안음(화면 오른쪽을 봄): 두 팔꿈치를 굽혀 허리 위에 두고 두 손목을 가슴 앞(0.25~0.27)에 · 고개는 듦(두 여인 다른 계집 — 참 어머니를 봄).
    "cradle_stand": {0: (0.05, 0.065), 1: (0.0, 0.14), 2: (0.05, 0.165), 3: (0.06, 0.31), 4: (0.14, 0.27), 5: (-0.05, 0.165), 6: (-0.04, 0.3),
                     7: (0.09, 0.25), 8: (0.03, 0.52), 9: (0.03, 0.74), 10: (0.03, 0.97), 11: (-0.03, 0.52), 12: (-0.03, 0.74), 13: (-0.04, 0.97),
                     14: (0.045, 0.05), 16: (0.0, 0.055)},
}


def pose_points(box, name, hip_dx=0.06):
    """뼈대 관절 화소 자리 — 키 = 상자 높이, 엉덩이 가운데 x = 상자 가운데 + hip_dx·키."""
    x0, y0, x1, y1 = box
    h, cx = y1 - y0, (x0 + x1) / 2 + hip_dx * (y1 - y0)
    return {k: (cx + x * h, y0 + y * h) for k, (x, y) in POSES[name].items()}, h


# task 404 f1 — 뼈대 인물의 몸 덩어리(규칙 generate.pose-body-mass): 뼈대만 주면 몸 너비 제한이 없어 카드 체형 낱말(「thick barrel torso」)이
# 부풀려짐(비율 문항 사울: 깊이 꼴 c5 5/8 · 뼈대 c11 1/8). 뼈대를 따라 깊이 몸(몸통 = 카드 너비, 팔다리 = 키 비율)을 함께 그린다.
LIMB_W = {(2, 3): 0.065, (3, 4): 0.05, (5, 6): 0.065, (6, 7): 0.05, (8, 9): 0.09, (9, 10): 0.065, (11, 12): 0.09, (12, 13): 0.065}


def pose_body(d, box, name, v, bw, knee=False):
    """뼈대 관절을 따라 깊이 몸: 몸통 사각(어깨 반폭 0.3·bw·키, 엉덩이 0.25) · 머리 원(HEAD_R person) · 팔다리 굵은 선(LIMB_W·키)
    · knee(무릎 길이 차림)면 엉덩이 ~ 무릎 치마 덩어리(f4 — 몸이 엉덩이에서 끝나면 튜닉이 짧게 그려져 「다리가 길고 가늚」 f1e~f3e, generate.guide-costume-legs)."""
    pts, h = pose_points(box, name)
    if knee:
        hx0 = (pts[8][0] + pts[11][0]) / 2
        hy0 = (pts[8][1] + pts[11][1]) / 2
        ky = (pts[9][1] + pts[12][1]) / 2
        hw0, kw = bw * h * 0.25, bw * h * 0.32   # 엉덩이 아래로 곧게(f4 가이드: 든 뒷무릎까지 퍼지면 망토 꼴)
        d.polygon([(hx0 - hw0, hy0), (hx0 + hw0, hy0), (hx0 + kw, ky), (hx0 - kw, ky)], fill=v)
    nx, ny = pts[1]
    hx, hy = ((pts[8][0] + pts[11][0]) / 2, (pts[8][1] + pts[11][1]) / 2)
    ax, ay = hx - nx, hy - ny
    n = max(1e-6, (ax * ax + ay * ay) ** 0.5)
    px, py = -ay / n, ax / n
    sw, hw = bw * h * 0.3, bw * h * 0.25   # 어깨·엉덩이 반폭 — person 꼴(body 어깨 ±0.3·bw)과 같은 기준
    d.polygon([(nx + px * sw, ny + py * sw), (hx + px * hw, hy + py * hw), (hx - px * hw, hy - py * hw), (nx - px * sw, ny - py * sw)], fill=v)
    r = h * HEAD_R["person"]
    cxh, cyh = (pts[0][0] + pts[16][0]) / 2, (pts[0][1] + pts[16][1]) / 2
    d.ellipse([cxh - r, cyh - r, cxh + r, cyh + r], fill=v)
    for (a, b), w in LIMB_W.items():   # f2 팔다리 × 카드 너비는 되돌림 — 굵은 팔 덩어리가 뒤로 든 팔을 「던지기 전」으로 보이게 함(f2e 5표 던진 몸짓 5/5 틀림)
        if a in pts and b in pts:
            d.line([pts[a], pts[b]], fill=v, width=max(2, round(w * h)))
            for q in (pts[a], pts[b]):
                rr = w * h / 2
                d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], fill=v)
    for a in (2, 5):   # 어깨에서 팔 시작까지
        d.line([pts[1], pts[a]], fill=v, width=max(2, round(0.065 * h)))


def draw_pose(img, box, name, hip_dx=0.06):
    """상자(x0, y0, x1, y1 화소) 안에 뼈대: 키 = 상자 높이, 엉덩이 가운데 x = 상자 가운데 + hip_dx·키. 굵기는 키에 비례(512px 사람 ≈ 4px)."""
    pts, h = pose_points(box, name, hip_dx)
    sw = max(2.0, h / 512 * 4 * 1.6)
    layer = Image.new("RGB", img.size, (0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i, (a, b) in enumerate(LIMBS):
        if a in pts and b in pts:
            (xa, ya), (xb, yb) = pts[a], pts[b]
            dx, dy = xb - xa, yb - ya
            n = max(1e-6, (dx * dx + dy * dy) ** 0.5)
            ox, oy = -dy / n * sw, dx / n * sw
            d.polygon([(xa + ox, ya + oy), (xb + ox, yb + oy), (xb - ox, yb - oy), (xa - ox, ya - oy)], fill=tuple(int(c * 0.6) for c in POSE_COLORS[i]))
    for k, (x, y) in pts.items():
        d.ellipse([x - sw, y - sw, x + sw, y + sw], fill=POSE_COLORS[k])
    mask = layer.convert("L").point(lambda p: 255 if p else 0)
    img.paste(layer, (0, 0), mask)
    return img


AIR_SHAPES = {"spear"}   # 허공을 나는 물체 꼴(recheck.AIR_SHAPES와 같음)
SHAPES = {"person": person, "person_throw": person_throw, "person_follow": person_follow, "person_dodge": person_dodge, "person_duck": person_duck, "spear": spear, "wall": wall, "person_bow": person_bow, "prostrate": prostrate, "kneel_bow": kneel_bow, "seated": seated, "sit": sit, "crowd": crowd, "boat": boat, "bank": bank}


def make_pose_only(spec, backdrop=False):
    """task 404 g1 — 뼈대만 가이드(규칙 generate.pose-only-control): 검은 바탕에 허공 물체 꼴(또렷하게) + 뼈대만, 깊이 그림을 섞지 않는다.
    진단(gibeah-pose-diag P1·P2): 깊이+뼈대 한 장은 깊이 실루엣이 선 사람으로 그려지고 뼈대가 약함 — 뼈대만이면 사울 몸통이 기울고
    가이드 없는 다윗은 문구대로 숙임. 뼈대 없는 인물·벽·바탕은 문구에 맡긴다."""
    g, R = spec["guide"], spec["regions"]
    if backdrop:   # m4 스텝별 1단계: 방 바탕(벽·바닥·옆벽 깊이) + 창 + 뼈대, 사람 깊이 몸은 뺌 — 검은 바탕은 방 구조 없이 시작해 액자·서명(m2e·m3e 16장 중 6)
        import copy
        s2 = copy.deepcopy(spec)
        g2 = s2["guide"]
        g2.pop("split", None), g2.pop("control", None)
        for k in [k for k, v in g2["shape"].items() if str(v).startswith("person")] + list(g2.get("pose", {})):
            g2["depth"].pop(k, None)
        g2["pose"] = {}
        out = make(s2)
        for k, name in sorted(g.get("pose", {}).items()):
            x0, y0, x1, y1 = R[k]
            draw_pose(out, (x0 * W, y0 * H, x1 * W, y1 * H), name)
        return out
    layer = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(layer)
    if g.get("tip") in ("big", "leaf"):
        BODY["big_tip"], BODY["leaf_tip"] = True, g["tip"] == "leaf"
    for k in g["shape"]:
        if g["shape"][k] in AIR_SHAPES:
            x0, y0, x1, y1 = R[k]
            SHAPES[g["shape"][k]](d, x0 * W, y0 * H, x1 * W, y1 * H, 255)
    BODY.pop("big_tip", None)
    BODY.pop("leaf_tip", None)
    out = layer.convert("RGB")
    for k, name in sorted(g.get("pose", {}).items()):
        x0, y0, x1, y1 = R[k]
        draw_pose(out, (x0 * W, y0 * H, x1 * W, y1 * H), name)
    return out


def make(spec, stage=1):
    """가이드 그림. guide.split(task 404 h1 — 규칙 generate.split-control)이면 stage 1 = 뼈대만(자세), stage 2 = 깊이(몸 덩어리·벽·바탕, 뼈대 선 없음)."""
    g, R = spec["guide"], spec["regions"]
    if g.get("control") == "pose":
        return make_pose_only(spec)
    if g.get("split") and stage == 1:
        return make_pose_only(spec, backdrop=True)
    skel = not g.get("split")   # stage 2: 뼈대 인물은 뼈대를 따른 깊이 몸만
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    PERSP["hy"] = S.scene_horizon(spec)
    hy = int(PERSP["hy"] * H)
    if g.get("backdrop") == "room":   # a3 실내 바탕: 바닥선 위를 먼 뒷벽(중간 깊이)으로 — 빈 검은 띠가 캡션 자리로 읽혔다(a2 4/8 글자)
        d.rectangle([0, 0, W, hy], fill=round(255 * ROOM_WALL))
    for y in range(hy, H):
        t = (y - hy) / (H - 1 - hy)
        d.line([(0, y), (W, y)], fill=round(255 * (GROUND[0] + t * (GROUND[1] - GROUND[0]))))
    if g.get("tip") in ("big", "leaf"):
        BODY["big_tip"] = True
        BODY["leaf_tip"] = g["tip"] == "leaf"
    build, knee = {}, set()
    if g.get("legs") == "costume":   # b2: 차림 문구가 무릎 길이면 그 인물 꼴에 무릎 아래 다리
        knee = {f["region"] for f in spec["figures"] if "knee-length" in (f.get("costume") or {}).get("en", "")}
    if g.get("body") == "card":
        import sys
        sys.path.insert(0, HERE)
        import derive_scene as ds
        build = {f["region"]: ds._cast_in_scene(f).get("card", {}).get("silhouette", {}).get("class") for f in spec["figures"]}
    facing = {f["region"]: f.get("screen_facing") for f in spec.get("figures") or []}   # task 417: sit 꼴 방향
    pose = g.get("pose", {})   # task 403 c7 — 뼈대로 줄 인물은 깊이 꼴을 그리지 않는다(흐림 뒤 draw_pose)
    air = [k for k in g["depth"] if g["shape"][k] in AIR_SHAPES]   # d2 — 허공 물체는 흐림 뒤에 또렷하게(d1 흐린 촉 → 창 방향 뒤집힘·화살촉)
    for k in sorted(g["depth"], key=lambda k: (g["depth"][k], k)):
        if k in air:
            continue
        if k in pose and g["shape"][k] != "sit":   # f1: 뼈대 인물도 뼈대를 따른 깊이 몸(카드 너비) — 뼈대는 흐림 뒤에 위에 그림 · 앉은 인물은 걸상째 sit 꼴(task 424)
            x0, y0, x1, y1 = R[k]
            pose_body(d, (x0 * W, y0 * H, x1 * W, y1 * H), pose[k], round(255 * g["depth"][k]), S.build_width(build.get(k)), k in knee)
            continue
        x0, y0, x1, y1 = R[k]
        BODY["w"] = S.build_width(build.get(k))
        BODY["knee"] = k in knee
        BODY["sit_right"] = facing.get(k) == "right"
        SHAPES[g["shape"][k]](d, x0 * W, y0 * H, x1 * W, y1 * H, round(255 * g["depth"][k]))
    BODY["w"], BODY["knee"], BODY["sit_right"] = S.build_width(), False, False
    img = img.filter(ImageFilter.GaussianBlur(g.get("blur", 3)))   # b6: blur 키우면 각진 몸이 누그러짐(b5 사울 상자 튜닉)
    d = ImageDraw.Draw(img)
    for k in air:
        x0, y0, x1, y1 = R[k]
        SHAPES[g["shape"][k]](d, x0 * W, y0 * H, x1 * W, y1 * H, round(255 * g["depth"][k]))
    BODY.pop("big_tip", None)
    BODY.pop("leaf_tip", None)
    out = img.convert("RGB")
    for k, name in sorted(pose.items()) if skel else ():
        x0, y0, x1, y1 = R[k]
        draw_pose(out, (x0 * W, y0 * H, x1 * W, y1 * H), name)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", default="authored-david-returns-jerusalem")
    ap.add_argument("--out", default=os.path.join(HERE, "samples", "jordan-guide", "guide.png"))
    ap.add_argument("--stage", type=int, default=1)   # guide.split 장면의 둘째 가이드(깊이)는 --stage 2
    a = ap.parse_args()
    spec = json.load(open(os.path.join(HERE, "scenes", f"{a.scene}.json"), encoding="utf-8"))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    make(spec, a.stage).save(a.out, format="PNG")
    print(f"[MakeGuide] {a.out}")


if __name__ == "__main__":
    main()
