#!/usr/bin/env python3
"""본문 기반 단계 인페인팅 장면 생성기 (2026-08-31, 사용자 재설계 지시).

**콘티를 쓰지 않는다.** 사용자 지시: 「콘티 사용하지말자 / 장면에 사용할 설명을 성경 내용을
충실히 만든 다음 / 토큰한계를 고려하여 프롬프트를 만들고 프롬프팅 순서를 정하고 인페인팅
방법으로 그림제작 / 1. 프롬프팅 → 그림1번 / 2. 1번그림, 프롬프팅 → 그림2번 / …」

**왜 이 구조인가 — 실측이 강제한다.**
  · 단일 프롬프트는 77토큰이라 장면 서술을 못 담는다. 골리앗 전신이 74/77이어서 방향을 두
    단어(`facing left`)밖에 못 실었고, 상세 후보는 79/77로 기각된 기록이 있다(§9-39).
    **단계마다 77이 새로 생기므로** 여덟 단계로 나누면 예산이 74 → 합계 444가 된다.
  · 콘티(ControlNet)는 「있고 없음」은 나르지만 「모양·방향」은 못 나른다(§9-32). 대신 정면 원
    머리가 시선을 못박는 대가를 치렀다. 텍스트 단계화는 그 대가 없이 서술을 싣는다.
  · 콘티를 빼면 판정 축 C·D·G가 파생원을 잃는다(§9-33의 소거 실험). 그 대체는 이 파일의
    `REGIONS`다 — 콘티도 사람이 저작한 것이었으므로 저작 층이 바뀐 것이고, 축 B·E·F가 쓰던
    인물창·머리밴드·몸통밴드는 여기서 다시 파생할 수 있다.

장면 명세는 `notes/SCENE-1SAM17.md`가 진다 — **요소마다 출처 절이 달려 있다.** 이 파일은
그 명세의 구역과 순서를 코드로 옮긴 것이고, 새 서술을 발명하지 않는다.

Usage:
  .../python gen_scripture_scene.py --scene <id> --seeds 11,42,7 [--stages S1,S2,...] [--label v1]
  (<id> = scripts/canon/scenes/<id>.json — 장면 명세. 재현 명령은 notes/SCENE-1SAM17.md §0)
"""
import argparse
import os
import sys
import time

import numpy as np
import torch
from diffusers import StableDiffusionXLInpaintPipeline
from PIL import Image, ImageDraw, ImageFilter

import params

sys.path.insert(0, params.CANON_DIR)
import derive_prompts as dp  # noqa: E402
import derive_scene as ds  # noqa: E402  — 장면 명세 → 구역·단계·프롬프트
import judge_scene as J  # noqa: E402  — 판정자와 **같은 하늘선 산식**을 쓴다(자와 그림이 어긋나면 안 된다)

OUT = os.path.join(params.OUT_ROOT, "scripture-scene")
W, H = params.SCENE_SIZE
# **단계별 strength** — 이음매와 「그린 것의 세기」가 상반된다(2026-09-01 실측, notes §12 판별표).
# 이미 그려진 지형 위에 **큰 상자**를 얹는 단계는 0.99면 상자 안 배경까지 새로 칠해 변화 마스크가
# 상자 전체가 되고, 그 테두리가 직사각 잔상으로 붙는다(언덕오른쪽 .989 · 거인 .542).
# 낮추면 아래를 보고 이어 그린다. 다만 **작은 상자까지 낮추면 인물이 지워진다**(다윗 잉크 .093→.035).
STRENGTH_BY_STAGE = {
    "S1":  0.99,   # 빈 종이색 캔버스에서 시작 — 통째로 새로 그린다
    "S1b": 0.95,   # 언덕은 **지형을 바꿔야** 하므로 이어붙임보다 세기가 우선(이음매 여유 .148~.204)
    "S1c": 0.95,
    "S2a": 0.85,   # 능선 위 군중 — 이어 그려야 배경이 안 갈라진다
    "S2b": 0.85,
    "S3":  0.85,   # 거인 상자가 가장 커서 이음매가 가장 잘 난다
    "S4":  0.99,   # 작은 상자 — 0.85까지 낮추면 **사라진다**(다윗 잉크 .093→.035, v21).
    "S5":  0.99,   # ⚠ 0.93으로 낮춰 봤다(v30): 이음매는 .342 → .403으로 **악화**했고 화풍만
                   # 좋아졌다(비 1.27 → 1.12). 이 둘의 이음매는 strength로 안 잡힌다.
}
DEFAULT_STRENGTH = 0.99
REFINE_STRENGTH = 0.72   # v12까지 0.55로는 고개를 못 돌렸다(다윗이 숙인 채였다).
                         # **이미 있는 것을 다듬는 단계**(얼굴). 1에 가까우면 모델이 그 자리에
                         # 새 그림을 그려 얼굴이 둘이 된다(2026-08-31 v4 실측: 다윗 얼굴이 별도의
                         # 큰 초상으로 생겼다). 낮은 strength가 「고치기」의 도구다.
FEATHER = 0.06           # 마스크 깃털 = 구역 짧은 변의 분율. 고정 px는 큰 구역에서 상자 변을
                         # 드러낸다(머리 단계 실측: 고정 6px에서 네모 이음매가 보였다).

# --- 구역·단계·문구는 **장면 명세**가 진다(task 330). ---------------------------------
# `scenes/<id>.json`을 `derive_scene`이 읽어 구역 상자·단계 순서·완성 프롬프트를 파생한다 — 좌표와
# 문구가 있는 곳은 명세 한 곳뿐이고, 판정자(`judge_scene`)도 같은 명세를 읽는다. 여기 남는 것은
# 장면과 무관한 **기전 상수**(strength·깃털·판 컷·배율 기준)다. 삼상17에 붙어 있던 실측 주석 원문은
# `notes/SCENE-1SAM17.md` §22.
# 단계 종류(kind): full(캔버스 통째) · region(상자 마스크) · ridge(하늘선 띠 마스크) · plate(판으로
# 그려 오려 붙임) · refine(있는 것을 다듬음 — REFINE_STRENGTH) · prop(인물 단계 `from`에서 파생한 손 근처 지물 띠). `skip`이 있으면 건너뛴다.
# 순서는 명세가 정한다 — **먼 것 → 가까운 것, 큰 것 → 작은 것**(뒤 단계가 앞을 덮으므로 원근과
# 가림이 저절로 맞는다).
ST, NEG = ds.ST, ds.NEG
REGIONS = {}   # main()이 명세에서 채운다 — 모듈 상수가 아니라 장면의 값이다



