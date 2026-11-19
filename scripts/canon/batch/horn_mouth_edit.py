"""task 660 — 기름 뿔 정본 입구를 klein 지시 편집으로(사람 657·658·659 마개 세 번 연속 미채택 → 칠하고 i2i 대신 모델이 입구를 직접 그림).
바탕 = fix-0.2(끝 다듬음) 위에 원본 s5의 열린 입을 되돌림 → 입구 크롭만 고증 세 꼴(사람 658 고증)로 편집 → 마스크 안만 되붙임.
  python3 batch/horn_mouth_edit.py tip woodplate-s1,bronzeplate-s4   # task 669 끝 구멍 마개 + 끈
  python3 batch/horn_mouth_edit.py run [꼴,꼴]   # 세 꼴 × 시드 1·2 → samples/prop-oil-horn-lying/mouth-<꼴>-s<시드>.png"""
import os, sys
CANON = "/Users/calmonion/Project/BibleMap/scripts/canon"
sys.path.insert(0, CANON); os.chdir(CANON)
from PIL import Image
import gen_local_edit as G
D = os.path.join(CANON, "samples", "prop-oil-horn-lying")
CROP, BOX = (200, 90, 300), (262, 188, 442, 282)
KEEP = ("Keep the horn's shape, its glossy dark brown color with pale amber streaks and ridges, the pale rim, the plain cream paper "
        "and the soft pencil and colored-pencil illustration style exactly the same.")
ARMS = {"linen": "Close the open wide end of this ram's horn with a rounded wooden stopper wrapped in pale linen cloth, pushed snugly "
                 "into the opening so only its slightly domed top shows. " + KEEP,
        "leather": "Close the open wide end of this ram's horn with a piece of soft brown leather stretched over the opening and tied "
                   "tightly around the rim with a thin cord. " + KEEP,
        "resin": "Close the open wide end of this ram's horn with a carved wooden plug fitted snugly inside the rim, its top slightly "
                 "domed, sealed around the edge with dark resin. " + KEEP,
        # task 661 — 사람 660 「뿔입구와 나무가 안맞아서 천으로 감싼 나무 마개 모양」: 둥근 나무와 울퉁불퉁한 입구 사이를 천이 메움
        "linenfit": "Close the open wide end of this ram's horn with a wooden stopper wrapped in pale linen cloth. The cloth-wrapped "
                    "stopper fills the whole uneven opening right up to the rim with no gap, the cloth pressed into the irregular edge, "
                    "its folds gathered on top with a little of the round wooden top showing in the middle. " + KEEP,
        "linencover": "Close the open wide end of this ram's horn with a wooden stopper fully covered in pale linen cloth. The cloth-covered "
                      "stopper fills the whole uneven opening right up to the rim with no gap, the cloth pressed into the irregular edge "
                      "and bulging slightly above it, with soft folds and no wood showing. " + KEEP,
        # task 661 2판 — 1판 천이 부풀어 높이 솟고 윗부분이 마스크 밖에서 흐려짐 → 얇고 낮게 · BOX 위로 넓힘(BOX_HI)
        "linensnug": "Close the open wide end of this ram's horn with a short wooden stopper wrapped in a thin layer of pale linen cloth, "
                     "pushed deep into the opening. The thin cloth fills the whole uneven opening right up to the rim with no gap and "
                     "rises only a little above the rim, with small tight folds around a round wooden top in the middle. " + KEEP}
ARMS.update({   # task 668 — 사람 667 뒤 고증 「넓은 밑부분을 나무나 금속 판으로 영구적으로 막아 바닥을 만들고, 뾰족한 끝부분을 잘라내어 작은 구멍을 낸 뒤 마개」 — 밑동은 마개가 아니라 컵 바닥
    "woodplate": "Seal the wide open end of this ram's horn permanently with a flat round wooden disc fitted inside the rim, set flush with the "
                 "rim edge like the flat bottom of a cup, with fine wood grain — no stopper sticking out, no cloth. " + KEEP,
    "bronzeplate": "Seal the wide open end of this ram's horn permanently with a flat round dull bronze plate fitted inside the rim, set flush "
                   "with the rim edge like the flat bottom of a cup — no stopper sticking out, no cloth. " + KEEP})
BOX_HI = {"linensnug": (262, 150, 442, 282)}
SEEDS4 = {"linensnug", "woodplate", "bronzeplate"}

