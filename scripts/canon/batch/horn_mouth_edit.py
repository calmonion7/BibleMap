"""task 660 — 기름 뿔 정본 입구를 klein 지시 편집으로(사람 657·658·659 마개 세 번 연속 미채택 → 칠하고 i2i 대신 모델이 입구를 직접 그림).
바탕 = fix-0.2(끝 다듬음) 위에 원본 s5의 열린 입을 되돌림 → 입구 크롭만 고증 세 꼴(사람 658 고증)로 편집 → 마스크 안만 되붙임.
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
BOX_HI = {"linensnug": (262, 150, 442, 282)}

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
        for seed in ((1, 2, 3, 4) if arm in BOX_HI else (1, 2)):
            out = os.path.join(tmp, f"mouth-{arm}-s{seed}.png")
            r = G.edit(src, CROP, BOX_HI.get(arm, BOX), arm, seed, out, prompt=prompt)
            if r["status"] == "ok":
                Image.open(out).save(os.path.join(D, f"mouth-{arm}-s{seed}.png"))
            print("[HornMouthEdit]", arm, seed, r)

{"run": run}[sys.argv[1]]()