def box_px(name):
    x0, y0, x1, y1 = REGIONS[name]
    return (int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H))


def region_mask(name):
    """구역 마스크 — 상자 + 깃털. 깃털은 구역 짧은 변에서 판다(고정 px는 큰 구역에서 변이 드러난다)."""
    b = box_px(name)
    m = Image.new("L", (W, H), 0)
    m.paste(255, b)
    f = max(4, int(round(FEATHER * min(b[2] - b[0], b[3] - b[1]))))
    return m.filter(ImageFilter.GaussianBlur(f))


# --- 장면 안 인물 인페인팅(task 337) — 판 합성과 **나란히 있는 선택지**다 -----------------
# 기본값은 여전히 판 합성이다. 봉인된 삼상17 v41이 그 위에 서 있고, `--figures inscene`을
# 주지 않으면 이 아래 것은 하나도 실행되지 않는다.
SCENE_FIG_STRENGTH = 0.85   # 판 0.99(빈 종이)와 접지 0.55(있는 것 다듬기) 사이. --fig-strength로 훑는다.
ELLIPSE_FEATHER = 0.06      # 타원 합집합 마스크의 깃털(구역 짧은 변의 분율)


def union_box(names):
    bs = [box_px(n) for n in names]
    return (min(b[0] for b in bs), min(b[1] for b in bs),
            max(b[2] for b in bs), max(b[3] for b in bs))


def ellipse_mask(names):
    """인물 구역마다 **내접 타원**을 그려 합치고 깃털을 준다.

    사각 구역 마스크가 낸 결함을 겨눈다. 아래 붙임은 이미 변화 마스크(실루엣)로 하는데,
    그 실루엣이 **상자 선에서 잘리고** 그 단차가 C3 이음매로 남았다(v25 0.232 → v26 0.365 회귀,
    손잡이 넷 전부 실패 — ADR 260902-193724). 곡선 경계에는 잘릴 직선 변이 없다."""
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    boxes = sorted((box_px(n) for n in names), key=lambda b: b[0])
    short = min(min(b[2] - b[0], b[3] - b[1]) for b in boxes)
    for b in boxes:
        d.ellipse(b, fill=255)
    # **그룹이면 타원 사이를 잇는다.** 두 사람이 닿는 자리가 바로 그 틈이라, 이어 두지 않으면
    # 손이 닿을 자리에 칠할 수가 없다 — 구멍 난 마스크는 판 합성의 결함을 그대로 재현한다.
    # 잇는 것도 타원이다(직선 변을 새로 들이지 않는다). 높이는 인물 상자 높이의 60%,
    # 즉 손과 팔이 오가는 중간 높이다.
    for p, q in zip(boxes, boxes[1:]):
        cy = (p[1] + p[3] + q[1] + q[3]) // 4
        hh = int(round(0.30 * max(p[3] - p[1], q[3] - q[1])))
        d.ellipse((min(p[0], q[0]), cy - hh, max(p[2], q[2]), cy + hh), fill=255)
    return m.filter(ImageFilter.GaussianBlur(max(4, int(round(ELLIPSE_FEATHER * short)))))


def anchor_kwargs(pipe, casts, cast_region, win, gw, gh, state):
    """승인된 동결 얼굴을 IP-Adapter 레퍼런스로 물린다 — ADR 260904-055320 2항의 게이트는
    2/7에서 이미 통과했고(27명 승인) 배선만 없었다.

    둘 이상이면 **지역 IP 마스크**로 인물마다 자기 구역에만 건다. 한 어댑터에 이미지를 둘 주면
    얼굴이 섞이기 때문이다. 마스크 경로가 이 diffusers에서 실패하면 앵커를 끄고 어휘로 간다
    — 조용히 섞인 얼굴을 내놓느니 대조군 쪽으로 물러난다. → (kwargs, 로그 문구)"""
    use = []
    for cid in casts:
        c = ds.load_cast(cid)
        pl = c.get("plate", {})
        fp = os.path.join(params.CANON_DIR, "frozen", f"{cid}.png")
        if pl.get("anchor") and os.path.exists(fp):
            use.append((cid, fp, float(pl.get("ipScale", 0.25))))
    if not use:
        if state.get("n") and hasattr(pipe, "unload_ip_adapter"):
            pipe.unload_ip_adapter()
            state["n"] = 0
        return {}, "앵커 없음(보류이거나 동결 얼굴 없음)"
    if state.get("n") != len(use):
        if state.get("n") and hasattr(pipe, "unload_ip_adapter"):
            pipe.unload_ip_adapter()
        pipe.load_ip_adapter(params.IP_ADAPTER_REPO,
                             subfolder=[params.IP_ADAPTER_SUBFOLDER] * len(use),
                             weight_name=[params.IP_ADAPTER_WEIGHT] * len(use))
        state["n"] = len(use)
    pipe.set_ip_adapter_scale([sc for _, _, sc in use])
    kw = {"ip_adapter_image": [Image.open(fp).convert("RGB") for _, fp, _ in use]}
    note = " · ".join(f"{cid} 앵커 {sc}" for cid, _, sc in use)
    if len(use) > 1:
        try:
            from diffusers.image_processor import IPAdapterMaskProcessor
            masks = []
            for cid, _, _ in use:
                mm = Image.new("L", (W, H), 0)
                ImageDraw.Draw(mm).ellipse(box_px(cast_region[cid]), fill=255)
                masks.append(mm.crop(win))
            # preprocess는 (N, 1, h, w)를 준다. 어댑터가 N개면 **어댑터마다 한 항목**이어야 하고
            # 각 항목이 (그 어댑터가 받는 이미지 수, 1, h, w)다 — 하나로 뭉치면 diffusers가
            # 「마스크 1개인데 스케일 2개」라고 거절한다(2026-09-05 실측).
            pm = IPAdapterMaskProcessor().preprocess(masks, height=gh, width=gw)
            kw["cross_attention_kwargs"] = {
                "ip_adapter_masks": [pm[i:i + 1] for i in range(pm.shape[0])]}
            note += " · 지역 마스크"
        except Exception as e:                                   # noqa: BLE001
            if hasattr(pipe, "unload_ip_adapter"):
                pipe.unload_ip_adapter()
            state["n"] = 0
            return {}, f"앵커 끔 — 지역 마스크 실패({type(e).__name__}: {e})"
    return kw, note


