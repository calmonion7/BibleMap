#!/usr/bin/env python3
"""장면 세밀화 파일럿 3장면 실물 UAT + 필름스트립 (task#286 S5).

`backend/scripts/validate_scene_sketch_detail.py`가 **소스 경계**(B1~B6)를 단언하고,
이 스크립트는 그 선언이 **실제 브라우저에서 그림이 됐는지**를 잰다. 둘은 서로를 대신하지
못한다 — 소스에 선이 36개 적혀 있어도 렌더가 죽으면 화면은 비어 있고(커버됨 = 화면에
그려진다, task#259), 반대로 렌더는 되는데 브라우저가 계산한 실제 애니메이션 종료 시각이
정적 파싱과 다르면 경계가 거짓 초록이 된다.

측정 방법 — **애니메이션을 멈추고 시각을 스크럽한다.** 흘러가는 애니메이션을 타이머로 쫓으면
프레임이 어긋나 필름스트립이 비결정적이 된다. 그래서 CSS(WAAPI)는 `pause()` + `currentTime`,
SMIL은 `pauseAnimations()` + `setCurrentTime()`으로 같은 시각에 고정한 뒤 찍는다.

**`scripts/check.sh`에 배선하지 않는다.** `deploy.sh`는 빌드 **전**에 check.sh를 부르므로 그
시점의 :8080은 옛 빌드를 서빙한다(`uat_intro_gutter.py`가 확립한 이유). 게이트에는 브라우저
없이 항상 도는 소스 불변식(validate_scene_sketch_detail)만 둔다.

실행법 (프론트 빌드 + nginx 재시작이 선행 조건):
    python3 scripts/uat_scene_detail_pilot.py --phase before   # 재작도 전 대조 프레임
    python3 scripts/uat_scene_detail_pilot.py --phase after    # 재작도 후 + 경계 판정
    python3 scripts/uat_scene_detail_pilot.py --phase after --mobile   # 폰 폭(하단 시트 레이아웃)
    BASE=http://localhost:8080 python3 scripts/uat_scene_detail_pilot.py --phase after

종료 코드: 0 = 통과 · 1 = 제품 결함 · 2 = 측정 환경 이상(자).
실패 계층을 구별하지 않으면 백지 렌더를 "규약 위반"으로 위장해 없는 결함에 fix-forward를 태운다.
"""
import argparse
import json
import os
import sys

BASE = os.environ.get("BASE", "http://localhost:8080")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, ".forge/reports/scene-detail-pilot")
PANEL_DELAY_MS = 450
MAX_DRAWIN_MS = 7000
MIN_STROKES = 30
FRAME_FRACTIONS = [0.0, 0.25, 0.5, 0.75, 1.0]  # 드로인 구간 필름스트립
NAV_LIMIT = 60                                  # 정차지 순회 상한(무한 클릭 방지)

# (라벨, 투어 id, 패널 캡션, step 예산 ms) — 캡션으로 찾는다(정차지 인덱스 드리프트에 강함).
TARGETS = [
    ("SamuelCircuitScene", "age-of-judges", "순회 재판 — 사무엘상 7장", 9440),
    ("TransfigurationScene", "gospel-of-jesus", "변화산 — 마태복음 17장", 10000),
    ("GoliathScene", "david-united-kingdom", "다윗과 골리앗 — 사무엘상 17장", 9520),
]

