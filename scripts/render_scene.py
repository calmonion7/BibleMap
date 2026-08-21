#!/usr/bin/env python3
"""장면 하나를 빌드→렌더→고배율 촬영해 PNG로 남긴다 (저작자용 시각 피드백 루프).

**왜 있는가.** 선화 저작 에이전트는 자기 그림을 못 본다 — 좌표를 눈 없이 쓰고 숫자 경계로만
자기검증한다. 그래서 B1~B11을 전부 통과하면서도 "재판하는 장면으로 안 읽힌다", "그림이 이상하다"
같은 지적이 반복됐다. 숫자로는 **무엇으로 읽히는가**를 잴 수 없다. 이 스크립트가 그 눈이다.

    python3 scripts/render_scene.py SamuelCircuitScene
    python3 scripts/render_scene.py GoliathScene --out /tmp/goliath.png --no-build
    python3 scripts/render_scene.py GoliathScene --at 8500   # 절정 뒤(쓰러진 상태)를 본다

빌드와 nginx는 **공유 자원**이다 — 여러 저작자가 동시에 이 스크립트를 돌리면 서로의 반쯤 쓴 파일을
빌드해 실패한다. 저작 에이전트는 **한 번에 하나만** 돌려야 한다(--no-build로 재사용 가능).

`scripts/check.sh`에 배선하지 않는다 — 저작 도구이고 판정 게이트가 아니다.
"""
import argparse
import os
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


def shoot(pw, scene, out, scale, at_ms):
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
        # 지정 시각에 고정한다. **절정 뒤(쓰러짐·이동)도 반드시 봐야 한다** — 드로인 구간만 보면
        # 완성된 그림은 멀쩡한데 절정 후 상태가 깨져 있는 결함을 영원히 놓친다(실제로 그랬다).
        page.evaluate("""(t) => {
          const svg = document.querySelector('[data-sketch-panel] svg');
          if (!svg) return;
          for (const a of svg.getAnimations({subtree:true})) { a.pause(); a.currentTime = t; }
          if (svg.pauseAnimations) { svg.pauseAnimations(); svg.setCurrentTime(t / 1000); }
        }""", at_ms)
        page.wait_for_timeout(200)
        el = page.query_selector("[data-sketch-panel]")
        if not el:
            sys.exit("패널이 렌더되지 않았다")
        el.screenshot(path=out)
        print(f"저장: {out}  (배율 {scale}x, 콘솔에러 {len(errs)}건)")
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
    a = ap.parse_args()
    out = a.out or os.path.join(ROOT, ".forge/scratch", f"render-{a.scene}.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if not a.no_build:
        build()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        shoot(pw, a.scene, out, a.scale, a.at)