# **인물은 장면 안에서 그리지 않고 「판」으로 따로 그려 오려 붙인다**(2026-09-01 사용자 제안, 실측 확인).
# 상자 인페인팅의 두 결함이 여기서 함께 사라진다:
#   ① 자세가 지형에 끌려간다 — 가파른 비탈 위 상자를 채우려 골리앗이 웅크리거나 누웠다(v26·v29·v30).
#   ② 상자 변이 잔상으로 남는다 — 모델이 상자 안 배경까지 새로 지으니 붙임 마스크가 사각형이 된다.
# 민 종이 위에서는 모델이 지형과 싸우지 않고, 붙임 마스크가 **인물 실루엣**이라 변이 없다.
# 캔버스는 params.SAMPLE_SIZE(832x1216) — 「가로 캔버스로 단독 전신을 뽑으면 모델이 장면을
# 구성해 버린다」는 2026-08-26 실측이 그 주석에 이미 있다.
PAPER = (247, 240, 226)   # 종이색 — 캔버스 바탕이자 판의 배경(오려내기 기준)
PLATE_BG = " plain empty paper background."
PLATE_NEG = ", landscape, hills, sky, ground, scenery, shadow"
PLATE_STRENGTH = 0.99   # 판은 빈 종이에서 시작하므로 통째로 새로 그린다
PLATE_CUT = 20   # 종이색과의 차이가 이보다 크면 인물. ⚠ 10에서는 **판 전체가 잡힌다**(옅은 배경
                 # 얼룩). 반대로 너무 높이면 v5의 「옅게 그려진 골리앗을 통째로 버림」이 재현된다.
# **창을 전체 캔버스로 주는 단계.** 규칙 ③(창 ≠ 마스크)의 또 다른 적용 — 능선 띠를 1024로 확대해
# 생성하면 「멀리 작은 병사」를 그리라 해도 **큰 병사**가 나온다(v9~v17). 창을 화면 전체로 주면
# 모델이 장면 배율을 보고 그 안에서 작게 그린다. 마스크는 여전히 능선 띠다.
# ⚠ v18 실측 — 전체 창을 주자 S2가 **아무것도 안 그렸다**(구역 창에서는 큰 병사가 나왔다).
# 「멀리 작은 군중」은 이 두 손잡이 사이에 답이 없다. **미해결로 남긴다** — 비워 두면 구역 창이다.
CONTEXT_FULL = set()   # 다듬는 단계 — REFINE_STRENGTH를 쓴다
PAD = 0.10        # 구역 둘레 맥락 여백(구역 짧은 변의 분율) — 모델이 이어붙일 주변을 봐야 한다.
                  # ⚠ 0.40으로 올려 봤다(2026-09-01): 이음매가 0.989 → 0.375로 줄었지만 **판당
                  # 6분 → 11분**이 됐고, 아래 가중치 붙임이 같은 결함을 원가 없이 없앤다.
TARGET = 1024     # 생성 해상도(긴 변) — gen_final.TARGET과 같은 값·같은 이유
# **S1 전용 생성 크기 — 캔버스보다 덜 납작하게 그려서 가운데 띠만 잘라 쓴다.**
# 2026-09-01 실측(같은 프롬프트·같은 시드 11, 크기만 바꿈): 1024×536(1.91:1)에서 하늘을
# 가로지르는 자 같은 선이 **5행**, 1024×768(1.33:1)과 1024×1024에서 **0행**. 즉 이 선은
# 프롬프트가 아니라 **극단적 종횡비의 생성 아티팩트**다(낱말·부정어로 다섯 판을 쓴 자리다).
# 캔버스가 1216×640 = 1.9:1이므로 S1만은 덜 납작하게 그리고 캔버스 종횡비로 **잘라** 맞춘다
# — 늘려 맞추면 지형이 눌린다.
S1_GEN = (1024, 768)
# 잘라낼 띠의 위치 — 0.0이면 **위쪽**, 0.5면 가운데, 1.0이면 아래쪽. 가운데를 자르면 4:3 원본이
# 그린 **하늘과 능선을 통째로 버린다**(2026-09-01 실측: 능선이 화면 위끝에 붙어 골짜기 깊이가
# +0.069에 머물고 군대를 세울 능선이 화면 밖으로 나갔다). 위쪽을 잘라 쓰면 하늘·능선이 남고
# 버리는 것은 가까운 자갈밭인데, 그 자리는 어차피 인물이 덮는다.
# ⚠ 1024x1024(1:1)는 **원형 액자**를 그린다 — 4:3이 이 모델의 자리다.
S1_CROP_BIAS = 0.0


ASPECT_MAX = 1.5   # 창의 긴 변 / 짧은 변 상한 — 넘으면 **가로 줄무늬 아티팩트**가 나온다
                   # (2026-09-01 실측: 1.91:1에서 하늘 가로선 5행, 1.33:1에서 0행. notes §12 규칙 여섯째)


PAD_BY_STAGE = {}
# ⚠ **인물 단계만 0.35로 넓혀 봤다가 되돌렸다**(2026-09-01 v28): 이음매는 자리만 옮겼고
# (골리앗·방패든자 → 다윗 .525) 그림이 무너졌다 — **다윗이 둘로 늘고**, 골리앗이 비탈에 눕고,
# 왼쪽 바위가 탑이 됐다. 창이 커지면 모델이 **마스크를 어디 채울지 잃는다**(v18의 「전체 창에서
# 아무것도 안 그렸다」와 같은 결). 창은 상자에 붙여 두고 이음매는 붙임 램프로 잡는다.