def run():
    if G.busy():
        sys.exit("[HornMouthEdit] 다른 생성 프로세스가 돎 — 끝난 뒤 다시")
    base = Image.open(os.path.join(D, "fix-0.2.png")).convert("RGB")
    s5 = Image.open(os.path.join(D, "sheet-s5.png")).convert("RGB")
    x0, y0, x1, y1 = BOX
    base.paste(s5.crop((x0 - 25, y0 - 25, x1 + 25, y1 + 25)), (x0 - 25, y0 - 25))   # 열린 입 되돌림(편집 입력용 — 마스크 안은 편집이 덮음)
    src = os.path.join(D, "mouth-base.png"); base.save(src)
    tmp = os.path.expanduser("~/.local/biblemap-imggen/prop-oil-horn-lying/mouth"); os.makedirs(tmp, exist_ok=True)
    for arm in (sys.argv[2].split(",") if len(sys.argv) > 2 else ARMS):
        prompt = ARMS[arm]
        for seed in ((1, 2, 3, 4) if arm in SEEDS4 else (1, 2)):
            out = os.path.join(tmp, f"mouth-{arm}-s{seed}.png")
            r = G.edit(src, CROP, BOX_HI.get(arm, BOX), arm, seed, out, prompt=prompt)
            if r["status"] == "ok":
                Image.open(out).save(os.path.join(D, f"mouth-{arm}-s{seed}.png"))
            print("[HornMouthEdit]", arm, seed, r)

TIP_CROP, TIP_BOX = (780, 100, 280), (850, 180, 1010, 300)
TIP_PROMPT = ("Push a small carved wooden stopper into the small hole at the narrow cut tip of this ram's horn, and tie the stopper to the horn "
              "with a thin leather cord that is wrapped around the horn a little below the tip. " + KEEP)


TIP_PROMPT2 = ("Push a small solid wooden plug with a rounded closed top, no hole, into the small hole at the narrow cut tip of this ram's horn; "
               "the plug sticks out a little. A thin leather cord is tied around the neck of the plug and runs back to a few turns of cord wrapped "
               "around the horn a little below the tip, so the plug hangs on the cord when pulled out. " + KEEP)   # 669 2판 — 1판 s1 마개 윗면 구멍(속 빈 관) · s2~s4 끝이 대롱·나팔·꼭지


PLUG_CROP, PLUG_BOX = (860, 70, 220), (948, 145, 1014, 210)
PLUG_PROMPT = ("Replace the wide wooden cup on the narrow tip of this ram's horn with a small solid wooden stopper that is no wider than the tip: "
               "a short tapered wooden peg pushed into the tip hole, sticking out only a little, with a smooth rounded closed top and no hole. "
               "Keep the leather cord tied around it and wrapped around the horn exactly the same. " + KEEP)


def plug(seeds=(1, 2, 3, 4)):
    """task 670 — 사람 669 plug1 · 「마개가 이상함」: 마개가 끝보다 굵은 원통에 윗면이 패여 끝에 컵을 씌운 꼴 → 끝 굵기의 작은 쐐기 마개."""
    if G.busy():
        sys.exit("[HornMouthEdit] 다른 생성 프로세스가 돎 — 끝난 뒤 다시")
    tmp = os.path.expanduser("~/.local/biblemap-imggen/prop-oil-horn-lying/plug"); os.makedirs(tmp, exist_ok=True)
    for seed in seeds:
        name = f"plug-s{seed}.png"
        r = G.edit(os.path.join(D, "tip-woodplate-s1-s1.png"), PLUG_CROP, PLUG_BOX, "plug", seed, os.path.join(tmp, name), prompt=PLUG_PROMPT, mask_shape="rect")
        if r["status"] == "ok":
            Image.open(os.path.join(tmp, name)).save(os.path.join(D, name))
        print("[HornMouthEdit] plug", seed, r)


CORD_CROP, CORD_BOX = (870, 70, 200), (938, 132, 1032, 206)
CORD_PROMPT = ("The thin brown painted lines are a leather cord. Draw them as a thin leather cord tied in a tight loop around the middle of the "
               "small wooden stopper in the horn tip, running down to the knot on the horn. Keep the wooden stopper, the horn, the other cord "
               "and everything else exactly the same. " + KEEP)


