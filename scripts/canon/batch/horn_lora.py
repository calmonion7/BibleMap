"""task 689 — 기름 뿔 지물 LoRA(사람 688 「참조 그림 생성 조사」 → 「LoRA 학습 진행」): 정본(frozen/props/oil-horn.png)을 생성기에 익혀 한 번에 그리기.
  $VENV batch/horn_lora.py sheet   # 학습 묶음 25장(정본 오린 꼴을 휨 그대로 돌리고·줄여 종이·장면 바탕에) + 설명 글 → ~/.local/biblemap-imggen/lora-sheet-horn
  python3 batch/horn_lora.py train # mflux-train(약 2시간 20분, 동시 금지) → ~/.local/biblemap-imggen/lora/oil-horn-v1.safetensors"""
import json, math, os, random, subprocess, sys, zipfile
CANON = "/Users/calmonion/Project/BibleMap/scripts/canon"
sys.path.insert(0, CANON); sys.path.insert(0, os.path.join(CANON, "batch"))
from PIL import Image
ROOT = os.path.expanduser("~/.local/biblemap-imggen")
SHEET, TRAIN = os.path.join(ROOT, "lora-sheet-horn"), os.path.join(ROOT, "train")
TRIG = "oilhorn_bm"
STEPS = 300
DESC = (f"{TRIG}, a ram's horn oil flask, glossy dark brown with pale amber streaks and fine ridges, its wide end closed flat with a round "
        "wooden disc, curving and narrowing to a small cut tip with a little wooden stopper tied on a thin leather cord")
_UNUSED_BGS = ["samples/gihon-step23-t18/composition-A-s42.png", "samples/bethlehem-step23-t17/composition-A-s5.png",
       "samples/gihon-step23-t18/composition-A-s303.png", "samples/bethlehem-step23-t18/composition-A-s7.png"]


def sheet():
    import horn_compose as H
    cut = H.canon_cut()
    bb = cut.getbbox(); cut = cut.crop(bb)
    os.makedirs(SHEET, exist_ok=True)
    rnd = random.Random(689)
    paper = (245, 236, 214)
    for i in range(25):
        ang = [0, -20, 20, -40, 40, -60, 60, -90, 90, -120, 120, 150, -150][i % 13] + rnd.uniform(-6, 6)   # 돌리기만(거울 없음 — 사람 674 「뒤집힘」)
        sc = rnd.uniform(0.45, 0.85)
        h = cut.resize((round(cut.width * sc), round(cut.height * sc)), Image.LANCZOS).rotate(ang, expand=True, resample=Image.BICUBIC)
        canvas = Image.new("RGB", (768, 768), [(245, 236, 214), (238, 226, 198), (247, 241, 226)][i % 3])   # 종이 색조 셋 — 장면 조각은 옛 나팔 뿔이 함께 잘려 들어와 뺌
        where = "alone on plain warm cream paper"
        if h.width > 740 or h.height > 740:
            k = 740 / max(h.width, h.height); h = h.resize((round(h.width * k), round(h.height * k)), Image.LANCZOS)
        canvas.paste(h, ((768 - h.width) // 2 + rnd.randint(-40, 40), (768 - h.height) // 2 + rnd.randint(-40, 40)), h)
        canvas.save(os.path.join(SHEET, f"{i + 1:02d}.png"))
        open(os.path.join(SHEET, f"{i + 1:02d}.txt"), "w").write(f"{DESC}, {where}, soft pencil and colored-pencil storybook illustration")
    print("[HornLora] 묶음", SHEET, len([f for f in os.listdir(SHEET) if f.endswith('.png')]), "장")


def train():
    cfg = json.load(open(os.path.join(TRAIN, "saul-v4.json")))
    cfg["data"] = SHEET
    cfg["checkpoint"]["output_path"] = os.path.join(TRAIN, "oil-horn-v1")
    n = len([f for f in os.listdir(SHEET) if f.endswith(".png")])
    cfg["training_loop"]["num_epochs"] = -(-STEPS // n)
    p = os.path.join(TRAIN, "oil-horn-v1.json"); json.dump(cfg, open(p, "w"), indent=1)
    out = os.path.join(ROOT, "lora", "oil-horn-v1.safetensors")
    with open(os.path.join(TRAIN, "oil-horn-v1.log"), "w") as log:
        subprocess.run(["/usr/bin/time", "-l", os.path.join(ROOT, ".venv-mflux", "bin", "mflux-train"), "--config", p], stdout=log, stderr=subprocess.STDOUT, check=True)
    z = os.path.join(TRAIN, "oil-horn-v1", "checkpoints", f"{STEPS:07d}_checkpoint.zip")
    with zipfile.ZipFile(z) as zf, open(out, "wb") as f:
        f.write(zf.read(f"{STEPS:07d}_adapter.safetensors"))
    print("[HornLora] 학습 끝 →", out)

{"sheet": sheet, "train": train}[sys.argv[1]]()
