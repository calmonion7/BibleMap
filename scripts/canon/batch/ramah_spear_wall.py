"""라마 곁 장면 — 다윗 머리 바로 위 뒷벽에 촉부터 박힌 창(사람 판정 task 522 「구름안 창이 벽에박히게」 · 527 「창이 허공을 가로질러
날고 있으며 다윗은 수금을 든 채 서 있어」 · task 535). 527 v1·v2(s11 창을 돌기둥에 수평으로 박음)는 「나는 창」으로 읽혀 거절.

곁 장면은 다윗이 돌기둥 앞에 웅크린 s7, 큰 장면은 사람이 고른 s11 — 합성(inset_try comp)이 같은 seed 이름으로 짝지으므로 s7 곁 장면을 -s11 이름으로 둔다.
s7 창(수평·촉이 사울 쪽)을 벽에서 떼어(같은 열 위쪽 벽 화소로 메움) 좌우로 뒤집고, 촉 쪽 BURY 화소는 벽 속에 묻힌 몫으로 버린 뒤
박힌 자리(TIP)에서 사울 쪽 아래로 DROOP° 처지게 VISIBLE 화소만 얹는다 — 방을 가로지르는 긴 수평 창은 「나는 창」으로 읽힌다.
박힌 자리는 돌기둥 옆면이라 촉이 돌 속으로 사라지는 가림이 박힘을 말한다(뒷벽에 박고 벽 그림자를 준 535 v3은 「공중에 뜬 창·속도선」 0/5). GPU 0 · 화소 편집만(화풍 그대로 — ADR 261030-011200).

    python3 batch/ramah_spear_wall.py   →  ~/.local/biblemap-imggen/ramah-inset-wall2/ 에 곁 장면(s7 → -s11)·큰 장면 s11
    python3 batch/inset_try.py comp --main authored-david-ramah-samuel --dir ramah-inset-wall2 --seeds 11
"""
import os
import shutil

from PIL import Image, ImageDraw, ImageFilter

SRC = os.path.expanduser("~/.local/biblemap-imggen/ramah-inset-r2")
DST = os.path.expanduser("~/.local/biblemap-imggen/ramah-inset-wall2")
INSET_SRC = "authored-david-ramah-samuel-inset-s7.png"
INSET_DST = "authored-david-ramah-samuel-inset-s11.png"
MAIN = "authored-david-ramah-samuel-s11.png"
BOX = (180, 268, 610, 298)   # s7 창이 든 띠(뒤끝 190 ~ 촉 605, y 275~291)
TIP = (205, 290)             # 박힌 자리 — 돌기둥 옆면(x 205) · 촉이 돌 속으로 사라짐(가림) · 자루가 다윗 머리(곱슬 위끝 y≈325) 약 20px 위를 지남
BURY = 62                    # 벽 속에 묻힌 촉 쪽 길이(화소) — 촉 꽂이·밑동만 보임(45는 「기둥 모서리에 살짝 닿음」 535 v4)
VISIBLE = 300                # 벽 밖으로 보이는 자루 길이(화소) — 230은 「화살처럼」(535 v4)
DROOP = 8                    # 사울 쪽 아래로 처진 각(도)
LIFT = 38                    # 지운 자리를 메울 벽 화소의 위쪽 거리
WALL_DIST = 40               # 벽 빛과 이만큼 먼 화소 = 창


def main():
    os.makedirs(DST, exist_ok=True)
    shutil.copy(os.path.join(SRC, MAIN), os.path.join(DST, MAIN))
    im = Image.open(os.path.join(SRC, INSET_SRC)).convert("RGB")
    px = im.load()
    x0, y0, x1, y1 = BOX
    wall = px[450, 230]
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
    spear = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sp = spear.load()
    for y in range(y0 - 3, y1 + 3):                # 지움(같은 열 위쪽 벽 화소로) · 창만 떼어 둠
        for x in range(x0 - 3, x1 + 3):
            if mp[x, y]:
                op[x, y] = px[x, y - LIFT]
                dist = sum(abs(a - b) for a, b in zip(px[x, y], wall))
                sp[x, y] = (*px[x, y], max(0, min(255, (dist - 70) * 255 // 40)))   # 벽 빛에 가까운 가장자리·원래 창 밑 그림자는 뺌(테두리·「자루 끝 번짐」 535 v5)
    spear = spear.crop(spear.getbbox()).transpose(Image.FLIP_LEFT_RIGHT)   # 촉이 왼쪽
    cy = spear.height // 2
    seg = spear.crop((BURY, 0, BURY + VISIBLE, spear.height))   # 묻힌 촉 몫은 버리고 보이는 자루만
    ImageDraw.Draw(seg).ellipse([VISIBLE - 7, cy - 4, VISIBLE - 1, cy + 4], fill=(165, 120, 70, 255), outline=(100, 70, 40, 255))   # 둥근 나무 뒤끝(쇠 마개는 「깃」 535 v4)
    big = Image.new("RGBA", (seg.width * 2 + 40,) * 2, (0, 0, 0, 0))   # 자루 앞끝을 가운데에 두고 돌림
    c = big.width // 2
    big.paste(seg, (c, c - cy), seg)
    big = big.rotate(-DROOP, resample=Image.BICUBIC, center=(c, c))
    lay = Image.new("RGBA", out.size, (0, 0, 0, 0))
    lay.paste(big, (TIP[0] - c, TIP[1] - c), big)
    alpha = lay.getchannel("A")
    ImageDraw.Draw(alpha).rectangle([0, 0, TIP[0] - 1, out.height], fill=0)   # 돌기둥 면 왼쪽 = 돌 속(촉이 가려짐)
    lay.putalpha(alpha)
    out.paste(lay, (0, 0), lay)
    d = ImageDraw.Draw(out)                        # 박힌 자리 — 돌 면이 패인 어두운 쐐기와 금
    d.polygon([(TIP[0], TIP[1] - 6), (TIP[0] - 9, TIP[1]), (TIP[0], TIP[1] + 6)], fill=(90, 80, 65))
    for dx, dy in ((-16, -14), (-20, 6), (-8, -20), (-9, 18), (-22, -3)):
        d.line([(TIP[0] - 4, TIP[1]), (TIP[0] + dx, TIP[1] + dy)], fill=(105, 92, 75), width=2)
    w, h = out.size                                # 위·왼쪽 가장자리 띠 잘라냄(가드 「종이 테두리 같은 띠」 535 v4) — 비율 그대로 늘림
    out = out.crop((22, 10, w, h)).resize((w, h), Image.LANCZOS)
    out.save(os.path.join(DST, INSET_DST))
    print(f"[SpearWall] {os.path.join(DST, INSET_DST)} ← {INSET_SRC}")


if __name__ == "__main__":
    main()
