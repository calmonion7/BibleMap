"""task 666 — 장면 속 붓는 뿔을 klein 지시 편집으로 정본 꼴로 바꿈(사람 663·664). 옛 뿔을 지우고 정본을 오려 얹으면 지운 자리 얼룩을
다시 그리기(i2i)가 큰 뿔로 되살림(베들레헴 666 s5 1판) → 뿔 둘레 크롭만 모델이 손에 맞춰 다시 그림(마개 660~661과 같은 수단).
  python3 batch/horn_scene_edit.py <이름> tip [시드,...]   # task 676 끝 끈·매달린 마개
  python3 batch/horn_scene_edit.py <이름> [시드,...] [--ref]   → samples/<out>/edit[-ref]-s<시드>.png (--ref: 정본 그림을 둘째 그림으로)"""
import os, sys
CANON = "/Users/calmonion/Project/BibleMap/scripts/canon"
sys.path.insert(0, CANON); os.chdir(CANON)
from PIL import Image
import gen_local_edit as G
KEEP = ("Keep the old man's hands and sleeves, every face, the other people, the background and the soft pencil and colored-pencil "
        "illustration style exactly the same.")
HORN = ("a glossy dark brown ram's horn with pale amber streaks and fine ridges, shorter than a forearm: its wide end, held in his two hands, "
        "is closed with a cloth-wrapped wooden stopper, and it curves and narrows to a small cut tip with a hole")
SCENES = {
    "bethlehem15": {"base": "samples/bethlehem-step23-t15/composition-A-s5.png", "out": "bethlehem15-horn-edit",
                    "crop": (390, 170, 200), "box": (425, 205, 548, 328),
                    "prompt": f"Replace the horn the old man holds up with {HORN} just above the kneeling boy's head; golden oil drips in a thin stream "
                              f"from that small tip hole down onto the boy's hair. {KEEP}"},
    # task 675 — 기혼 665 s42: 오려 얹기는 휨을 거울로 뒤집거나(사람 674 「기름뿔 뒤집힘」) 옛 뿔 끝·흐린 뿔이 남음 → 베들레헴과 같은 klein + 정본
    # task 676 — 확정본 B1 끝을 정본 끝처럼(끈·매달린 마개)
    "bethlehem15b1": {"image": "samples/bethlehem15-horn-edit/edit-ref-s1.png", "out": "bethlehem15-horn-edit",
                      "tip": {"tip": (527, 295), "deg": 47, "crop": (476, 250, 80), "box": (492, 262, 548, 322), "hang_left": True},
                      "clean": {"crop": (400, 180, 180), "box": (436, 200, 552, 330)},
                      "oil": {"src": "samples/bethlehem-b1-canon/canon-c.png", "out": "bethlehem-b1-canon", "crop": (488, 270, 72), "box": (522, 297, 540, 326)}},
    "bethlehem15b1g": {"base": "samples/bethlehem-b1-canon/src.png", "out": "bethlehem15-horn-edit", "crop": (390, 170, 200), "box": (425, 205, 548, 328),
                       "prompt": "", "tag": "b1g", "extra": " A thin leather cord is wrapped around the horn just below the tip, and the small wooden stopper hangs from it on a short loop of cord, pulled out of the tip."},
    # task 684 — 사람 675 「기름뿔모양이 아님」(klein이 다시 그림) → 베들레헴 677~678과 같은 길: 뿔 지운 바탕 → 정본 그대로 얹기 → 기름만 klein
    "gihon18c": {"image": "samples/gihon-step23-t18/composition-A-s42.png", "out": "gihon18-horn-edit",
                 "clean": {"crop": (480, 240, 170), "box": (512, 262, 628, 372)},
                 "oil": {"src": "samples/gihon18-horn-canon/canon-c.png", "out": "gihon18-horn-canon", "crop": (560, 315, 72), "box": (588, 336, 608, 366)}},
    # task 685 — 사람 684 「두 손으로 쥐어야 함」: 두 손이 뿔 몸통 한 자리에 모인 665 s303(그 자리 = 정본을 휨 그대로 얹을 때 굽은 배)
    "gihon303": {"image": "samples/gihon-step23-t18/composition-A-s303.png", "out": "gihon303-horn",
                 "clean": {"crop": (490, 228, 175), "box": (515, 245, 640, 382)},
                 "oil": {"src": "samples/gihon303-horn/canon-c.png", "out": "gihon303-horn", "crop": (564, 310, 72), "box": (590, 330, 610, 366)},
                 "grip": {"src": "samples/gihon303-horn/oil-s3-b.png", "out": "gihon303-horn", "crop": (505, 262, 96), "box": (520, 286, 580, 340)}},
    "gihon18": {"base": "samples/gihon-step23-t18/composition-A-s42.png", "out": "gihon18-horn-edit",
                "crop": (450, 225, 195), "box": (500, 255, 622, 365), "who": "kneeling young man", "prompt": ""},
    # task 675 2판 — s42 그대로면 옛 나팔 배치를 따라 넓은 밑동에서 부음(4/4) → 정본을 거울 없이 얹어 끝을 머리 위에 둔 칠한 그림(horn_compose gihon18-canon src)에서
    "gihon18g": {"base": "samples/gihon18-horn-canon/src.png", "out": "gihon18-horn-edit",
                 "crop": (450, 225, 195), "box": (500, 255, 622, 365), "who": "kneeling young man", "prompt": "", "tag": "g"},
}
REF_PROMPT = ("Replace the horn the old man holds with the curved ram's horn from the second image — the same shape, glossy dark brown color "
              "with pale amber streaks whose wide end is closed flat with a wooden disc. He holds its thick body near the wide end in his two hands, it curves and "
              "narrows to its small cut tip just above the kneeling boy's head — the closed wide end stays up in his hands and no oil comes from it — and golden oil drips in a thin stream from that small tip hole onto "
              "the boy's hair. ") + KEEP