def cord(seeds=(1, 2, 3, 4)):
    """task 671 — 사람 670 「끈이 마개에 묶여 있어야 됨」(마개 쪽 두 번 연속 미채택 → 수단 바꿈: 글만 → 칠한 길잡이 선 + 지시 편집).
    plug-s4에 마개 허리 띠 + 띠에서 뿔 매듭(948,197)까지 처진 선을 칠하고 klein이 가죽 끈으로 그림."""
    import math
    from PIL import ImageDraw
    if G.busy():
        sys.exit("[HornMouthEdit] 다른 생성 프로세스가 돎 — 끝난 뒤 다시")
    im = Image.open(os.path.join(D, "plug-s4.png")).convert("RGB")
    d = ImageDraw.Draw(im)
    c, ax = (1006, 159), math.radians(-58)                       # 마개 허리 가운데 · 마개 축(아래 왼쪽 → 위 오른쪽)
    px, py = -math.sin(ax), math.cos(ax)                          # 축에 수직
    a, b = (c[0] - 11 * px, c[1] - 11 * py), (c[0] + 11 * px, c[1] + 11 * py)
    col = (150, 95, 50)
    d.line([a, b], fill=col, width=3)                             # 마개 허리를 두른 띠
    lo = a if a[1] > b[1] else b
    d.line([lo, ((lo[0] + 948) / 2 - 2, (lo[1] + 197) / 2 + 4), (948, 197)], fill=col, width=3, joint="curve")   # 띠 → 뿔 매듭(살짝 처짐)
    src = os.path.join(D, "cord-guide.png"); im.save(src)
    tmp = os.path.expanduser("~/.local/biblemap-imggen/prop-oil-horn-lying/cord"); os.makedirs(tmp, exist_ok=True)
    for seed in seeds:
        name = f"cord-s{seed}.png"
        r = G.edit(src, CORD_CROP, CORD_BOX, "cord", seed, os.path.join(tmp, name), prompt=CORD_PROMPT, mask_shape="rect")
        if r["status"] == "ok":
            Image.open(os.path.join(tmp, name)).save(os.path.join(D, name))
        print("[HornMouthEdit] cord", seed, r)


SMOOTH_CROP, SMOOTH_BOX = (800, 90, 240), (830, 140, 1012, 322)
SMOOTH_PROMPT = ("Make the narrow end of this ram's horn one continuous piece of natural horn that tapers smoothly into the tip, its color "
                 "darkening gradually toward the tip — no separate collar, no ring, no joint and no step anywhere along the horn. Keep the small "
                 "wooden stopper, the leather cord tied around it and the cord wrapped around the horn exactly the same. " + KEEP)


def smooth(seeds=(1, 2, 3, 4)):
    """task 672 — 사람 「뿔끝이 마디가 안느껴지게」: 끝의 따로 끼운 듯한 검은 원통 테 · 밝은 몸통이 검은 토막으로 꺾이는 이음선 → 한 덩이로 매끈하게."""
    if G.busy():
        sys.exit("[HornMouthEdit] 다른 생성 프로세스가 돎 — 끝난 뒤 다시")
    tmp = os.path.expanduser("~/.local/biblemap-imggen/prop-oil-horn-lying/smooth"); os.makedirs(tmp, exist_ok=True)
    for seed in seeds:
        name = f"smooth-s{seed}.png"
        r = G.edit(os.path.join(D, "cord-s4.png"), SMOOTH_CROP, SMOOTH_BOX, "smooth", seed, os.path.join(tmp, name), prompt=SMOOTH_PROMPT, mask_shape="rect")
        if r["status"] == "ok":
            Image.open(os.path.join(tmp, name)).save(os.path.join(D, name))
        print("[HornMouthEdit] smooth", seed, r)


PLUG2_CROP, PLUG2_BOX = (860, 60, 200), (938, 118, 1036, 206)
PLUG2_PROMPT = ("The painted tan shape at the tip is a small solid wooden stopper pushed into the tip hole, sticking out a little, with a rounded "
                "closed top. The thin brown painted lines are a leather cord tied in a tight loop around the stopper and running down to the "
                "knot on the horn. Keep the smooth horn tip, the horn and everything else exactly the same. " + KEEP)


