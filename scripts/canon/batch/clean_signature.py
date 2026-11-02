"""그림 오른쪽 아래 구석의 서명 같은 낙서를 바로 왼쪽 바탕 화소로 덮는다(task 547 — 놉 t13 s7이 이것 하나로 가드 0/3).

모델이 종종 구석에 「서명」을 그린다(놉 s7 · 배교 s7 「글자 같은 서명」). 구석 BOX만 같은 높이 왼쪽 바탕으로 덮고 이음매를 흐린다 —
작은 부위 손질(규칙 edit.no-paste-large-parts의 「작은 지물·흐름만」 범위) · GPU 0 · 화풍 그대로.

    python3 batch/clean_signature.py <src.png> <dst.png>
"""
import sys

from PIL import Image, ImageDraw, ImageFilter

BOX_W, BOX_H = 56, 30   # 덮을 구석(서명 약 40 × 20화소 + 여유)
SHIFT = 64              # 덮을 바탕을 가져올 왼쪽 거리


def clean(src, dst):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    patch = im.crop((w - BOX_W - SHIFT, h - BOX_H, w - SHIFT, h))
    mask = Image.new("L", (BOX_W, BOX_H), 0)
    ImageDraw.Draw(mask).rectangle([6, 6, BOX_W, BOX_H], fill=255)   # 왼쪽·위 6화소는 이음매로 흐림
    im.paste(patch, (w - BOX_W, h - BOX_H), mask.filter(ImageFilter.GaussianBlur(3)))
    im.save(dst)
    print(f"[CleanSig] {dst}")


if __name__ == "__main__":
    clean(sys.argv[1], sys.argv[2])