def edit_ref(src, crop, box, seed, out):
    """G.edit와 같되 둘째 그림으로 지물 정본을 넘김(task 666 2판 — 글만으로는 곧은 원통·병 꼴)."""
    import subprocess, time
    from gen_engedi_knife import color_match
    L, T, side = crop
    base = Image.open(src).convert("RGB")
    stem = out[:-4]
    inp, ref, raw = stem + "-in.png", stem + "-ref.png", stem + "-raw.png"
    base.crop((L, T, L + side, T + side)).resize((G.EDIT, G.EDIT), Image.LANCZOS).save(inp)
    c = Image.open(os.path.join(CANON, "frozen/props/oil-horn.png")).convert("RGB").crop((220, 100, 1060, 480))   # task 673 정본(끝이 1031,123까지)
    bg = Image.new("RGB", (G.EDIT, G.EDIT), c.getpixel((5, 5))); c.thumbnail((G.EDIT, G.EDIT)); bg.paste(c, (0, (G.EDIT - c.height) // 2)); bg.save(ref)
    if not os.path.exists(raw):
        subprocess.run([G.MFLUX, "--model", "flux2-klein-4b", "-q", "8", "--image-paths", inp, ref, "--prompt", REF_PROMPT.replace("kneeling boy", cfg.get("who", "kneeling boy")).replace("the boy's hair", "his hair") + cfg.get("extra", ""), "--seed", str(seed),
                        "--steps", "4", "--width", str(G.EDIT), "--height", str(G.EDIT), "--output", raw], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not os.path.exists(raw):
        return {"status": "fail"}
    layer, mm = Image.new("RGB", base.size), Image.new("L", base.size, 0)
    e = Image.open(raw).convert("RGB").resize((side, side), Image.LANCZOS)
    layer.paste(color_match(e, base.crop((L, T, L + side, T + side))), (L, T))
    mm.paste(G.mask(crop, box, "rect"), (L, T))
    Image.composite(layer, base, mm).save(out)
    return {"status": "ok"}


TIP_PROMPT = ("Close-up of the narrow end of the ram's horn the old man pours from. Make it match the narrow end of the horn in the second image: "
              "the smooth dark horn tapering to a small cut tip with a hole, and a thin leather cord wrapped around the horn a little below the tip. "
              "The painted brown lines are that cord: from the wraps it hangs down in a short loop to the small tan wooden stopper, which hangs "
              "on the cord, pulled out of the tip. Golden oil drips in a thin stream from the open tip hole. Keep the old man's sleeves, the boy, "
              "the other people, the background and the soft pencil and colored-pencil illustration style exactly the same.")


def tip_edit(cfg, seeds):
    """task 676 — 사람 674(B1) 「끝부분이 안닮았고 줄도없음 줄에 묶인 마개도 없고」: 확정본 끝을 정본 끝처럼 — 끝 감은 끈 + 끈에 매달린 마개(붓는 중이라 뺌).
    좁은 크롭(80) + 칠한 길잡이(감은 끈 두 줄·늘어진 끈·매달린 마개) + 둘째 그림 = 정본 끝 확대(673 마개 매듭과 같은 수단)."""
    import math, subprocess
    from PIL import ImageDraw
    from gen_engedi_knife import color_match
    t = cfg["tip"]
    base = Image.open(os.path.join(CANON, cfg["image"])).convert("RGB")
    im = base.copy(); d = ImageDraw.Draw(im)
    (tx, ty), ang = t["tip"], math.radians(t["deg"])          # 끝 · 뿔 축(밑동 → 끝)
    ux, uy = math.cos(ang), math.sin(ang); px, py = -uy, ux
    q = lambda a, b: (tx + ux * a + px * b, ty + uy * a + py * b)
    col = (140, 86, 44)
    for a in (-7, -10.5):
        d.line([q(a, -4.6), q(a, 4.6)], fill=col, width=2)   # 끝 아래 몸통을 감은 끈
    side = -1 if t.get("hang_left") else 1
    h0 = q(-9, 4.6 * side)
    hp = (h0[0] - 4 if side < 0 else h0[0] + 4, h0[1] + 9)
    d.line([h0, ((h0[0] + hp[0]) / 2 - 1, (h0[1] + hp[1]) / 2 + 2), hp], fill=col, width=2, joint="curve")   # 늘어진 끈
    d.rounded_rectangle([hp[0] - 2.5, hp[1], hp[0] + 2.5, hp[1] + 6], radius=2, fill=(210, 174, 124), outline=(110, 74, 40))   # 매달린 마개
    src = os.path.join(CANON, "samples", cfg["out"], "tip-guide.png"); im.save(src)
    L, T, side_px = t["crop"]
    tmp = os.path.expanduser(f"~/.local/biblemap-imggen/{cfg['out']}/tip"); os.makedirs(tmp, exist_ok=True)
    inp, ref = os.path.join(tmp, "in.png"), os.path.join(tmp, "ref.png")
    im.crop((L, T, L + side_px, T + side_px)).resize((G.EDIT, G.EDIT), Image.LANCZOS).save(inp)
    c = Image.open(os.path.join(CANON, "frozen/props/oil-horn.png")).convert("RGB").crop((820, 90, 1060, 330)).resize((G.EDIT, G.EDIT), Image.LANCZOS); c.save(ref)
    for sd in seeds:
        raw, out = os.path.join(tmp, f"raw-s{sd}.png"), os.path.join(CANON, "samples", cfg["out"], f"tip-s{sd}.png")
        if not os.path.exists(raw):
            subprocess.run([G.MFLUX, "--model", "flux2-klein-4b", "-q", "8", "--image-paths", inp, ref, "--prompt", TIP_PROMPT, "--seed", str(sd),
                            "--steps", "4", "--width", str(G.EDIT), "--height", str(G.EDIT), "--output", raw], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not os.path.exists(raw):
            print("[HornSceneEdit] tip 실패", sd); continue
        layer, mm = Image.new("RGB", base.size), Image.new("L", base.size, 0)
        e = Image.open(raw).convert("RGB").resize((side_px, side_px), Image.LANCZOS)
        layer.paste(color_match(e, base.crop((L, T, L + side_px, T + side_px))), (L, T))
        mm.paste(G.mask(t["crop"], t["box"], "rect"), (L, T))
        Image.composite(layer, base, mm).save(out)
        print("[HornSceneEdit] tip", sd, out)


CLEAN_PROMPT = ("Remove the horn the old man is holding, the golden oil stream and any oil on the young man's hair completely, and show what is behind them: the plain "
                "background behind. Keep the old man's two raised hands exactly where they are with the fingers curled as if "
                "gripping something, and keep the boy, the other people, the background and the soft pencil and colored-pencil illustration style "
                "exactly the same.")


def clean(cfg, seeds):
    """task 677 — 사람 676 「뿔이 찌그러져 있음 정본이랑 비교해봐」: klein이 정본을 다시 그리며 몸통을 부풀리고 꺾음(지운 자리 번짐까지 뿔로) →
    먼저 뿔만 지운 깨끗한 바탕을 만들고(이 함수), 그 위에 정본을 다시 그리지 않고 그대로 얹는다(horn_compose bethlehem-b1c)."""
    c = cfg["clean"]
    for sd in seeds:
        name = f"clean-s{sd}.png"
        o = os.path.join(os.path.expanduser(f"~/.local/biblemap-imggen/{cfg['out']}"), name)
        os.makedirs(os.path.dirname(o), exist_ok=True)
        r = G.edit(os.path.join(CANON, cfg["image"]), c["crop"], c["box"], "clean", sd, o, prompt=CLEAN_PROMPT, mask_shape="rect")
        if r["status"] == "ok":
            Image.open(o).save(os.path.join(CANON, "samples", cfg["out"], name))
        print("[HornSceneEdit] clean", sd, r)


OIL_PROMPT = ("The painted yellow line is golden olive oil: draw it as a clearly visible, bright shining golden stream of oil, as wide as the painted line, with a glossy highlight, clearly standing out against the grey tunic behind it, falling from the small hole at the tip "
              "of the horn straight down onto the kneeling boy's hair, with a small shining drop on his hair. The small brown oval is a little wooden "
              "stopper hanging on a thin leather cord from the horn. Keep the horn itself, the boy, the other people, the background and the soft pencil "
              "and colored-pencil illustration style exactly the same.")


def oil(cfg, seeds):
    """task 677 2판 — 정본을 그대로 얹은 그림(canon-c)에 칠한 기름 줄·마개를 좁은 크롭 klein으로 자연스럽게(뿔 몸통은 상자 밖)."""
    o = cfg["oil"]
    for sd in seeds:
        name = f"oil-s{sd}.png"
        tmpo = os.path.join(os.path.expanduser(f"~/.local/biblemap-imggen/{o['out']}"), name)
        os.makedirs(os.path.dirname(tmpo), exist_ok=True)
        r = G.edit(os.path.join(CANON, o["src"]), o["crop"], o["box"], "oil", sd, tmpo, prompt=OIL_PROMPT, mask_shape="rect")
        if r["status"] == "ok":
            Image.open(tmpo).save(os.path.join(CANON, "samples", o["out"], name))
        print("[HornSceneEdit] oil", sd, r)


GRIP_PROMPT = ("The old priest's two hands firmly grip the body of the dark brown ram's horn: his fingers wrap around the horn and overlap it, "
               "both hands holding it together from below and in front, so the horn clearly rests in his hands. Keep the horn's shape, color and "
               "stripes, his sleeves, his face, the background and the soft pencil and colored-pencil illustration style exactly the same.")


def grip(cfg, seeds):
    """task 686 — 사람 685 「기름뿔을 손으로 들고 있지 않음」: 얹은 정본 아래에 손이 놓였을 뿐 감싸 쥐지 않음 → 두 손과 닿는 몸통만 좁은 크롭 klein."""
    gr = cfg["grip"]
    for sd in seeds:
        name = f"grip-s{sd}.png"
        tmpo = os.path.join(os.path.expanduser(f"~/.local/biblemap-imggen/{gr['out']}"), name)
        os.makedirs(os.path.dirname(tmpo), exist_ok=True)
        r = G.edit(os.path.join(CANON, gr["src"]), gr["crop"], gr["box"], "grip", sd, tmpo, prompt=GRIP_PROMPT, mask_shape="rect")
        if r["status"] == "ok":
            Image.open(tmpo).save(os.path.join(CANON, "samples", gr["out"], name))
        print("[HornSceneEdit] grip", sd, r)


if len(sys.argv) > 2 and sys.argv[2] == "grip":
    if G.busy():
        sys.exit("[HornSceneEdit] 다른 생성 프로세스가 돎")
    grip(SCENES[sys.argv[1]], [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else [1, 2, 3, 4])
    sys.exit(0)
if len(sys.argv) > 2 and sys.argv[2] == "oil":
    if G.busy():
        sys.exit("[HornSceneEdit] 다른 생성 프로세스가 돎")
    oil(SCENES[sys.argv[1]], [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else [1, 2, 3, 4])
    sys.exit(0)
if len(sys.argv) > 2 and sys.argv[2] == "clean":
    if G.busy():
        sys.exit("[HornSceneEdit] 다른 생성 프로세스가 돎")
    clean(SCENES[sys.argv[1]], [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else [1, 2, 3, 4])
    sys.exit(0)
if len(sys.argv) > 2 and sys.argv[2] == "tip":
    c = SCENES[sys.argv[1]]
    if G.busy():
        sys.exit("[HornSceneEdit] 다른 생성 프로세스가 돎")
    tip_edit(c, [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else [1, 2, 3, 4])
    sys.exit(0)
cfg = SCENES[sys.argv[1]]
use_ref = "--ref" in sys.argv
sys.argv = [a for a in sys.argv if a != "--ref"]
seeds = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [1, 2]
if G.busy():
    sys.exit("[HornSceneEdit] 다른 생성 프로세스가 돎")
out = os.path.join(CANON, "samples", cfg["out"]); os.makedirs(out, exist_ok=True)
tmp = os.path.expanduser(f"~/.local/biblemap-imggen/{cfg['out']}"); os.makedirs(tmp, exist_ok=True)
for sd in seeds:
    name = f"edit{'-ref' if use_ref else ''}{cfg.get('tag', '')}-s{sd}.png"
    o = os.path.join(tmp, name)
    r = (edit_ref(os.path.join(CANON, cfg["base"]), cfg["crop"], cfg["box"], sd, o) if use_ref else
         G.edit(os.path.join(CANON, cfg["base"]), cfg["crop"], cfg["box"], "horn", sd, o, prompt=cfg["prompt"], mask_shape="rect"))
    if r["status"] == "ok":
        Image.open(o).save(os.path.join(out, name))
    print("[HornSceneEdit]", sd, r)
