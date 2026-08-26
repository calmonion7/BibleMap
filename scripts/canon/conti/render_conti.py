#!/usr/bin/env python3
"""goliath_scene.html을 PNG로 찍는다 (task#318 S3).

render_scene.py(앱 경유, 투어 정차지를 캡션으로 찾음)는 이 콘티엔 못 쓴다 — 콘티는 앱 밖의
자립 HTML이다(계획 S3의 렌더 경로 결정). 대신 이 스크립트가 playwright로 `file://`을 직접 연다.

    /opt/homebrew/bin/python3 render_conti.py                    # 전체 콘티 → goliath_scene.png
    /opt/homebrew/bin/python3 render_conti.py --only david       # 다윗 레이어만 (S4 마스크 파생용)
    /opt/homebrew/bin/python3 render_conti.py --only goliath -o /tmp/g.png

`--only <id>`는 svg 직계 <g id="bg|david|goliath"> 중 지정한 것만 남기고 나머지를 숨긴 뒤
찍는다(배경 <rect id="paper">는 항상 남는다 — 이진화 기준면이 있어야 한다).

해상도는 scripts/canon/params.py의 SCENE_SIZE(1216×640)에 맞춘다 — svg의 viewBox·width·height가
이미 그 값이므로 el.screenshot()이 그대로 그 픽셀 크기를 낸다(device_scale_factor=1).
"""
import argparse
import os

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, "goliath_scene.html")
DEFAULT_OUT = os.path.join(HERE, "goliath_scene.png")
LAYER_IDS = ("bg", "david", "goliath")


def render(out, only=None):
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        page = b.new_page(viewport={"width": 1216, "height": 640}, device_scale_factor=1)
        page.goto("file://" + HTML)
        if only:
            if only not in LAYER_IDS:
                raise SystemExit(f"--only는 {LAYER_IDS} 중 하나여야 한다: {only!r}")
            for layer in LAYER_IDS:
                if layer != only:
                    page.eval_on_selector(f"#{layer}", "el => el.style.display = 'none'")
        el = page.query_selector("#conti")
        el.screenshot(path=out)
        b.close()
    print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", choices=LAYER_IDS, help="이 레이어 하나만 찍는다(인물별 잉크 추출용)")
    ap.add_argument("-o", "--out", default=None, help="출력 경로 (기본: goliath_scene.png, --only는 conti/<only>.png)")
    args = ap.parse_args()
    out = args.out or (os.path.join(HERE, f"{args.only}.png") if args.only else DEFAULT_OUT)
    render(out, args.only)