# 패널 안 stroke 수 · CSS 애니메이션 종료 시각 · SMIL begin(ms)을 한 번에 걷어온다.
_PROBE = """() => {
  const panel = document.querySelector('[data-sketch-panel]');
  if (!panel) return { error: 'no-panel' };
  const svg = panel.querySelector('svg');
  if (!svg) return { error: 'no-svg' };
  const strokes = svg.querySelectorAll('path, circle, ellipse, line, polyline, rect');
  let end = 0;
  for (const a of svg.getAnimations({ subtree: true })) {
    const t = a.effect && a.effect.getComputedTiming();
    if (t && isFinite(t.endTime)) end = Math.max(end, t.endTime);
  }
  // 절정(장면 SMIL)과 이름표 페이드인을 구조로 가른다 — <text> 하위 <animate>는 Label의
  // opacity 페이드인이며(SceneLabel.jsx: "대상이 그려진 뒤 페이드인") 캡션이지 절정이 아니다.
  // B5는 '절정'을 말하므로 이름표를 섞으면 검사가 정적 판정과 어긋난다. 제외분도 함께 보고한다.
  const smil = [], labels = [];
  for (const el of svg.querySelectorAll('animate, animateTransform, animateMotion, set')) {
    const b = (el.getAttribute('begin') || '').trim();
    const m = b.match(/^([0-9.]+)(ms|s)?$/);
    if (!m) continue;
    const ms = m[2] === 'ms' ? +m[1] : +m[1] * 1000;
    (el.closest('text') ? labels : smil).push(ms);
  }
  return { strokes: strokes.length, drawinEnd: Math.round(end), smil, labels,
           caption: (panel.textContent || '').trim().slice(0, 120) };
}"""

# 시각 t(ms)에 CSS·SMIL을 동시에 고정 — 필름스트립이 결정적이 된다.
_SCRUB = """(t) => {
  const svg = document.querySelector('[data-sketch-panel] svg');
  if (!svg) return false;
  for (const a of svg.getAnimations({ subtree: true })) { a.pause(); a.currentTime = t; }
  if (svg.pauseAnimations) { svg.pauseAnimations(); svg.setCurrentTime(t / 1000); }
  return true;
}"""


def _seek_stop(page, caption):
    """재생을 켜고 즉시 일시정지한 뒤, 캡션이 맞는 정차지까지 '다음'으로 이동."""
    page.get_by_role("button", name="투어 재생", exact=False).first.click(timeout=15000)
    page.wait_for_selector('[aria-label="일시정지"], [aria-label="재생"]', timeout=15000)
    pause = page.query_selector('[aria-label="일시정지"]')
    if pause:
        pause.click()
    for _ in range(NAV_LIMIT):
        panel = page.query_selector("[data-sketch-panel]")
        if panel and caption in (panel.text_content() or ""):
            return True
        nxt = page.query_selector('[aria-label="다음 정차지"]')
        if not nxt or not nxt.is_enabled():
            return False
        nxt.click()
        page.wait_for_timeout(120)
    return False


def _shoot(page, out_dir, label, drawin_end, after_ms=None):
    """드로인 구간을 등분해 찍고, **절정 뒤 상태도 한 장 더** 찍는다.
    드로인 구간만 보면 완성된 그림은 멀쩡한데 절정(쓰러짐·이동) 후 상태가 깨진 결함을 못 본다 —
    골리앗이 쓰러진 뒤 몸이 지면 아래로 뚫고 나간 것을 이 프레임이 없어서 놓쳤다."""
    os.makedirs(out_dir, exist_ok=True)
    span = max(drawin_end, 1000)
    paths = []
    marks = [(f"{int(f * 100):03d}", round(span * f)) for f in FRAME_FRACTIONS]
    if after_ms:
        marks.append(("after", round(after_ms)))
    for name, t in marks:
        page.evaluate(_SCRUB, t)
        page.wait_for_timeout(60)
        p = os.path.join(out_dir, f"{label}-{name}.png")
        el = page.query_selector("[data-sketch-panel]")
        (el or page).screenshot(path=p)
        paths.append(p)
    return paths


# 모바일에선 해설 카드가 하단 시트로 바뀌고(MOBILE_BREAKPOINT=768) 폭이 좁아 desc가 줄바꿈될 수
# 있다 — 데스크톱 폭만 재면 그 레이아웃을 한 번도 보지 않는다.
VIEWPORTS = {"desktop": {"width": 1280, "height": 900}, "mobile": {"width": 390, "height": 844}}


