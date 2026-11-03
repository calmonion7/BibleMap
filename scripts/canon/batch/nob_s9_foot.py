"""놉 t19 s9 — 칼 꾸러미 아래 끝의 퍼진 매듭(「양쪽 끝에 자루가 있는 것처럼」 자루 하나 1/3)만 고친다(task 562 · 작은 부위 손질 · GPU 0).

꾸러미 기둥 폭(COL) 안은 바로 위 꾸러미 줄(SRC_Y)을 내려 곧게 땅까지 잇고, 그 밖 퍼진 자리는 같은 열 위쪽 땅 화소(LIFT)로 덮고 가장자리를 흐려 섞는다.

    python3 batch/nob_s9_foot.py <src.png> <dst.png>
"""
import sys

from PIL import Image, ImageDraw, ImageFilter

BOX = (512, 554, 562, 580)   # 퍼진 매듭이 든 자리
COL = (528, 547)             # 꾸러미 기둥 폭(x)
SRC_Y = 548                  # 기둥을 이어 내릴 꾸러미 줄
LIFT = 28                    # 땅 화소를 가져올 위쪽 거리(같은 열 — 옆 땅은 결이 달라 네모 자국)


def fix(src, dst):
    im = Image.open(src).convert("RGB")
    px = im.load()
    out = im.copy()
    op = out.load()
    x0, y0, x1, y1 = BOX
    for y in range(y0, y1):
        for x in range(x0, x1):
            op[x, y] = px[x, SRC_Y - (y - y0) % 8] if COL[0] <= x < COL[1] else px[x, y - LIFT]
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rectangle([x0 + 3, y0 + 3, x1 - 3, y1 - 1], fill=255)
    im.paste(out, (0, 0), mask.filter(ImageFilter.GaussianBlur(2.5)))
    im.save(dst)
    print(f"[NobFoot] {dst}")


if __name__ == "__main__":
    fix(sys.argv[1], sys.argv[2])
