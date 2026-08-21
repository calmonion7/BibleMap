#!/usr/bin/env python3
"""투어별 스케치 청크 분할 실물 UAT (task#287 S2).

`backend/scripts/validate_scene_coverage.py`가 **소스 정합**(투어↔모듈 매핑·오배치·미연결)을
단언하고, 이 스크립트는 그 배선이 **실제 브라우저에서 그림이 되고, 실제로 그 투어 것만 내려오는지**
를 잰다. 정적 청크 목록만 보면 "쪼갰지만 어차피 전부 로드"를 통과시킨다 — 그래서 네트워크를 본다.

측정 축 4가지:
  ① 9투어 전부의 첫 정차지에서 스케치가 렌더된다(stroke > 0)
  ② `#/intro` 오프닝 몽타주 5씬이 전부 렌더된다
  ③ **격리** — 한 투어를 재생하는 동안 다른 투어의 스케치 청크가 요청되지 않는다
  ④ 카드 높이 점프 0 — 패널이 뜬 뒤 높이가 변하지 않는다(모듈 로드가 끝나며 글이 들어와도)

**`scripts/check.sh`에 배선하지 않는다.** `deploy.sh`는 빌드 **전**에 check.sh를 부르므로 그 시점의
:8080은 옛 빌드를 서빙한다(`uat_intro_gutter.py`가 확립한 이유).

실행법 (프론트 빌드 + nginx 재시작이 선행 조건):
    python3 scripts/uat_tour_chunk_split.py

종료 코드: 0 = 통과 · 1 = 제품 결함 · 2 = 측정 환경 이상(자).
"""
import json
import os
import re
import sys

BASE = os.environ.get("BASE", "http://localhost:8080")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, ".forge/reports/tour-chunk-split")
HEIGHT_TOLERANCE_PX = 1.0   # 서브픽셀 반올림 허용
SETTLE_MS = 2600            # 450ms 대기 + 모듈 로드 + 여유

# 투어 id → 청크 파일명에 박히는 모듈명(vite가 모듈명을 청크명에 유지한다).
TOUR_MODULE = {
    "creation-to-flood": "creationToFlood",
    "patriarchs-covenant": "patriarchsCovenant",
    "exodus-to-conquest": "exodusToConquest",
    "age-of-judges": "ageOfJudges",
    "david-united-kingdom": "davidUnitedKingdom",
    "elijah-and-elisha": "elijahAndElisha",
    "exile-and-return": "exileAndReturn",
    "gospel-of-jesus": "gospelOfJesus",
    "the-early-church": "theEarlyChurch",
}

# 패널이 처음 뜬 뒤의 높이 변화를 기록한다 — 폴링이 아니라 관찰자로 잡아야 프레임을 놓치지 않는다.
_WATCH = """() => {
  // header가 뜬 뒤에 설치한다 — init script 시점엔 문서가 비어 있어 관찰자가 조용히 죽고
  // 높이 표본 0건이 "점프 0px"라는 거짓 초록이 된다(첫 두 측정에서 실제로 그랬다).
  window.__h = [];
  window.__watchOn = true;
  new MutationObserver(() => {
    const p = document.querySelector('[data-sketch-panel]');
    if (!p || p.__watched) return;
    p.__watched = true;
    window.__h.push(p.getBoundingClientRect().height);
    new ResizeObserver(es => { for (const e of es) window.__h.push(e.target.getBoundingClientRect().height); })
      .observe(p);
  }).observe(document.body, { childList: true, subtree: true });
}"""

_PROBE = """() => {
  const p = document.querySelector('[data-sketch-panel]');
  const svg = p && p.querySelector('svg');
  return {
    panel: !!p,
    strokes: svg ? svg.querySelectorAll('path, circle, ellipse, line, polyline, rect').length : 0,
    heights: window.__h || [],
    watchOn: !!window.__watchOn,
  };
}"""

# 몽타주 SVG만 고른다 — 장면 스케치는 viewBox "0 0 120 64"이고 인물 인장은 64×64라 구조로 갈린다.
# 앞선 측정에서 '모든 svg 중 stroke>2'로 셌더니 인장을 세고 몽타주 미렌더를 통과시켰다(거짓 초록).
_INTRO_PROBE = """() => {
  const s = document.querySelector('svg[viewBox="0 0 120 64"]');
  if (!s) return null;
  const strokes = s.querySelectorAll('path, circle, ellipse, line, polyline, rect');
  if (strokes.length <= 2) return null;
  const head = [...strokes].slice(0, 3).map(e => e.getAttribute('d') || e.outerHTML).join('|');
  return { n: strokes.length, sig: strokes.length + ':' + head.slice(0, 120) };
}"""


def _sketch_chunks(urls):
    """요청된 URL 중 스케치 모듈 청크만 → 모듈명 집합."""
    out = set()
    for u in urls:
        m = re.search(r"/assets/([A-Za-z]+)-[A-Za-z0-9_-]+\.js$", u)
        if m and m.group(1) in set(TOUR_MODULE.values()) | {"introMontage"}:
            out.add(m.group(1))
    return out


# 모바일은 폭이 좁아 desc가 줄바꿈될 수 있다 — 높이 점프 리스크가 데스크톱보다 크다.
VIEWPORTS = {"desktop": {"width": 1280, "height": 900}, "mobile": {"width": 390, "height": 844}}