def _window(b, name=None):
    """구역 + 맥락 여백, 캔버스 안으로 클램프. gen_final.window와 같은 구실.

    **납작한 창은 짧은 쪽을 늘려 완화한다.** 능선 띠처럼 가늘고 긴 구역을 그대로 창으로 쓰면
    종횡비가 3:1을 넘어 모델이 자 같은 가로선을 그린다. 마스크는 그대로 두고 창만 넓히는 것이라
    규칙 ③(창 ≠ 마스크)의 또 다른 적용이다."""
    pad = int(round(PAD_BY_STAGE.get(name, PAD) * min(b[2] - b[0], b[3] - b[1])))
    x0, y0 = max(0, b[0] - pad), max(0, b[1] - pad)
    x1, y1 = min(W, b[2] + pad), min(H, b[3] + pad)
    for _ in range(8):
        w, h = x1 - x0, y1 - y0
        if w > h * ASPECT_MAX:
            need = int(round(w / ASPECT_MAX)) - h
            y0, y1 = max(0, y0 - need // 2), min(H, y1 + (need - need // 2))
            if y0 == 0 and y1 == H:
                break
        elif h > w * ASPECT_MAX:
            need = int(round(h / ASPECT_MAX)) - w
            x0, x1 = max(0, x0 - need // 2), min(W, x1 + (need - need // 2))
            if x0 == 0 and x1 == W:
                break
        else:
            break
    return (x0, y0, x1, y1)


RIDGE_UP, RIDGE_DOWN = 0.07, 0.05   # 능선 띠 = 하늘선 위 7% ~ 아래 5%
# ⚠ **0.035/0.02로 얇게 해 봤다가 되돌렸다**(2026-09-01). 「띠 두께가 병사 키를 정한다」고 봤는데,
# 그렇게 본 근거였던 세로 런이 사실은 **병사가 아니라 언덕**을 재고 있었다(판정자 버그, judge_scene
# c2_army 주석 ②). 자를 고쳐 다시 재니 얇은 띠는 군중 밀도를 **0.39 → 0.065로 떨어뜨렸다** —
# 모델이 채울 자리가 없으면 안 그린다(v18의 「마스크가 묻히면 아무것도 안 그린다」와 같은 결).


def ridge_mask(canvas, region):
    """**능선을 따라가는 띠** — 「이편 산에 섰고 저편 산에 섰고」(17:3)를 상자가 아니라 지형에서
    파생한다. 손으로 적은 가로 상자는 지형이 바뀔 때마다 어긋나 병사가 **빈 하늘에** 그려졌다
    (v17 실측: 능선 위 비율 좌 0.28 · 우 0.20)."""
    lum = np.asarray(canvas.convert("L"), dtype=np.float32) / 255.0
    top = J.skyline(lum)
    x0, _, x1, _ = box_px(region)
    yy = np.arange(H)[:, None]
    band = (yy >= (top - RIDGE_UP * H)) & (yy <= (top + RIDGE_DOWN * H))
    band &= (top < H - 1)[None, :]     # 지형이 없는 열(하늘선 = H)은 뺀다 — 안 그러면 화면 바닥에 띠가 생긴다
    m = np.zeros((H, W), np.uint8)
    m[:, x0:x1] = (band[:, x0:x1] * 255).astype(np.uint8)
    return Image.fromarray(m, "L").filter(ImageFilter.GaussianBlur(max(4, int(0.02 * H))))


def _gen_size(win):
    w, h = win[2] - win[0], win[3] - win[1]
    sc = TARGET / max(w, h)
    return max(8, round(w * sc / 8) * 8), max(8, round(h * sc / 8) * 8)


def _change_mask(new_im, old_im):
    """**앞 단계 대비 바뀐 화소** = 이 단계가 실제로 그린 것. 사각 상자 대신 이것으로 되붙인다.

    **왜 필요한가**(2026-08-31 v4·v5 실측):
    ① v4 — 구역 마스크가 사각형이라 창 안의 **배경까지** 새로 칠해 붙었고, 단계마다 그 사각형이
       드러나 그림이 **콜라주**가 됐다.
    ② v5 — 그래서 「종이색이 아닌 화소」를 실루엣으로 썼더니 **옅게 그려진 골리앗이 통째로
       버려졌다.** 절대 밝기 기준은 옅은 인물을 못 잡는다.
    그래서 기준을 **변화량**으로 바꾼다 — 밝기와 무관하게 자기 보정된다.

    ⚠ **경계에 램프를 둔다**(2026-09-01 v29). 이진 컷은 「많이 바뀐 곳」의 테두리를 **한 픽셀
    단차**로 만들고 그것이 그대로 이음매가 된다(지형이 상세해지자 골리앗 .365 · 방패든자 .352).
    임계 **이상은 그대로 꽉 차게**(=옛 동작 보존, 인물이 옅어지지 않는다) 두고, 임계의 45%부터
    임계까지만 0→255로 올린다. 앞서 램프를 임계의 50%~200%로 걸었다가 **인물까지 부분 알파로
    붙어 다윗 잉크가 반토막**났던 것이 v24다 — 램프는 임계 **아래에만** 있어야 한다."""
    a = np.asarray(new_im.convert("L")).astype(np.float32)
    b = np.asarray(old_im.convert("L")).astype(np.float32)
    d = np.abs(a - b)
    lo = params.THRESHOLD * 0.45
    ramp = np.clip((d - lo) / (params.THRESHOLD - lo), 0.0, 1.0)
    return Image.fromarray((ramp * 255).astype(np.uint8), "L")


# ⚠ **부정어에는 토큰 가드가 없었다**(2026-09-01 task 325 실측). 긍정만 재고 부정은 그대로
# 넘겼다 — S3의 판 부정어가 **105/77**이라 뒤 28토큰이 조용히 잘렸고, 잘린 것이 하필
# **창 부정어 셋(two spears·double spear·pair of poles)과 PLATE_NEG 전부**였다.
# 그래서 「부정어로 안 잡혔다」(a591905 커밋 메시지)는 틀린 판정이다 — 부정어가 모델에
# **도달한 적이 없다**. 잘림이 불가피하면 무엇을 버릴지는 **명시적으로** 고른다:
#   ① PLATE_NEG — 배경을 그리면 오려낼 수가 없다(판 경로의 존재 이유)
#   ② 단계 고유 부정어 — 그 판의 결함을 막으려고 적은 말
#   ③ 공용 NEG — 앞에서부터 들어가는 만큼만
def _fit_neg(tok, stage_neg, lim):
    """판 부정어를 한도 안에 **명시적으로** 싼다 → (부정어, 버린 것). 조용히 자르지 않는다."""
    specific_raw = stage_neg[len(NEG):] if stage_neg.startswith(NEG) else stage_neg
    split = lambda t: [x.strip() for x in t.split(",") if x.strip()]
    # 화풍 바닥(`stick figure, crude drawing`)도 필수부에 넣는다 — 다섯 축의 C4가 재는 값이라
    # 공용 뒤쪽으로 밀리면 회귀 가드를 이 수선이 스스로 깨뜨린다.
    # ⚠ **테두리족도 필수부다**(2026-09-01 v36·d1 실측). 처음엔 「판은 어차피 오려내니 액자류는
    # 저가」로 보고 공용 뒤쪽에 뒀는데 **두 군데서 값을 치렀다**: ① v36에서 골리앗 판이 제 발밑에
    # 회색 그림자 타원을 그렸고 그것이 알파 컷에 들어가 판 하단이 직선으로 붙었다(C3 이음매
    # 0.250 → 0.540 실패) ② 판별 실행 d1의 시드 7에서 **테두리가 그려진 흰 종이**가 판을 통째로
    # 채웠다. 판을 오려 붙이는 구조에서는 판이 제 테두리를 그리는 순간 그것이 곧 이음매다.
    head = (split(PLATE_NEG) + ["stick figure", "crude drawing"]
            # `framed, picture frame`도 필수부(2026-09-03 task 329: 다윗 판 문구 4종 모두 시드 7이
            # 종이 테두리 — 단계 부정어가 늘자 이 둘이 공용 뒤쪽에서 잘렸다).
            + ["frame", "border", "framed", "picture frame", "vignette", "paper edge", "torn paper"]
            + split(specific_raw))
    head = list(dict.fromkeys(head))              # 단계 부정어와 겹칠 수 있다(S4의 vignette)
    if len(tok(", ".join(head)).input_ids) > lim:
        sys.exit(f"판 부정어의 필수부가 한도를 넘었다"
                 f"({len(tok(', '.join(head)).input_ids)}/{lim}) — 단계 부정어를 줄여라")
    generic = [t for t in split(NEG) if t not in head]   # 필수부와 겹치면 보고가 거짓말을 한다
    kept = list(head)
    for i, t in enumerate(generic):
        if len(tok(", ".join(kept + [t])).input_ids) > lim:
            return ", ".join(kept), generic[i:]
        kept.append(t)
    return ", ".join(kept), []


def _plate(pipe, name, prompt, neg, seed, label):
    """인물 한 명을 **민 종이 위에 단독으로** 그려 오려낸다 → (그림, 알파, 토큰수).

    배경 지시는 프롬프트 뒤에 붙이므로 **토큰 한도를 넘으면 조용히 잘려** 배경이 그려진다.
    넘으면 자세 문구를 줄여서 배경 지시를 살린다 — 배경이 그려지면 오려낼 수가 없다."""
    pw, ph = params.SAMPLE_SIZE
    p = prompt.rstrip() + PLATE_BG
    lim = pipe.tokenizer.model_max_length
    # ⚠ 문장부호에 기대지 말 것 — S3은 「…turned left.」로 **마침표**로 끝나서 앞선 규칙이
    # 아무것도 못 줄였고 가드가 79/77로 멈췄다(2026-09-01 v31 1차). 구절 자체를 갈아끼운다.
    for long, brief in (("seen from the side, body and face turned left", "side view facing left"),
                        ("strict side profile facing left", "side view facing left"),
                        ("strict side profile facing right", "side view facing right"),
                        ("running mid-stride", "running")):
        if len(pipe.tokenizer(p).input_ids) <= lim:
            break
        p = p.replace(long, brief, 1)
    n = len(pipe.tokenizer(p).input_ids)
    if n > lim:
        sys.exit(f"{name} 판 프롬프트가 한도를 넘었다({n}/{lim}) — 배경 지시가 잘린다")
    ng, dropped = _fit_neg(pipe.tokenizer, neg, lim)
    if dropped:
        print(f"    [{name}] 부정어 {len(dropped)}개를 예산에서 뺐다(공용 뒤쪽): "
              f"{', '.join(dropped)}", flush=True)
    res = pipe(prompt=p, negative_prompt=ng,
               image=Image.new("RGB", (pw, ph), PAPER),
               mask_image=Image.new("L", (pw, ph), 255),
               width=pw, height=ph, strength=PLATE_STRENGTH,
               num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
               generator=torch.Generator("mps").manual_seed(seed)).images[0]
    d = np.abs(np.asarray(res.convert("RGB")).astype(int) - np.array(PAPER)).max(axis=2)
    al = Image.fromarray(((d > PLATE_CUT) * 255).astype(np.uint8), "L")
    al = al.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))   # 내부 구멍 메우기
    bb = al.getbbox()
    if bb is None:
        sys.exit(f"{name} 판에서 인물을 못 오렸다 — PLATE_CUT을 의심하라")
    # **크롭 전 원본 판을 남긴다.** 프롬프트·시드가 고정이면 판은 결정적이라, 이 한 장이 있으면
    # 오려내기·배율 규칙 훑기를 **GPU 없이** 반복할 수 있다(알파는 PAPER/PLATE_CUT에서 재파생).
    res.save(os.path.join(OUT, f"{label}-plate-{name}-s{seed}.png"))   # 라벨을 붙여 문구 판별 비교가 되게
    return res.crop(bb), al.crop(bb).filter(ImageFilter.GaussianBlur(1.5)), n, lim


