"""task 666 — 장면 속 붓는 뿔을 klein 지시 편집으로 정본 꼴로 바꿈(사람 663·664). 옛 뿔을 지우고 정본을 오려 얹으면 지운 자리 얼룩을
다시 그리기(i2i)가 큰 뿔로 되살림(베들레헴 666 s5 1판) → 뿔 둘레 크롭만 모델이 손에 맞춰 다시 그림(마개 660~661과 같은 수단).
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
        subprocess.run([G.MFLUX, "--model", "flux2-klein-4b", "-q", "8", "--image-paths", inp, ref, "--prompt", REF_PROMPT.replace("kneeling boy", cfg.get("who", "kneeling boy")).replace("the boy's hair", "his hair"), "--seed", str(seed),
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