def plug2(seeds=(1, 2, 3, 4)):
    """task 672 2판 — 매끈한 끝(smooth-s2)에서 마개가 사라짐 → 마개·끈 자리를 칠한 길잡이 + klein(671과 같은 수단)."""
    import math
    from PIL import ImageDraw
    if G.busy():
        sys.exit("[HornMouthEdit] 다른 생성 프로세스가 돎 — 끝난 뒤 다시")
    im = Image.open(os.path.join(D, "smooth-s2.png")).convert("RGB")
    d = ImageDraw.Draw(im)
    tip, ang = (1010, 150), math.radians(-50)
    ux, uy = math.cos(ang), math.sin(ang); px, py = -uy, ux
    q = lambda a, b: (tip[0] + ux * a + px * b, tip[1] + uy * a + py * b)
    d.polygon([q(-3, -6), q(13, -5), q(15, -2), q(15, 2), q(13, 5), q(-3, 6)], fill=(214, 178, 128), outline=(120, 84, 50))   # 마개(끝에서 조금 나옴)
    col = (150, 95, 50)
    d.line([q(7, -6.5), q(7, 6.5)], fill=col, width=3)                                         # 마개 허리 끈 고리
    lo = max((q(7, -6.5), q(7, 6.5)), key=lambda p: p[1])
    d.line([lo, ((lo[0] + 950) / 2, (lo[1] + 196) / 2 + 4), (950, 196)], fill=col, width=3, joint="curve")   # 고리 → 뿔 매듭
    src = os.path.join(D, "plug2-guide.png"); im.save(src)
    tmp = os.path.expanduser("~/.local/biblemap-imggen/prop-oil-horn-lying/plug2"); os.makedirs(tmp, exist_ok=True)
    for seed in seeds:
        name = f"plug2-s{seed}.png"
        r = G.edit(src, PLUG2_CROP, PLUG2_BOX, "plug2", seed, os.path.join(tmp, name), prompt=PLUG2_PROMPT, mask_shape="rect")
        if r["status"] == "ok":
            Image.open(os.path.join(tmp, name)).save(os.path.join(D, name))
        print("[HornMouthEdit] plug2", seed, r)


TIE_CROP, TIE_BOX = (958, 102, 96), (985, 120, 1040, 182)
TIE_PROMPT = ("Close-up of the narrow tip of a ram's horn. The painted tan peg is a small solid wooden stopper pushed into the tip hole. "
              "The painted brown bands are a thin leather cord wrapped twice tightly around the neck of that wooden stopper and tied in a small "
              "knot on its side; from the knot the same cord runs down along the horn. Draw the cord clearly tied around the stopper. "
              "Keep the smooth dark horn, the paper and the soft pencil and colored-pencil illustration style exactly the same.")


def tie(seeds=(1, 2, 3, 4)):
    """task 673 — 사람 672 「마개에 끈이 안묵여 있음」(670·672 두 번 「끈이 마개에」) → 수단 바꿈: 크롭 200 → 96(마개가 15화소라 매듭 그릴 화소가 없었음)
    + 마개를 조금 더 내밀고 마개 목을 두 번 감은 끈·옆 매듭·내려가는 끈을 굵게 칠한 길잡이."""
    import math
    from PIL import ImageDraw
    if G.busy():
        sys.exit("[HornMouthEdit] 다른 생성 프로세스가 돎 — 끝난 뒤 다시")
    im = Image.open(os.path.join(D, "plug2-s4.png")).convert("RGB")
    d = ImageDraw.Draw(im)
    tip, ang = (1008, 152), math.radians(-52)
    ux, uy = math.cos(ang), math.sin(ang); px, py = -uy, ux
    q = lambda a, b: (tip[0] + ux * a + px * b, tip[1] + uy * a + py * b)
    d.polygon([q(-2, -5), q(15, -4.5), q(18, -2), q(18, 2), q(15, 4.5), q(-2, 5)], fill=(214, 178, 128), outline=(110, 76, 44))   # 마개
    col, dark = (150, 92, 48), (96, 58, 30)
    for a in (5, 8.5):
        d.line([q(a, -5.6), q(a, 5.6)], fill=col, width=2)                                   # 마개 목을 두 번 감은 끈
    k = q(7, 6.2)
    d.ellipse([k[0] - 2.2, k[1] - 2.2, k[0] + 2.2, k[1] + 2.2], fill=dark)                  # 옆 매듭
    d.line([k, q(-8, 7.5), q(-26, 6.5)], fill=col, width=2, joint="curve")                  # 매듭에서 뿔 따라 내려가는 끈
    src = os.path.join(D, "tie-guide.png"); im.save(src)
    tmp = os.path.expanduser("~/.local/biblemap-imggen/prop-oil-horn-lying/tie"); os.makedirs(tmp, exist_ok=True)
    for seed in seeds:
        name = f"tie-s{seed}.png"
        r = G.edit(src, TIE_CROP, TIE_BOX, "tie", seed, os.path.join(tmp, name), prompt=TIE_PROMPT, mask_shape="rect")
        if r["status"] == "ok":
            Image.open(os.path.join(tmp, name)).save(os.path.join(D, name))
        print("[HornMouthEdit] tie", seed, r)


