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
if sys.argv[1] == "plug":
    plug()
elif sys.argv[1] == "tip":
    tip(sys.argv[2].split(","))
else:
    {"run": run}[sys.argv[1]]()
