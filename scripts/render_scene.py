#!/usr/bin/env python3
"""장면 하나를 빌드→렌더→고배율 촬영해 PNG로 남긴다 (저작자용 시각 피드백 루프).

**왜 있는가.** 선화 저작 에이전트는 자기 그림을 못 본다 — 좌표를 눈 없이 쓰고 숫자 경계로만
자기검증한다. 그래서 B1~B11을 전부 통과하면서도 "재판하는 장면으로 안 읽힌다", "그림이 이상하다"
같은 지적이 반복됐다. 숫자로는 **무엇으로 읽히는가**를 잴 수 없다. 이 스크립트가 그 눈이다.

    python3 scripts/render_scene.py SamuelCircuitScene
    python3 scripts/render_scene.py GoliathScene --out /tmp/goliath.png --no-build
    python3 scripts/render_scene.py GoliathScene --at 8500   # 절정 뒤(쓰러진 상태)를 본다
    python3 scripts/render_scene.py SamuelCircuitScene --min-stroke-width 2.0,1.8,1.4,1.3,0
                                                             # 감선 계단 — 굵기 임계별로 한 장씩

`--min-stroke-width`는 **굵기로 선을 깎아 밀도 계단**을 만든다(task#305 최소 선 밀도 측정).
단위는 `sw(n, o)`의 n이고, 임계는 `lib.jsx`의 `W`를 **파생**해 DOM 굵기(n x W)로 환산한다 —
W를 이 스크립트에 복사하면 누가 W를 바꿨을 때 계단이 조용히 어긋난다
(ADR 260820-003946 · 260821-000937). 계단 여러 개를 쉼표로 주면 **한 브라우저 세션에서**
전부 촬영한다 — 투어 정차지 탐색이 불안정하고 빌드·nginx가 공유 자원이라, 계단마다 프로세스를
새로 띄우면 실패 확률과 벽시계가 계단 수만큼 곱해진다(task#303 이탈 2).

빌드와 nginx는 **공유 자원**이다 — 여러 저작자가 동시에 이 스크립트를 돌리면 서로의 반쯤 쓴 파일을
빌드해 실패한다. 저작 에이전트는 **한 번에 하나만** 돌려야 한다(--no-build로 재사용 가능).

`scripts/check.sh`에 배선하지 않는다 — 저작 도구이고 판정 게이트가 아니다.
"""
import argparse
import os
import re
import subprocess
import sys

BASE = os.environ.get("BASE", "http://localhost:8080")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 장면 → (투어 id, 패널 캡션). 캡션으로 정차지를 찾는다(인덱스 드리프트에 강함).
SCENES = {
    "SamuelCircuitScene": ("age-of-judges", "순회 재판 — 사무엘상 7장"),
    "TransfigurationScene": ("gospel-of-jesus", "변화산 — 마태복음 17장"),
    "GoliathScene": ("david-united-kingdom", "다윗과 골리앗 — 사무엘상 17장"),
}


def stroke_scale():
    """`sw(n)`이 DOM에 내보내는 굵기 배율 W를 lib.jsx에서 파생한다(복사 금지 — 위 docstring 참조)."""
    src = os.path.join(ROOT, "frontend/src/sketches/lib.jsx")
    with open(src, encoding="utf-8") as f:
        m = re.search(r"^export const W\s*=\s*([0-9.]+)", f.read(), re.M)
    if not m:
        sys.exit("lib.jsx에서 export const W를 찾지 못했다 — 굵기 배율이 바뀌었다면 이 스크립트도 갱신하라")
    return float(m.group(1))


# sw()는 n*W를 toFixed(2)로 반올림해 내보낸다 — 임계와 정확히 같은 굵기의 선이 반올림 오차로
# 탈락하지 않도록 반올림 단위의 절반을 여유로 둔다.
_ROUND_TOL = 0.006

# 굵기 임계로 선을 숨기고 (전체, 잔존) 수를 돌려준다. stroke가 없는 요소(이름표 상자 등)는
# 밀도에 세지 않는다 — 검증기의 밀도 정의와 같은 기준(stroke 요소만)을 쓴다.
# **`display`로 숨기지 않는다.** display:none이 된 요소는 CSS 애니메이션을 잃고, 되살릴 때 0부터
# 다시 시작한다 — 계단을 여러 장 찍으면 두 번째 이후가 '점 무더기'로 촬영된다(선이 dash 애니메이션
# 시작 지점에 걸려 있다). `visibility`는 애니메이션을 재시작시키지 않는다. 그래도 안전판으로
# 필터 뒤에 동결을 한 번 더 건다(_FREEZE_JS).
_FILTER_JS = """([th, tol]) => {
  const panel = document.querySelector('[data-sketch-panel]');
  const svg = panel && panel.querySelector('svg');
  if (!svg) return null;
  let total = 0, kept = 0;
  for (const el of svg.querySelectorAll('path,circle,ellipse,line,polyline,rect')) {
    el.style.removeProperty('visibility');
    const cs = getComputedStyle(el);
    if (cs.stroke === 'none' || cs.stroke === 'transparent') continue;
    total++;
    const w = parseFloat(cs.strokeWidth);
    if (w >= th - tol) { kept++; } else { el.style.visibility = 'hidden'; }
  }
  return { total, kept };
}"""

