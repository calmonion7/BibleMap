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
    "oil-horn": {"word": "oil-horn", "shape": "horn_pour", "box": (0.34, 0.2, 0.66, 0.86),   # task 652: 짧고 굵게(사람 650 「뿔이 이렇게 길지 않음」 — 화면 0.64 너비 구역은 길고 가는 뿔)
                 "pose": "short and stout, its length only about three times the width of its plugged wide end, tilted with its plugged wide end at the upper left and its narrow tip with the spout at the lower right, a thin stream of golden oil dripping straight down from the spout"},   # task 651 — 사람 제공 고증: 숫양 뿔 · 밑동 마개 · 끝 주둥이(v1 매끈한 소뿔은 samples/prop-oil-horn/v1)
    # task 653 — 사람 사진(숫양 뿔) 윤곽을 좌표로 옮긴 가이드(_guide_photo60.png — 끝이 아래로 60° 돌림). 사진은 생성에 넣지 않음(저작권) — 윤곽만.
    # 652까지 make_guide 꼴 + 문구로는 끝이 급히 가늘어지는 긴 갈고리(사람 650 「뿔이 이렇게 길지 않음」·「변한게 없음」).
    "oil-horn-photo": {"word": "oil-horn", "guide": "samples/prop-oil-horn/_guide_photo60.png",
                       "pose": "its length about four times the width of its wide end, tilted with the wide end at the upper left and the blunt tip at the lower right, a thin stream of golden oil dripping straight down from the tip"},   # task 654: 마개 낱말 뺌(사람 653 「마개가 아니고 기름뿔이 문제」)
    # task 655 — 사람 654 「예제사진처럼은 못만드나?」 → 사람 「4」(출발 그림 없이): 사진과 같은 방향(옆으로 누움)으로 그림 — 붓는 방향은 장면에 얹을 때 돌림 · 가이드 5스텝(3+2)
    "oil-horn-lying": {"word": "oil-horn", "guide": "samples/prop-oil-horn/_guide_photo0.png", "cn_steps": (3, 2),
                       "pose": "lying on its side, its wide end flaring into a large oval opening at the upper left, the body sagging into a gentle curve and rising to a blunt tip at the upper right, its length about four times the width of its wide end"},
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
    guide = os.path.join(out, "_guide.png")
    if "guide" in cfg:   # 미리 그린 윤곽 가이드
        Image.open(os.path.join(HERE, cfg["guide"])).convert("RGB").save(guide)
    else:
        g = Image.new("L", (W, H), 0)
        x0, y0, x1, y1 = cfg["box"]
        G.SHAPES[cfg["shape"]](ImageDraw.Draw(g), x0 * W, y0 * H, x1 * W, y1 * H, 255)
        g.convert("RGB").save(guide)
    prompt = (f"{STYLE} A single object drawn alone on plain warm cream paper, with nothing else: {look(cfg['word'])}, {cfg['pose']}. "
              "No hands, no people, no background, no text.")
    jobs = [{"prompt": prompt, "seed": s, "w": W, "h": H, "out": os.path.join(out, f"sheet-s{s}.png"),
             "control": guide, "control2": guide, "scale": 1.0, "cn_steps": cfg.get("cn_steps", (2, 2))[0], "cn_steps2": cfg.get("cn_steps", (2, 2))[1]}
            for s in SEEDS if not os.path.exists(os.path.join(out, f"sheet-s{s}.png"))]
    with open(os.path.join(out, "prompt.txt"), "w", encoding="utf-8") as fh:
        fh.write(prompt + "\n")
    tmp = os.path.expanduser(f"~/.local/biblemap-imggen/prop-{name}")
    os.makedirs(tmp, exist_ok=True)
    if jobs:
        print(f"[PropSheet] gencn {len(jobs)}장 {run_scene.gen_zimage(jobs, tmp, 'gencn')}")


if __name__ == "__main__":
    {"gen": gen}[sys.argv[2]](sys.argv[1])