def run(pw, view="desktop"):
    os.makedirs(OUT, exist_ok=True)
    browser = pw.chromium.launch()
    vp = VIEWPORTS[view]
    rows, env_bad, prod_bad = [], [], []
    try:
        # ── ①③④ 9투어 ──────────────────────────────────────────────────────
        for tour, module in TOUR_MODULE.items():
            ctx = browser.new_context(viewport=vp, is_mobile=(view == "mobile"),
                                      has_touch=(view == "mobile"))
            page = ctx.new_page()
            urls, errors = [], []
            page.on("request", lambda r: urls.append(r.url))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            try:
                r = page.goto(f"{BASE}/#/tour/{tour}", wait_until="domcontentloaded")
                if not r or r.status != 200:
                    env_bad.append(f"{tour}: HTTP {r.status if r else '무응답'}")
                    continue
                page.wait_for_selector("header", timeout=15000)
                page.evaluate(_WATCH)
                page.get_by_role("button", name="투어 재생", exact=False).first.click(timeout=15000)
                page.wait_for_selector("[data-sketch-panel]", timeout=15000)
                page.wait_for_timeout(SETTLE_MS)
                probe = page.evaluate(_PROBE)
                loaded = _sketch_chunks(urls)
                strangers = sorted(loaded - {module, "introMontage"})
                heights = [round(h, 2) for h in probe["heights"]]
                jump = round(max(heights) - min(heights), 2) if heights else 0.0
                rows.append({"tour": tour, "module": module, "strokes": probe["strokes"],
                             "chunks": sorted(loaded), "strangers": strangers,
                             "heights": heights, "jump": jump, "console_errors": errors})
                if not probe["watchOn"] or not heights:
                    env_bad.append(f"{tour}: 높이 관찰자가 표본을 못 남겼다 — 측정이 실행되지 않았다")
                if not probe["panel"] or probe["strokes"] == 0:
                    prod_bad.append(f"{tour}: 스케치가 렌더되지 않았다(stroke {probe['strokes']})")
                if strangers:
                    prod_bad.append(f"{tour}: 다른 투어 청크가 요청됐다 {strangers} — 격리 실패")
                if jump > HEIGHT_TOLERANCE_PX:
                    prod_bad.append(f"{tour}: 패널 높이 점프 {jump}px (허용 {HEIGHT_TOLERANCE_PX})")
                if errors:
                    prod_bad.append(f"{tour}: 콘솔 에러 {len(errors)}건 — {errors[0][:100]}")
            finally:
                ctx.close()

        # ── ② 인트로 몽타주 ────────────────────────────────────────────────
        ctx = browser.new_context(viewport=vp, is_mobile=(view == "mobile"),
                                  has_touch=(view == "mobile"))
        page = ctx.new_page()
        urls, errors = [], []
        page.on("request", lambda r: urls.append(r.url))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        try:
            page.goto(f"{BASE}/#/intro", wait_until="domcontentloaded")
            page.wait_for_selector("header", timeout=15000)
            # 몽타주는 인트로 비트 ③(BEAT_MS=[3000,5000,5000,...])이라 8초 후 시작해 5초간
            # 5씬을 1초 간격으로 순환한다. 그 전에 재면 몽타주에 도달조차 못 한다(첫 측정의 결함).
            page.wait_for_timeout(8200)
            sigs, samples = set(), 0
            for _ in range(24):
                r = page.evaluate(_INTRO_PROBE)
                if r:
                    sigs.add(r["sig"]); samples += 1
                page.wait_for_timeout(220)
            drawn = len(sigs)
            print(f"  · 인트로 몽타주 표본 {samples}회 · 구별된 장면 {drawn}종")
            loaded = _sketch_chunks(urls)
            tour_chunks = sorted(loaded - {"introMontage"})
            page.screenshot(path=os.path.join(OUT, f"intro-montage-{view}.png"))
            rows.append({"tour": "#/intro", "module": "introMontage", "strokes": drawn,
                         "chunks": sorted(loaded), "strangers": tour_chunks,
                         "heights": [], "jump": 0.0, "console_errors": errors})
            if drawn == 0:
                prod_bad.append("#/intro: 몽타주 선화가 하나도 렌더되지 않았다")
            elif drawn < 5:
                prod_bad.append(f"#/intro: 몽타주 5씬 중 {drawn}종만 렌더됐다(표본 {samples})")
            if "introMontage" not in loaded:
                prod_bad.append("#/intro: introMontage 청크가 요청되지 않았다 — 몽타주가 실제로 로드되지 않았다")
            if tour_chunks:
                prod_bad.append(f"#/intro: 투어 청크가 요청됐다 {tour_chunks} — 인트로가 소형 청크만 받아야 한다")
            if errors:
                prod_bad.append(f"#/intro: 콘솔 에러 {len(errors)}건 — {errors[0][:100]}")
        finally:
            ctx.close()
    finally:
        browser.close()

    with open(os.path.join(OUT, f"measurements-{view}.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"=== 투어 청크 분할 UAT — view={view} ({vp['width']}x{vp['height']}) · {BASE} ===")
    for r in rows:
        print(f"  {r['tour']:22} stroke {r['strokes']:3} · 청크 {r['chunks']} · "
              f"타투어 {r['strangers'] or '없음'} · 높이점프 {r['jump']}px · 에러 {len(r['console_errors'])}")
    if env_bad:
        for m in env_bad:
            print(f"  ⚠ 환경: {m}")
        return 2
    if prod_bad:
        for m in prod_bad:
            print(f"  ✗ {m}")
        return 1
    if len(rows) != len(TOUR_MODULE) + 1:
        print(f"  ⚠ 환경: {len(rows)}/{len(TOUR_MODULE) + 1}건만 측정됨")
        return 2
    print(f"PASS — 9투어 + 인트로, 격리 위반 0 · 높이 점프 0 · 콘솔 에러 0")
    return 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--mobile", action="store_true", help="폰 폭(390x844)으로 측정")
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        sys.exit(run(pw, "mobile" if a.mobile else "desktop"))
