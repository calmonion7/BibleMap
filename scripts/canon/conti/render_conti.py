#!/usr/bin/env python3
"""goliath_scene.html을 PNG로 찍는다 (task#318 S3).

render_scene.py(앱 경유, 투어 정차지를 캡션으로 찾음)는 이 콘티엔 못 쓴다 — 콘티는 앱 밖의
자립 HTML이다(계획 S3의 렌더 경로 결정). 대신 이 스크립트가 playwright로 `file://`을 직접 연다.

    /opt/homebrew/bin/python3 render_conti.py                    # 전체 콘티 → goliath_scene.png
    /opt/homebrew/bin/python3 render_conti.py --only david       # 다윗 레이어만 (S4 마스크 파생용)
    /opt/homebrew/bin/python3 render_conti.py --only david-arm   # 다윗의 물매 든 팔만 (부위 파생용)
    /opt/homebrew/bin/python3 render_conti.py --only goliath -o /tmp/g.png

`--only <id>`는 지정한 것만 남기고 나머지를 숨긴 뒤 찍는다(배경 <rect id="paper">는 항상 남는다 —
이진화 기준면이 있어야 한다). 받는 id는 두 층이다:

  * **레이어** — svg 직계 <g id="bg|david|goliath">
  * **부위** — 그 안의 <g id="david-head|david-torso|david-arm|…"> (task#321 S2)

**고를 수 있는 id 목록은 DOM에서 파생한다 — 여기에 손으로 적지 않는다.** 콘티에 부위 그룹을
더하면 이 스크립트를 고치지 않아도 그 자리에서 선택 가능해진다. 이것이 ADR `260830-084555`
「판정 기하는 저작 원본에서 파생한다」를 부위로 확장하는 방식이고, 문자열·좌표 매칭에 기대지 않는다.

해상도는 scripts/canon/params.py의 SCENE_SIZE(1216×640)에 맞춘다 — svg의 viewBox·width·height가
이미 그 값이므로 el.screenshot()이 그대로 그 픽셀 크기를 낸다(device_scale_factor=1).
"""
import argparse
import os

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, "goliath_scene.html")
DEFAULT_OUT = os.path.join(HERE, "goliath_scene.png")


def _hide(page, el_id):
    page.eval_on_selector(f"#{el_id}", "el => el.style.display = 'none'")


def render(out, only=None):
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        page = b.new_page(viewport={"width": 1216, "height": 640}, device_scale_factor=1)
        page.goto("file://" + HTML)
        if only:
            layers = page.eval_on_selector_all("#conti > g[id]", "els => els.map(e => e.id)")
            parts = dict(page.eval_on_selector_all(
                "#conti > g[id] > g[id]", "els => els.map(e => [e.id, e.parentElement.id])"))
            if only in layers:
                for lid in layers:
                    if lid != only:
                        _hide(page, lid)
            elif only in parts:
                # 부위 하나 = 그 부위의 레이어만 남기고, 그 레이어 안의 형제 부위도 숨긴다.
                for lid in layers:
                    if lid != parts[only]:
                        _hide(page, lid)
                for pid, parent in parts.items():
                    if parent == parts[only] and pid != only:
                        _hide(page, pid)
            else:
                raise SystemExit(f"--only는 {layers + sorted(parts)} 중 하나여야 한다: {only!r}")
        el = page.query_selector("#conti")
        el.screenshot(path=out)
        b.close()
    print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="이 레이어/부위 하나만 찍는다(인물별·부위별 잉크 추출용). "
                                   "고를 수 있는 값은 콘티 DOM에서 파생한다 — 틀리면 목록을 알려준다")
    ap.add_argument("-o", "--out", default=None, help="출력 경로 (기본: goliath_scene.png, --only는 conti/<only>.png)")
    args = ap.parse_args()
    out = args.out or (os.path.join(HERE, f"{args.only}.png") if args.only else DEFAULT_OUT)
    render(out, args.only)