BODY_COV = 0.20   # 이 비율(행/열 최대 피복 대비) 이상이 **본체**다. 물매 끈·고리처럼 피복 2~5%인
                  # 얇은 지물을 배율·중심의 기준에서 뺀다 — 2026-09-02 실측: 다윗 판의 위쪽 314행
                  # (알파 bbox 848행의 **37%**)이 피복 1.8~4.7%짜리 끈이었다.


def _body_box(alpha):
    """판에서 **본체**(얇은 지물을 뺀 몸)의 상자. 배율과 가로 중심의 기준이다."""
    a = np.asarray(alpha) > 127
    cov = a.sum(axis=1)
    rows = np.flatnonzero(cov >= BODY_COV * cov.max())
    y0, y1 = int(rows[0]), int(rows[-1]) + 1
    ccov = a[y0:y1].sum(axis=0)
    cols = np.flatnonzero(ccov >= BODY_COV * ccov.max())
    return int(cols[0]), y0, int(cols[-1]) + 1, y1


def _place(canvas, fig, alpha, b):
    """오려낸 인물을 상자에 맞춰 얹는다 — **본체를 상자 높이에 맞추고 본체의 발이 상자 바닥에** 오게.

    ⚠ 기준을 판 전체 bbox에서 **본체**로 옮겼다(2026-09-02). 판 전체로 재면 얇은 지물이 두 번
    손해를 끼친다: ① 끈이 bbox를 세로로 늘린 만큼 소년이 **축소되고**(다윗 기여 잉크 0.048 →
    0.118) ② 끈이 bbox 중심을 끌어당겨 몸이 상자에서 **밀려난다**(같은 배율에서 0.083 → 0.118).
    붙일 범위는 여전히 알파 전체다 — 물매는 그림에 그대로 남는다.

    본체 아래의 그림자·지면은 이제 상자 선 **아래로 넘어간다**(골리앗 13px · 다윗 18px). 상자는
    「인물이 어디에 얼마나 크게 서는가」를 말하는 것이지 판이 그린 그림자까지 그 안에 욱여넣으라는
    뜻이 아니다."""
    bx0, by0, bx1, by1 = b
    cx0, cy0, cx1, cy1 = _body_box(alpha)
    sc = (by1 - by0) / (cy1 - cy0)
    nw, nh = max(8, int(fig.width * sc)), max(8, int(fig.height * sc))
    px = int(round((bx0 + bx1) / 2 - (cx0 + cx1) / 2 * sc))
    py = int(round(by1 - cy1 * sc))
    canvas.paste(fig.resize((nw, nh), Image.LANCZOS), (px, py),
                 alpha.resize((nw, nh), Image.LANCZOS))
    return canvas, (max(0, px), max(0, py), min(W, px + nw), min(H, py + nh))