def run(pw, phase, view="desktop"):
    out_dir = os.path.join(OUT, phase if view == "desktop" else f"{phase}-{view}")
    browser = pw.chromium.launch()
    rows, env_bad, prod_bad = [], [], []
    try:
        for label, tour, caption, step_ms in TARGETS:
            ctx = browser.new_context(viewport=VIEWPORTS[view],
                                      is_mobile=(view == "mobile"), has_touch=(view == "mobile"))
            page = ctx.new_page()
            errors = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            try:
                r = page.goto(f"{BASE}/#/tour/{tour}", wait_until="domcontentloaded")
                if not r or r.status != 200:
                    env_bad.append(f"{label}: HTTP {r.status if r else '무응답'}")
                    continue
                page.wait_for_selector("header", timeout=15000)
                if not _seek_stop(page, caption):
                    env_bad.append(f"{label}: 정차지('{caption}')에 도달하지 못했다")
                    continue
                page.wait_for_timeout(PANEL_DELAY_MS + 200)
                probe = page.evaluate(_PROBE)
                if probe.get("error"):
                    prod_bad.append(f"{label}: 패널 렌더 실패({probe['error']})")
                    continue
                drawin = probe["drawinEnd"]
                # 절정 뒤 상태: 마지막 연출 종료 + 200ms
                tail = max(probe["smil"] + probe["labels"] + [drawin]) + 200
                frames = _shoot(page, out_dir, label, drawin, after_ms=tail)
                row = {
                    "label": label, "tour": tour, "phase": phase, "view": view,
                    "strokes": probe["strokes"], "drawin_ms": drawin,
                    "smil_ms": sorted(probe["smil"]), "label_ms": sorted(probe["labels"]), "step_ms": step_ms,
                    "console_errors": errors, "frames": [os.path.relpath(f, ROOT) for f in frames],
                }
                rows.append(row)
                if phase == "after":
                    if probe["strokes"] < MIN_STROKES:
                        prod_bad.append(f"{label}: 렌더된 stroke {probe['strokes']}개 < {MIN_STROKES}")
                    if drawin > MAX_DRAWIN_MS:
                        prod_bad.append(f"{label}: 실측 드로인 {drawin}ms > {MAX_DRAWIN_MS}ms")
                    if PANEL_DELAY_MS + drawin > step_ms:
                        prod_bad.append(
                            f"{label}: 대기 {PANEL_DELAY_MS}+드로인 {drawin} > step {step_ms}ms")
                    early = [b for b in probe["smil"] if b < drawin]
                    if early:
                        prod_bad.append(f"{label}: 절정이 드로인 종료 전에 터진다 {early}")
                    if errors:
                        prod_bad.append(f"{label}: 콘솔 에러 {len(errors)}건 — {errors[0][:100]}")
            finally:
                ctx.close()
    finally:
        browser.close()

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "measurements.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"=== 장면 세밀화 파일럿 UAT — phase={phase} · view={view} "
          f"({VIEWPORTS[view]['width']}x{VIEWPORTS[view]['height']}) · {BASE} ===")
    for r in rows:
        print(f"  {r['label']}: {r['strokes']}선 · 실측 드로인 {r['drawin_ms']}ms · "
              f"절정SMIL {r['smil_ms']} · 이름표 {r['label_ms']} · step {r['step_ms']}ms · "
              f"콘솔에러 {len(r['console_errors'])}건")
    if env_bad:
        for m in env_bad:
            print(f"  ⚠ 환경: {m}")
        return 2
    if prod_bad:
        for m in prod_bad:
            print(f"  ✗ {m}")
        return 1
    if len(rows) != len(TARGETS):
        print(f"  ⚠ 환경: {len(rows)}/{len(TARGETS)}장면만 측정됨")
        return 2
    print(f"PASS — {len(rows)}장면, 필름스트립 {len(FRAME_FRACTIONS)}프레임씩 {out_dir}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["before", "after"], required=True)
    ap.add_argument("--mobile", action="store_true", help="폰 폭(390x844)으로 측정 — 하단 시트 레이아웃")
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        sys.exit(run(pw, a.phase, "mobile" if a.mobile else "desktop"))