# 지정 시각에 애니메이션을 고정한다. **절정 뒤(쓰러짐·이동)도 반드시 봐야 한다** — 드로인 구간만
# 보면 완성된 그림은 멀쩡한데 절정 후 상태가 깨져 있는 결함을 영원히 놓친다(실제로 그랬다).
_FREEZE_JS = """(t) => {
  const svg = document.querySelector('[data-sketch-panel] svg');
  if (!svg) return;
  for (const a of svg.getAnimations({subtree:true})) { a.pause(); a.currentTime = t; }
  if (svg.pauseAnimations) { svg.pauseAnimations(); svg.setCurrentTime(t / 1000); }
}"""


def build():
    r = subprocess.run(["npm", "run", "build"], cwd=os.path.join(ROOT, "frontend"),
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-2000:], sep="\n")
        sys.exit("빌드 실패 — 위 오류를 먼저 고쳐라")
    subprocess.run(["docker", "compose", "restart", "nginx"], cwd=ROOT,
                   capture_output=True, text=True)
    import time
    time.sleep(3)


def shoot(pw, scene, out, scale, at_ms, rungs=None):
    tour, caption = SCENES[scene]
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={"width": 1280, "height": 900}, device_scale_factor=scale)
    page = ctx.new_page()
    errs = []
    page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errs.append(str(e)))
    try:
        page.goto(f"{BASE}/#/tour/{tour}", wait_until="domcontentloaded")
        page.wait_for_selector("header", timeout=15000)
        page.get_by_role("button", name="투어 재생", exact=False).first.click(timeout=15000)
        page.wait_for_selector('[aria-label="일시정지"], [aria-label="재생"]', timeout=15000)
        pause = page.query_selector('[aria-label="일시정지"]')
        if pause:
            pause.click()
        # 정차지 탐색은 카드 리마운트와 경쟁해 불안정하다 — 패널이 뜬 뒤에 넘기고, 클릭이
        # 씹히면 잠깐 기다렸다 다시 시도한다(끝까지 못 가면 그때 실패로 본다).
        page.wait_for_selector("[data-sketch-panel]", timeout=15000)
        found = False
        for _ in range(80):
            panel = page.query_selector("[data-sketch-panel]")
            if panel and caption in (panel.text_content() or ""):
                found = True
                break
            nxt = page.query_selector('[aria-label="다음 정차지"]')
            if not nxt or not nxt.is_enabled():
                page.wait_for_timeout(400)
                nxt = page.query_selector('[aria-label="다음 정차지"]')
                if not nxt or not nxt.is_enabled():
                    break
            nxt.click()
            page.wait_for_timeout(160)
        if not found:
            sys.exit(f"정차지('{caption}')에 도달하지 못했다 — 재시도해도 안 되면 캡션을 확인하라")
        page.wait_for_timeout(700)
        page.evaluate(_FREEZE_JS, at_ms)
        page.wait_for_timeout(200)
        el = page.query_selector("[data-sketch-panel]")
        if not el:
            sys.exit("패널이 렌더되지 않았다")
        if not rungs:
            el.screenshot(path=out)
            print(f"저장: {out}  (배율 {scale}x, --at {at_ms}, 콘솔에러 {len(errs)}건)")
        else:
            # 감선 계단 — 한 세션에서 임계별로 한 장씩. 임계 0은 전체(무필터)와 같다.
            W = stroke_scale()
            stem, ext = os.path.splitext(out)
            for n in rungs:
                got = page.evaluate(_FILTER_JS, [n * W, _ROUND_TOL])
                if got is None:
                    sys.exit("패널 svg를 찾지 못했다 — 선택자가 바뀌었는지 확인하라")
                page.evaluate(_FREEZE_JS, at_ms)   # 안전판 — 위 _FILTER_JS 주석 참조
                page.wait_for_timeout(120)
                path = f"{stem}-mw{n:g}{ext}"
                el.screenshot(path=path)
                print(f"저장: {path}  임계 n>={n:g} (DOM {n * W:.4f}) "
                      f"선 {got['kept']}/{got['total']}  배율 {scale}x  --at {at_ms}")
        if errs:
            print("  ⚠ 콘솔에러:", errs[0][:160])
    finally:
        b.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("scene", choices=sorted(SCENES))
    ap.add_argument("--out")
    ap.add_argument("--scale", type=int, default=3, help="촬영 배율(기본 3 — 선 겹침이 보인다)")
    ap.add_argument("--no-build", action="store_true", help="빌드·재시작을 생략(직전 빌드 재사용)")
    ap.add_argument("--at", type=int, default=1000000,
                    help="이 시각(ms)에 애니메이션을 고정. 기본은 전부 끝난 상태. "
                         "절정 뒤 상태를 보려면 예: --at 8500")
    ap.add_argument("--min-stroke-width", dest="rungs",
                    help="굵기 임계(sw()의 n)로 선을 깎아 밀도 계단을 만든다. 쉼표로 여러 개를 주면 "
                         "한 세션에서 계단별로 한 장씩 촬영하고 파일명에 -mw<n>을 붙인다. "
                         "0은 전체(무필터). 예: 2.0,1.8,1.4,1.3,0")
    a = ap.parse_args()
    rungs = None
    if a.rungs:
        rungs = [float(v) for v in a.rungs.split(",") if v.strip() != ""]
    out = a.out or os.path.join(ROOT, ".forge/scratch", f"render-{a.scene}.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if not a.no_build:
        build()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        shoot(pw, a.scene, out, a.scale, a.at, rungs)