CONTACT_STRENGTH = 0.55   # 접지 다듬기 — 있는 것을 고치는 쪽이라 낮다(얼굴 다듬기 0.72보다도).
                          # 높이면 모델이 그 자리에 새 그림을 그려 인물이 둘이 된다(v4 실측).
CONTACT_UP, CONTACT_DOWN, CONTACT_SIDE = 0.10, 0.06, 0.15   # 인물 높이·폭 대비 접지 띠


def _contact(pipe, canvas, bb, seed):
    """오려 붙인 인물의 **발 주변 띠만** 다듬어 땅에 닿게 하고 그림자를 넣는다.

    판 합성의 유일한 구조적 손해가 접지다 — 오려낸 인물은 배경과 **닿은 적이 없어서**
    발이 뜨고 그림자가 없다(스티커로 읽힌다). 장면 안 인페인팅은 이걸 공짜로 얻었다.
    인물 전체를 다시 그리면 판으로 얻은 자세를 잃으므로, 띠를 얇게 잡고 낮은 strength로 건다."""
    px0, py0, px1, py1 = bb
    fw, fh = px1 - px0, py1 - py0
    b = (max(0, int(px0 - CONTACT_SIDE * fw)), max(0, int(py1 - CONTACT_UP * fh)),
         min(W, int(px1 + CONTACT_SIDE * fw)), min(H, int(py1 + CONTACT_DOWN * fh)))
    m = Image.new("L", (W, H), 0)
    m.paste(255, b)
    m = m.filter(ImageFilter.GaussianBlur(max(4, int(0.25 * (b[3] - b[1])))))
    win = _window(b)
    gw, gh = _gen_size(win)
    prompt = (f"{ST} dry stony ground at the foot of a slope, feet planted on the ground, "
              f"a soft grey contact shadow on the ground under them.")
    neg = NEG + ", floating, gap, outline, cut-out, new person, second figure, face, portrait"
    res = pipe(prompt=prompt, negative_prompt=neg,
               image=canvas.crop(win).resize((gw, gh), Image.LANCZOS),
               mask_image=m.crop(win).resize((gw, gh), Image.LANCZOS),
               width=gw, height=gh, strength=CONTACT_STRENGTH,
               num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
               generator=torch.Generator("mps").manual_seed(seed)).images[0]
    ww, wh = win[2] - win[0], win[3] - win[1]
    canvas.paste(res.resize((ww, wh), Image.LANCZOS), (win[0], win[1]), m.crop(win))
    return canvas, b