def tie2(seeds=(1, 2, 3, 4)):
    """task 673 2판 — 1판 tie-s3만 마개가 길게 나왔으나 끈은 여전히 뿔 끝 테를 감음 → tie-s3의 나온 마개 허리(1018,139)에 끈 두 줄·매듭을 칠하고 같은 좁은 크롭."""
    import math
    from PIL import ImageDraw
    if G.busy():
        sys.exit("[HornMouthEdit] 다른 생성 프로세스가 돎 — 끝난 뒤 다시")
    im = Image.open(os.path.join(D, "tie-s3.png")).convert("RGB")
    d = ImageDraw.Draw(im)
    c, ang = (1019, 138), math.radians(-57)
    ux, uy = math.cos(ang), math.sin(ang); px, py = -uy, ux
    q = lambda a, b: (c[0] + ux * a + px * b, c[1] + uy * a + py * b)
    col, dark = (140, 84, 42), (90, 52, 26)
    for a in (-2, 2):
        d.line([q(a, -6.2), q(a, 6.2)], fill=col, width=2)                     # 마개 허리를 두 번 감은 끈
    k = q(0, 6.8)
    d.ellipse([k[0] - 2.4, k[1] - 2.4, k[0] + 2.4, k[1] + 2.4], fill=dark)     # 옆 매듭
    d.line([k, q(-12, 9), q(-30, 9.5)], fill=col, width=2, joint="curve")      # 매듭에서 뿔 따라 내려감
    src = os.path.join(D, "tie2-guide.png"); im.save(src)
    tmp = os.path.expanduser("~/.local/biblemap-imggen/prop-oil-horn-lying/tie2"); os.makedirs(tmp, exist_ok=True)
    for seed in seeds:
        name = f"tie2-s{seed}.png"
        r = G.edit(src, (957, 92, 96), (995, 112, 1042, 172), "tie2", seed, os.path.join(tmp, name),
                   prompt=TIE_PROMPT.replace("wrapped twice tightly around the neck of that wooden stopper", "wrapped twice tightly around the middle of that wooden stopper, above the horn rim"), mask_shape="rect")
        if r["status"] == "ok":
            Image.open(os.path.join(tmp, name)).save(os.path.join(D, name))
        print("[HornMouthEdit] tie2", seed, r)


def tip(base_names):
    """task 669 — 사람 668 「구멍 뚫은 곳에 마개가 꽂혀 있어야하고 해당 마개는 끈으로 연결되어 있어야함」: 끝 구멍에 마개 + 끈. 바탕 = 밑동 바닥판 정본 후보."""
    if G.busy():
        sys.exit("[HornMouthEdit] 다른 생성 프로세스가 돎 — 끝난 뒤 다시")
    tmp = os.path.expanduser("~/.local/biblemap-imggen/prop-oil-horn-lying/tip"); os.makedirs(tmp, exist_ok=True)
    for b in base_names:
        for seed in ((5, 6, 7, 8) if V2 else (1, 2, 3, 4)):
            name = f"tip{'2' if V2 else ''}-{b}-s{seed}.png"
            r = G.edit(os.path.join(D, f"mouth-{b}.png"), TIP_CROP, TIP_BOX, "tip", seed, os.path.join(tmp, name), prompt=TIP_PROMPT2 if V2 else TIP_PROMPT, mask_shape="rect")
            if r["status"] == "ok":
                Image.open(os.path.join(tmp, name)).save(os.path.join(D, name))
            print("[HornMouthEdit] tip", b, seed, r)


V2 = "--v2" in sys.argv
if sys.argv[1] == "tie2":
    tie2()
elif sys.argv[1] == "tie":
    tie()
elif sys.argv[1] == "plug2":
    plug2()
elif sys.argv[1] == "smooth":
    smooth()
elif sys.argv[1] == "cord":
    cord()
elif sys.argv[1] == "plug":
    plug()
elif sys.argv[1] == "tip":
    tip(sys.argv[2].split(","))
else:
    {"run": run}[sys.argv[1]]()
