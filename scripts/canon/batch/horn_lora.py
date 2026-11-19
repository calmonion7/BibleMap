"""task 689 — 기름 뿔 지물 LoRA(사람 688 「참조 그림 생성 조사」 → 「LoRA 학습 진행」): 정본(frozen/props/oil-horn.png)을 생성기에 익혀 한 번에 그리기.
  $VENV batch/horn_lora.py sheet   # 학습 묶음 25장(정본 오린 꼴을 휨 그대로 돌리고·줄여 종이·장면 바탕에) + 설명 글 → ~/.local/biblemap-imggen/lora-sheet-horn
  python3 batch/horn_lora.py train # mflux-train(약 2시간 20분, 동시 금지) → ~/.local/biblemap-imggen/lora/oil-horn-v1.safetensors
  $VENV batch/horn_lora.py sheet v2 · train v2   # task 690 — 사람 689 「기름뿔 표현 제대로 안됨」(밑동 열린 아가리로 붓기 · 마개 0/8 · 금빛 쇠테):
                                                 # v1 25장 + 끝을 아래로 기울여 끝에서 붓는 10장 + 나무판 밑동·끈 마개 확대 4장 → lora-sheet-horn-v2 · oil-horn-v2(360스텝)"""
import json, math, os, random, subprocess, sys, zipfile
CANON = "/Users/calmonion/Project/BibleMap/scripts/canon"
sys.path.insert(0, CANON); sys.path.insert(0, os.path.join(CANON, "batch"))
from PIL import Image
ROOT = os.path.expanduser("~/.local/biblemap-imggen")
VER = sys.argv[2] if len(sys.argv) > 2 else "v1"
SHEET, TRAIN = os.path.join(ROOT, "lora-sheet-horn" + ("" if VER == "v1" else "-" + VER)), os.path.join(ROOT, "train")
NAME = "oil-horn-" + VER
TRIG = "oilhorn_bm"
STEPS = 300 if VER == "v1" else 360   # v2 39장 × 10번 = 390 → 60마다 저장이라 360 체크포인트
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
    if VER != "v1":
        pour_and_closeups(cut, rnd)
    print("[HornLora] 묶음", SHEET, len([f for f in os.listdir(SHEET) if f.endswith('.png')]), "장")


def pour_and_closeups(cut, rnd):
    """v2 — 끝을 아래로 기울여 끝에서 금빛 기름이 떨어지는 10장 + 정본 종이 그림의 밑동 나무판·끝 마개 확대 4장."""
    from PIL import ImageDraw
    import horn_compose as H
    bb = H.canon_cut().getbbox()
    tip0 = (H.CANON_TIP[0] - bb[0], H.CANON_TIP[1] - bb[1])
    for j in range(10):
        ang = [-40, -55, -70, -48, -62, -130, -145, -118, -35, -78][j] + rnd.uniform(-4, 4)   # 정본은 끝이 약 9° 위 — 음수 = 시계 방향으로 끝을 아래로(거울 없음)
        sc = rnd.uniform(0.5, 0.75)
        h = cut.resize((round(cut.width * sc), round(cut.height * sc)), Image.LANCZOS)
        cx, cy = h.width / 2, h.height / 2
        tx, ty = tip0[0] * sc - cx, tip0[1] * sc - cy
        h = h.rotate(ang, expand=True, resample=Image.BICUBIC)
        a = math.radians(ang)
        tx, ty = tx * math.cos(a) + ty * math.sin(a) + h.width / 2, -tx * math.sin(a) + ty * math.cos(a) + h.height / 2
        if h.width > 700 or h.height > 560:
            k = min(700 / h.width, 560 / h.height); h = h.resize((round(h.width * k), round(h.height * k)), Image.LANCZOS); tx, ty = tx * k, ty * k
        canvas = Image.new("RGB", (768, 768), [(245, 236, 214), (238, 226, 198), (247, 241, 226)][j % 3])
        ox, oy = (768 - h.width) // 2 + rnd.randint(-30, 30), 40 + rnd.randint(0, 30)
        canvas.paste(h, (ox, oy), h)
        x, y = ox + tx, oy + ty
        d = ImageDraw.Draw(canvas)
        y1 = min(760, y + rnd.randint(220, 330))
        d.line([(x, y + 2), (x + 2, y1)], fill=(222, 170, 36), width=7)          # 끝에서 떨어지는 금빛 기름
        d.line([(x - 1, y + 4), (x + 1, y1 - 4)], fill=(255, 232, 140), width=2)  # 윤기
        d.ellipse([x - 6, y1 - 4, x + 9, y1 + 9], fill=(222, 170, 36))
        i = 26 + j
        canvas.save(os.path.join(SHEET, f"{i:02d}.png"))
        open(os.path.join(SHEET, f"{i:02d}.txt"), "w").write(f"{DESC}, tilted with the small tip pointing down, a thin stream of golden oil pouring "
                                                              "from the small tip, the wide end closed by the wooden disc, alone on plain warm cream paper, soft pencil and colored-pencil storybook illustration")
    paper = Image.open(os.path.join(CANON, H.CANON_HORN)).convert("RGB")
    close = [((210, 110, 520, 420), "close-up of the wide end of " + TRIG + ", closed flat with a round wooden disc set into the rim, no opening"),
             ((250, 130, 500, 380), "close-up of the wide end of " + TRIG + ", closed flat with a round wooden disc set into the rim, no opening"),
             ((820, 80, 1080, 340), "close-up of the small cut tip of " + TRIG + ", a little wooden stopper in the tip tied on a thin leather cord wound around the horn"),
             ((860, 100, 1060, 300), "close-up of the small cut tip of " + TRIG + ", a little wooden stopper in the tip tied on a thin leather cord wound around the horn")]
    for j, (box, cap) in enumerate(close):
        i = 36 + j
        paper.crop(box).resize((768, 768), Image.LANCZOS).save(os.path.join(SHEET, f"{i:02d}.png"))
        open(os.path.join(SHEET, f"{i:02d}.txt"), "w").write(f"{cap}, glossy dark brown horn with pale amber streaks, on warm cream paper, soft pencil and colored-pencil storybook illustration")


def train():
    cfg = json.load(open(os.path.join(TRAIN, "saul-v4.json")))
    cfg["data"] = SHEET
    cfg["checkpoint"]["output_path"] = os.path.join(TRAIN, NAME)
    n = len([f for f in os.listdir(SHEET) if f.endswith(".png")])
    cfg["training_loop"]["num_epochs"] = -(-STEPS // n)
    p = os.path.join(TRAIN, NAME + ".json"); json.dump(cfg, open(p, "w"), indent=1)
    out = os.path.join(ROOT, "lora", NAME + ".safetensors")
    with open(os.path.join(TRAIN, NAME + ".log"), "w") as log:
        subprocess.run(["/usr/bin/time", "-l", os.path.join(ROOT, ".venv-mflux", "bin", "mflux-train"), "--config", p], stdout=log, stderr=subprocess.STDOUT, check=True)
    z = os.path.join(TRAIN, NAME, "checkpoints", f"{STEPS:07d}_checkpoint.zip")
    with zipfile.ZipFile(z) as zf, open(out, "wb") as f:
        f.write(zf.read(f"{STEPS:07d}_adapter.safetensors"))
    print("[HornLora] 학습 끝 →", out)

{"sheet": sheet, "train": train}[sys.argv[1]]()