def _tok(pipe, prompt, label):
    n = len(pipe.tokenizer(prompt).input_ids)
    lim = pipe.tokenizer.model_max_length
    if n > lim:
        sys.exit(f"{label} 프롬프트가 한도를 넘었다({n}/{lim}) — 뒤가 조용히 잘린다")
    return n, lim


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True, help="장면 명세 id (scenes/<id>.json)")
    ap.add_argument("--seeds", default=",".join(str(s) for s in params.SCENE_SEEDS))
    ap.add_argument("--stages", default=None, help="쉼표로 단계 이름 일부만(기본 전부)")
    ap.add_argument("--label", default="v1")
    ap.add_argument("--plate-seeds", default="", help="판 단계별 시드, 예 S3=42,S4=11,S5=7 (기본은 장면 시드)")
    ap.add_argument("--figures", choices=("plate", "inscene"), default="plate",
                    help="인물을 그리는 법. plate=민 종이에 그려 오려 붙임(기본, 봉인된 삼상17이 이 위에 선다) · "
                         "inscene=장면 캔버스 안에 인페인팅 + 승인된 얼굴 앵커 (task 337)")
    ap.add_argument("--fig-strength", type=float, default=SCENE_FIG_STRENGTH,
                    help=f"--figures inscene의 인물 단계 strength (기본 {SCENE_FIG_STRENGTH})")
    ap.add_argument("--no-anchor", action="store_true",
                    help="장면 안 경로에서 얼굴 앵커를 끈다 — 3판 대조의 **대조군**이다"
                         "(ADR 260825-013557: 대조군 없이 판정하지 않는다)")
    a = ap.parse_args()
    seeds = [int(s) for s in a.seeds.split(",")]
    plate_seeds = {k: int(v) for k, v in (kv.split("=") for kv in a.plate_seeds.split(",") if kv)}
    pick = None if a.stages is None else set(a.stages.split(","))
    spec = ds.load(a.scene)
    REGIONS.update(ds.regions(spec))
    J.configure(spec)   # 판정자도 같은 명세를 본다(자와 그림이 어긋나면 안 된다)
    stages = ds.stages(spec, a.figures)
    cast_region = {f["cast"]: f["region"] for f in spec.get("figures", [])}
    ip_state = {"n": 0}
    refine_src = {st["id"]: st["from"] for st in spec["stages"] if "from" in st}   # 다듬기 단계의 원천 인물 단계
    os.makedirs(OUT, exist_ok=True)

    t = time.time()
    pipe = StableDiffusionXLInpaintPipeline.from_pretrained(
        params.SDXL_BASE, torch_dtype=torch.float16, variant="fp16",
        use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    # **IP 앵커를 뗐다**(2026-09-03, task 329 · ADR `260903-062733`). 골리앗 갑주에만 동결 표본의
    # 몸통 밴드를 IP-Adapter 0.25로 붙여 왔는데(어휘 6종 0/6 이력), 판 방식에서 그 앵커가 표본의
    # **단색 목각 톤과 정면성**을 함께 실어 와 골리앗이 다른 삽화가의 그림으로 읽혔다. 세 판이 한
    # 화풍이어야 하므로 앵커 없이 어휘만으로 간다 — 갑옷이 새면 최소 패치 레퍼런스가 별건이다.
    print(f"로드 {time.time() - t:.0f}s  ·  ControlNet 없음 · IP 레퍼런스 없음 — "
          f"서술은 전부 텍스트가 진다", flush=True)

    for seed in seeds:
        # S1은 빈 종이색 캔버스를 전체 인페인팅한다 — text2img와 같고 파이프라인이 하나면 된다.
        canvas = Image.new("RGB", (W, H), PAPER)
        drawn = {}   # 단계별 실제로 그려진 실루엣 bbox — 머리 상자를 여기서 파생한다
        for st in stages:
            name, region, verse, prompt, neg = st["id"], st["region"], st["verse"], st["prompt"], st["neg"]
            if st["skip"] or (pick is not None and name not in pick):
                continue
            # **머리 상자는 저작하지 않고 실루엣에서 파생한다.** v8까지 골리앗 머리 상자가
            # y 0.05~0.30에 고정돼 있었는데 구역을 좁히며 그의 머리가 내려가, S8이 **빈 하늘을
            # 칠하고 있었다**(그래서 얼굴 단계가 「거의 안 먹는다」로 보였다).
            if st["kind"] == "plate":
                # **판으로 그려 오려 붙인다** — 장면 안에서 그리지 않는다(아래 PAPER 주석).
                ts = time.time()
                ps = plate_seeds.get(name, seed)   # 판별 시드 — 없으면 장면 시드
                fig, al, n, lim = _plate(pipe, name, prompt, neg, ps, a.label)
                canvas, bb = _place(canvas, fig, al, box_px(region))
                canvas, cb = _contact(pipe, canvas, bb, seed)
                drawn[name] = bb
                out = os.path.join(OUT, f"{a.label}-{name}-s{seed}.png")
                canvas.save(out)
                print(f"  [{name} {region} {verse}] {time.time() - ts:.0f}s  "
                      f"{n}/{lim}토큰  판 s{ps} {fig.width}x{fig.height} → 얹음 {bb} · 접지 {cb} -> "
                      f"{os.path.basename(out)}", flush=True)
                continue

            src = refine_src.get(name)
            if src and src in drawn:
                x0, y0, x1, y1 = drawn[src]
                if st["kind"] == "prop":   # 인물 단계에서 파생한 손 근처 지물 띠(폐기 단계 S9의 기전)
                    # 물매는 **든 손 크기**여야 한다. v10·v11에서 마스크가 다윗 몸통만 해서
                    # 「거대한 팔」이 나왔다 — 창을 고쳐도 **마스크가 크면 큰 것을 그린다.**
                    # v10~v12: 상자에 「물건」을 그리라 하면 그 상자 크기의 물건이 나온다(나팔·원뿔).
                    # 팔을 따라가는 **얇고 긴 띠**로 바꾸고, 문구도 「끈 두 가닥」으로만 말한다.
                    fw, fh = x1 - x0, y1 - y0
                    b = (x0 + int(fw * 0.55), max(0, y0 - int(fh * 0.16)),
                         min(W, x0 + int(fw * 1.30)), y0 + int(fh * 0.06))
                else:
                    hh = int(round((y1 - y0) * 0.30))      # 인물 상단 30% = 머리·어깨
                    b = (x0, y0, x1, y0 + hh)
                m = Image.new("L", (W, H), 0)
                m.paste(255, b)
                m = m.filter(ImageFilter.GaussianBlur(
                    max(4, int(round(FEATHER * min(b[2] - b[0], b[3] - b[1]))))))
            elif st["kind"] == "scene":
                # 인물(또는 한 그룹)을 **장면 안에서** 그린다 — 상자 합집합에 타원 마스크.
                # 그룹이면 두 사람이 한 마스크 안에 있어 서로 닿을 수 있다.
                b = union_box(st["regions"])
                m = ellipse_mask(st["regions"])
            elif st["kind"] == "ridge":
                m = ridge_mask(canvas, region)
                b = m.point(lambda v: 255 if v > 40 else 0).getbbox() or box_px(region)
            else:
                b = box_px(region)
                m = region_mask(region)
            n, lim = _tok(pipe, prompt, f"{name} {region}")
            # **구역만 잘라 1024로 키워 생성하고 되붙인다.** 전체 캔버스를 strength 0.99로
            # 넘기면 이미지 전체가 재노이즈되어 구역 내용이 **주변과 무관하게** 나오고, 단계마다
            # 쓰레기가 누적된다(2026-08-31 1차 실행에서 그렇게 무너졌다). 기존에 작동하던
            # `gen_final.run_figures`가 쓰는 패턴이 이것이다 — 창 크롭 → 확대 → 인페인팅 → 되붙임.
            # **창(맥락)과 마스크(칠할 곳)를 분리한다.** v10 실측: 작은 파생 구역(158×175)을
            # 1024로 확대하니 모델이 **클로즈업**을 그려 「거대한 손」·「인형 얼굴」이 나왔다.
            # 옛 콘티 파이프라인은 창 = 인물창 + 여백, 마스크 = 인물 실루엣으로 분리돼 있었다.
            if name in CONTEXT_FULL:
                win = (0, 0, W, H)
            elif src and src in drawn:
                win = _window(drawn[src], name)
            else:
                win = _window(b, name)
            gw, gh = S1_GEN if st["kind"] == "full" else _gen_size(win)
            ts = time.time()
            refine = st["kind"] == "refine"
            ipkw = {}
            if st["kind"] == "scene":
                ipkw, ipnote = anchor_kwargs(pipe, [] if a.no_anchor else (st.get("casts") or []),
                                             cast_region, win, gw, gh, ip_state)
                print(f"    [{name}] {ipnote}", flush=True)
            elif ip_state.get("n") and hasattr(pipe, "unload_ip_adapter"):
                pipe.unload_ip_adapter()          # 앵커가 켜진 채 다른 단계로 넘어가지 않게
                ip_state["n"] = 0
            res = pipe(prompt=prompt, negative_prompt=neg,
                       image=canvas.crop(win).resize((gw, gh), Image.LANCZOS),
                       mask_image=m.crop(win).resize((gw, gh), Image.LANCZOS),
                       width=gw, height=gh,
                       strength=(REFINE_STRENGTH if refine else
                                 a.fig_strength if st["kind"] == "scene" else
                                 STRENGTH_BY_STAGE.get(name, DEFAULT_STRENGTH)),
                       num_inference_steps=params.STEPS,
                       guidance_scale=params.GUIDANCE,
                       generator=torch.Generator("mps").manual_seed(seed),
                       **ipkw).images[0]
            ww, wh = win[2] - win[0], win[3] - win[1]
            if st["kind"] == "full":
                # 지형은 화면 전체다. **마스크를 쓰지 않고 통째로 갈아끼운다** — 부분 마스크로
                # 전체를 칠하면 캔버스 경계에서 가로 줄무늬 글리치가 남는다(v3~v8 실측).
                # 캔버스 종횡비의 **가운데 띠**만 잘라 쓴다(S1_GEN 주석 참조).
                ch = int(round(gw * H / W))
                oy = int(round((gh - ch) * S1_CROP_BIAS))
                canvas = res.crop((0, oy, gw, oy + ch)).resize((W, H), Image.LANCZOS)
                print(f"  [{name} {region} {verse}] {time.time() - ts:.0f}s  {n}/{lim}토큰  "
                      f"{gw}x{gh} → 가운데 {ch}행 잘라 전체 교체",
                      flush=True)
                continue
            else:
                back = res.resize((ww, wh), Image.LANCZOS)
                # **실루엣으로 되붙인다** — 사각 상자를 붙이면 그 변이 드러나 콜라주가 된다.
                sil = _change_mask(back, canvas.crop(win))
                # **형태학적 닫기(팽창 → 침식)로 내부 구멍을 메운다.** v6 실측: 옅게 그려진
                # 골리앗의 **내부**에서 변화량이 임계 아래라 구멍이 뚫려 그가 반투명해졌다.
                # 반지름은 구역 짧은 변에서 판다(고정값은 큰 구역에서 부족하다).
                # ⚠ **상한 8을 걸어 봤다가 되돌렸다**(2026-09-01 v27): 이음매는 안 줄고
                # (0.365 → 0.402, 자리만 옮겼다) 골리앗이 **반투명해졌다**(잉크 .109 → .049).
                # v6이 경고한 「옅은 인물 내부에 구멍」이 그대로 재현됐다 — 반지름은 구역 크기를
                # 따라가야 한다.
                r = max(3, int(round(0.035 * min(ww, wh))))
                k = 2 * r + 1
                sil = sil.filter(ImageFilter.MaxFilter(k)).filter(ImageFilter.MinFilter(k))
                sil = sil.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(4))
                paste_m = Image.composite(sil, Image.new("L", sil.size, 0), m.crop(win))
            canvas.paste(back, (win[0], win[1]), paste_m)
            bb = paste_m.point(lambda v: 255 if v > 40 else 0).getbbox()
            if bb:
                drawn[name] = (win[0] + bb[0], win[1] + bb[1], win[0] + bb[2], win[1] + bb[3])
            out = os.path.join(OUT, f"{a.label}-{name}-s{seed}.png")
            canvas.save(out)
            print(f"  [{name} {region} {verse}] {time.time() - ts:.0f}s  "
                  f"{n}/{lim}토큰  상자 {b} -> {os.path.basename(out)}", flush=True)
        final = os.path.join(OUT, f"{a.label}-final-s{seed}.png")
        canvas.save(final)
        print(f"  최종: {os.path.basename(final)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
