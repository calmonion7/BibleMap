"""라마 곁 장면 s11 — 허공의 창을 왼쪽 돌기둥에 촉부터 박음(사람 판정 task 522 「구름안 창이 벽에박히게」 · task 527).

창 화소를 벽에서 떼어(위쪽 같은 열 벽 화소로 메움) 왼쪽으로 SHIFT만큼 옮겨 다시 얹되, 돌기둥 면(EDGE) 왼쪽은 그리지 않아
촉 앞쪽이 돌 속에 묻힌다. 뒤끝 촉(BUTT 오른쪽 — 규칙 derive.no-second-point)은 버리고 둥근 마개로 닫으며, 박힌 자리를 축으로 뒤끝을 사울 손 쪽으로 TILT만큼 내린다.
GPU 0 · 화소 편집만(편집기를 거치지 않아 화풍 그대로 — ADR 261030-011200).

    python3 batch/ramah_spear_wall.py   →  ~/.local/biblemap-imggen/ramah-inset-wall/ 에 곁 장면·큰 장면 s11
    python3 batch/inset_try.py comp --main authored-david-ramah-samuel --dir ramah-inset-wall --seeds 11
"""
import os
import shutil

from PIL import Image, ImageDraw, ImageFilter

SRC = os.path.expanduser("~/.local/biblemap-imggen/ramah-inset-r2")
DST = os.path.expanduser("~/.local/biblemap-imggen/ramah-inset-wall")
INSET, MAIN = "authored-david-ramah-samuel-inset-s11.png", "authored-david-ramah-samuel-s11.png"
BOX = (200, 255, 706, 292)   # 창이 든 띠(촉 208 ~ 뒤끝 촉 702, y 262~284)
BUTT = 662                   # 뒤끝 촉이 시작하는 x
EDGE = 181                   # 돌기둥 오른쪽 면 x(창 높이 y≈272)
SHIFT = 75                   # 왼쪽으로 옮김 — 촉 앞 절반쯤이 돌 속
TILT = 8                     # 기울임(도) — 수평이면 합성 크기에서 「허공에 가로로 떠 있음」(판정 527 1차)
Y = 272                      # 창 가운데 높이 = 박힌 자리
LIFT = 38                    # 지운 자리를 메울 벽 화소의 위쪽 거리
WALL_DIST = 40               # 벽 빛과 이만큼 먼 화소 = 창


def main():
    os.makedirs(DST, exist_ok=True)
    shutil.copy(os.path.join(SRC, MAIN), os.path.join(DST, MAIN))
    im = Image.open(os.path.join(SRC, INSET)).convert("RGB")
    px = im.load()
    x0, y0, x1, y1 = BOX
    wall = px[450, 235]
    mask = Image.new("L", im.size, 0)
    mp = mask.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            if sum(abs(a - b) for a, b in zip(px[x, y], wall)) > WALL_DIST:
                mp[x, y] = 255
    mask = mask.filter(ImageFilter.MaxFilter(5))   # 연필 가장자리까지
    mp = mask.load()
    out = im.copy()
    op = out.load()
    for y in range(y0 - 3, y1 + 3):                # 지움 — 같은 열 위쪽 벽 화소로
        for x in range(x0 - 3, x1 + 3):
            if mp[x, y]:
                op[x, y] = px[x, y - LIFT]
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))   # 창만 — 옮겨서
    lp = layer.load()
    for y in range(y0 - 3, y1 + 3):
        for x in range(x0 - 3, BUTT):
            if mp[x, y]:
                lp[x - SHIFT, y] = (*px[x, y], 255)
    d = ImageDraw.Draw(layer)                      # 자루 끝 둥근 마개(뚝 끊긴 끝 — 판정 527 가드)
    end = BUTT - SHIFT
    d.ellipse([end - 4, Y - 4, end + 3, Y + 4], fill=(150, 108, 62, 255), outline=(95, 65, 40, 255))
    layer = layer.rotate(-TILT, resample=Image.BICUBIC, center=(EDGE, Y))   # 뒤끝을 사울 손 쪽으로 내림
    alpha = layer.getchannel("A")
    ImageDraw.Draw(alpha).rectangle([0, 0, EDGE - 1, layer.height], fill=0)   # 돌기둥 면 왼쪽은 돌이 덮음
    layer.putalpha(alpha)
    out.paste(layer, (0, 0), layer)
    d = ImageDraw.Draw(out)                        # 박힌 자리 — 돌 윤곽선이 촉을 덮고 잔금 두 줄
    line = (135, 130, 105)
    d.line([(EDGE - 1, Y - 10), (EDGE + 1, Y), (EDGE - 1, Y + 12)], fill=line, width=2)
    d.line([(EDGE - 2, Y - 6), (EDGE - 9, Y - 11)], fill=line, width=1)
    d.line([(EDGE - 2, Y + 7), (EDGE - 8, Y + 13)], fill=line, width=1)
    out.save(os.path.join(DST, INSET))
    print(f"[SpearWall] {os.path.join(DST, INSET)}")


if __name__ == "__main__":
    main()
