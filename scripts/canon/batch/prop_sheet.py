"""task 650 — 지물 정본 그림: 빈 종이에 지물 하나만 크게 그려 사람이 고른 한 장을 정본으로 둔다(사람 649 「사물을 먼저 따로그리고 비교도구로 만들어야
기름뿔이 정확히 그려질듯」). 장면 안의 작은 뿔은 문구·가이드가 안 먹어 넓은 입으로 붓는 꼴로 되돌아감(베들레헴 639~644 · 기혼 640~647) —
화면 전체 크기면 가이드 꼴이 먹는다. 정본은 ① 비교 판정(장면 크롭과 나란히) ② 장면에 얹고 약하게 다시 그리기(horn_compose)에 쓴다.
쓰기: venv314 python batch/prop_sheet.py oil-horn gen   → samples/prop-oil-horn/sheet-s<seed>.png (+ _guide.png)"""
import json, os, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "batch"))
W, H = 1216, 640
SEEDS = (42, 7, 5, 11, 23, 101, 202, 303)
STYLE = "warm cream paper, soft pencil and colored-pencil storybook illustration, gentle hand-drawn lines."
PROPS = {
    # word: 사전 낱말 id(look L2를 문구로) · shape: make_guide 꼴 · box: 화면 비 · pose: 방향·흐름 문구(사람 620 「뿔 위아래 위치 바뀜」)
    "oil-horn": {"word": "oil-horn", "shape": "horn_pour", "box": (0.18, 0.12, 0.82, 0.92),
                 "pose": "tilted with its wide end at the upper left and its narrow open pointed tip at the lower right, a thin stream of golden oil dripping straight down from the pointed tip"},
}


def look(word):
    with open(os.path.join(HERE, "..", "..", "data", "scripture_words", "words.json"), encoding="utf-8") as fh:
        w = next(x for x in json.load(fh)["words"] if x["id"] == word)
    return w["look"]["L2"]["en"].rstrip(".")


def gen(name):
    from PIL import Image, ImageDraw
    import make_guide as G
    import run_scene
    cfg = PROPS[name]
    out = os.path.join(HERE, "samples", f"prop-{name}")
    os.makedirs(out, exist_ok=True)
    g = Image.new("L", (W, H), 0)
    x0, y0, x1, y1 = cfg["box"]
    G.SHAPES[cfg["shape"]](ImageDraw.Draw(g), x0 * W, y0 * H, x1 * W, y1 * H, 255)
    guide = os.path.join(out, "_guide.png")
    g.convert("RGB").save(guide)
    prompt = (f"{STYLE} A single object drawn alone on plain warm cream paper, with nothing else: {look(cfg['word'])}, {cfg['pose']}. "
              "No hands, no people, no background, no text.")
    jobs = [{"prompt": prompt, "seed": s, "w": W, "h": H, "out": os.path.join(out, f"sheet-s{s}.png"),
             "control": guide, "control2": guide, "scale": 1.0, "cn_steps": 2, "cn_steps2": 2}
            for s in SEEDS if not os.path.exists(os.path.join(out, f"sheet-s{s}.png"))]
    with open(os.path.join(out, "prompt.txt"), "w", encoding="utf-8") as fh:
        fh.write(prompt + "\n")
    tmp = os.path.expanduser(f"~/.local/biblemap-imggen/prop-{name}")
    os.makedirs(tmp, exist_ok=True)
    if jobs:
        print(f"[PropSheet] gencn {len(jobs)}장 {run_scene.gen_zimage(jobs, tmp, 'gencn')}")


if __name__ == "__main__":
    {"gen": gen}[sys.argv[2]](sys.argv[1])
