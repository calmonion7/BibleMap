#!/usr/bin/env python3
"""task 379 — 후보 화면 HTML 검사(Playwright, 이미지 생성 없음).

  /opt/homebrew/bin/python3 check_cand_page.py <task> [<page.html>]   # 없으면 게시본 자리(~/.local/biblemap-imggen/pages/<묶음>-cand.html)
  /opt/homebrew/bin/python3 check_cand_page.py 376 --build            # 376 그림으로 검사용 사본을 새로 만들어 검사(게시본은 그대로)

검사: ① 16MB 이하 ② 화면 수 ≤ 2 × (장면 − 되돌림) + 되돌림 ③ 360px·1280px에서 화면마다 가로 넘침 0(끝까지 답하며 넘김)
④ 쉼 뺀 타이머 — 가짜 시계로 입력 → 60초 뒤 입력(쌓임) → 3분 멈춤 뒤 입력(빠짐) → active_minutes = 1.0, 벽시계 human_minutes ≥ 4.
하나라도 어기면 exit 1."""
import json, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "batch"))


def screens(page):
    t = open(page, encoding="utf-8").read()
    i = t.index("const SCENES")
    sc = json.JSONDecoder().raw_decode(t[t.index("=", i) + 1:].lstrip())[0]
    return sc, len(t.encode("utf-8"))


def walk(pg):
    """끝 화면까지 답하며 넘긴다 — 화면마다 가로 넘침을 잰다."""
    over, n = [], 0
    for _ in range(200):
        n += 1
        w = pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
        if w[0] > w[1] + 1:
            over.append((n, w))
        for sel in ("#ok", "#agree", "#next:not([hidden])"):
            b = pg.query_selector(sel)
            if b and b.is_visible():
                b.click()
                break
        else:
            return over, n   # 끝 화면(답 단추 없음)
    return over, n


def main():
    from playwright.sync_api import sync_playwright
    import make_cand_page as C
    import judge_items as J
    task = int(sys.argv[1])
    page = next((a for a in sys.argv[2:] if a.endswith(".html")), None)
    if "--build" in sys.argv:
        page = os.path.join(tempfile.mkdtemp(prefix="cand-check-"), C.dst(task))
        C.main(task, out=page)
    page = page or os.path.join(J.PAGES, C.dst(task))
    sc, size = screens(page)
    rej = sum(1 for s in sc if s["reject"])
    bad = []
    if size > 16 * 1024 * 1024:
        bad.append(f"크기 {size / 1e6:.2f}MB > 16MB")
    n_screens = 2 * (len(sc) - rej) + rej
    print(f"[CandCheck] {page} {size / 1e6:.2f}MB · 장면 {len(sc)} · 되돌림 {rej} · 화면 {n_screens}", flush=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        for vw in (360, 1280):
            ctx = b.new_context(viewport={"width": vw, "height": 800})
            pg = ctx.new_page()
            pg.goto("file://" + page)
            over, n = walk(pg)
            if n - 1 != n_screens:
                bad.append(f"{vw}px 넘긴 화면 {n - 1} ≠ {n_screens}")
            if over:
                bad.append(f"{vw}px 가로 넘침 {over[:3]}")
            print(f"[CandCheck] {vw}px 화면 {n - 1} · 가로 넘침 {len(over)}", flush=True)
            ctx.close()
        ctx = b.new_context(viewport={"width": 360, "height": 800})
        pg = ctx.new_page()
        pg.clock.install()
        pg.goto("file://" + page)
        pg.mouse.click(5, 5)                 # 첫 입력 — 기준점
        pg.clock.fast_forward(60_000)
        pg.mouse.click(5, 5)                 # 60초 — 쌓임
        pg.clock.fast_forward(180_000)
        pg.mouse.click(5, 5)                 # 3분 멈춤 — 쉼, 빠짐
        v = pg.evaluate("verdict()")
        a, h = v["active_minutes"], v["human_minutes"]
        first = next(iter(v["scenes"].values()))
        if abs(a - 1.0) > 0.02 or h < 4.0 or abs(first["active_minutes"] - 1.0) > 0.02:
            bad.append(f"타이머 active {a} · 첫 장면 {first['active_minutes']} · 벽시계 {h}")
        print(f"[CandCheck] 타이머 쉼 뺀 {a}분 · 첫 장면 {first['active_minutes']}분 · 벽시계 {h}분", flush=True)
        b.close()
    print(f"[CandCheck] {'불통: ' + ' / '.join(bad) if bad else '통과'}", flush=True)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
