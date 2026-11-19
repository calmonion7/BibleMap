"""task 682 — 사람 679 「사람들이 다윗을 바라보지 않음 근처에 둘러 있어야」: 생성(무리 실루엣·옆 보는 뼈대) 16/16 형들이 정면 → 사람 「고른 장에서 머리만 돌리기」.
고른 장(681 s5)의 형 무리 둘레만 klein 지시 편집으로 다윗 쪽으로 돌림.
  python3 batch/brothers_turn.py <무리 r|l> <바탕> <시드,...> → samples/bethlehem-turn/<무리>-s<시드>.png"""
import os, sys
CANON = "/Users/calmonion/Project/BibleMap/scripts/canon"
sys.path.insert(0, CANON); os.chdir(CANON)
from PIL import Image
import gen_local_edit as G
KEEP = ("Keep each man's clothes, colors, headwrap, beard and height, the number of men, the old prophet, the kneeling boy, the stone wall, "
        "the field and the soft pencil and colored-pencil illustration style exactly the same.")
GROUPS = {   # crop (L, T, 변) · box(편집 범위) · 지시
    "r": ((575, 205, 330), (585, 215, 900, 535),
          "Turn every grown man in this group of brothers toward the left, toward the kneeling boy: their bodies in three-quarter view and their "
          "faces in profile facing left, heads slightly bowed, looking down at the boy, hands clasped in front. " + KEEP),
    "l": ((20, 200, 340), (35, 210, 255, 540),
          "Turn the three men in this group toward the right, toward the kneeling boy in the middle of the picture: their bodies in three-quarter "
          "view and their faces in profile facing right, looking at the boy, hands clasped in front. " + KEEP),
}
HEADS = {"r": [(627, 250), (663, 247), (700, 250), (763, 250), (833, 248)], "l": [(92, 243), (147, 243), (208, 243)]}   # 681 s5 머리 가운데
HEAD_PROMPT = ("Turn this man's head so that his face is seen in profile, facing {side} and tilted slightly down, looking down at a kneeling boy "
               "beside him. Keep his headwrap or hair, beard, skin, his neck and shoulders, the background and the soft pencil and colored-pencil "
               "illustration style exactly the same.")


def heads(base, seed):
    """task 682 2판 — 무리 통째 편집은 무릎 꿇은 사람을 덧붙이고 얼굴은 정면(4/4) → 머리 하나씩 좁은 크롭(100)으로 차례로 돌림(앞 결과 위에 다음)."""
    out = os.path.join(CANON, "samples", "bethlehem-turn"); os.makedirs(out, exist_ok=True)
    tmp = os.path.expanduser(f"~/.local/biblemap-imggen/bethlehem-turn/heads-s{seed}"); os.makedirs(tmp, exist_ok=True)
    cur = os.path.join(CANON, base)
    for g, side in (("r", "left"), ("l", "right")):
        for i, (cx, cy) in enumerate(HEADS[g]):
            o = os.path.join(tmp, f"{g}{i}.png")
            r = G.edit(cur, (cx - 50, cy - 50, 100), (cx - 24, cy - 30, cx + 24, cy + 30), "head", seed * 10 + i, o,
                       prompt=HEAD_PROMPT.format(side=side), mask_shape="ellipse")
            print("[BrothersTurn] head", g, i, r)
            if r["status"] == "ok":
                cur = o
    Image.open(cur).save(os.path.join(out, f"heads-s{seed}.png"))


if sys.argv[1] == "heads":
    if G.busy():
        sys.exit("[BrothersTurn] 다른 생성 프로세스가 돎")
    for sd in [int(x) for x in sys.argv[3].split(",")]:
        heads(sys.argv[2], sd)
    sys.exit(0)
g, base, seeds = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3].split(",")]
if G.busy():
    sys.exit("[BrothersTurn] 다른 생성 프로세스가 돎")
crop, box, prompt = GROUPS[g]
out = os.path.join(CANON, "samples", "bethlehem-turn"); os.makedirs(out, exist_ok=True)
tmp = os.path.expanduser("~/.local/biblemap-imggen/bethlehem-turn"); os.makedirs(tmp, exist_ok=True)
tag = os.path.splitext(os.path.basename(base))[0]
for sd in seeds:
    name = f"{g}-{tag}-s{sd}.png"
    r = G.edit(os.path.join(CANON, base), crop, box, "turn", sd, os.path.join(tmp, name), prompt=prompt, mask_shape="rect")
    if r["status"] == "ok":
        Image.open(os.path.join(tmp, name)).save(os.path.join(out, name))
    print("[BrothersTurn]", g, sd, r)
