"""task#314 S4 1단계 — 정본 두상(David/Goliath) 조건 입력 PNG.

`#/cast` 시트에서 인물 카드의 svg(주역 배율)를 찾아 `position:fixed`로 레이아웃 밖에 고정 배치하고
CSS 크기를 키운 뒤, `getScreenCTM()`으로 로컬 좌표(원본 viewBox "0 0 120 64", cx=60,cy=34 고정)를
화면 좌표로 변환해 `page.screenshot(clip=...)`으로 머리 주변만 클립 촬영한다
(.forge/scratch/task307/crop_heads.py와 같은 기법 — viewBox 자체는 바꾸지 않고 CTM 클립만 쓴다.
element.screenshot()로 시도했다가 카드가 스크롤 컨테이너 안에 있어 헤더와 겹쳐 잘리는 문제를 먼저
겪었다 — position:fixed로 레이아웃에서 완전히 떼어내면 그 문제가 사라진다).

이름표·배율 라벨은 그 svg의 형제 <div>에 있고 svg **안**에는 결코 텍스트가 없다(CastSheet.jsx 구조) —
클립 대상이 svg 자신이므로 글자를 가릴 필요조차 없다.

여백(half-width/top/bottom)은 HEAD_DIAMETER에서 비례 파생한다(정본별로 손으로 다시 재지 않는다):
  half_width = D, top = D*1.1, bottom = D*0.75 — 원 + 머리카락/투구 돌출을 넉넉히 덮는다.
"""
import json
import os
import re
import sys

import params

# 이 BASE는 **로컬 개발 서버 URL**이지 모델 ID가 아니다 — 정본이 모델 쪽을 `SDXL_BASE`로
# 부르는 이유가 이 이름 충돌이다(params.py 주석 참조).
BASE = os.environ.get("BASE", "http://localhost:8080")
ROOT = params.REPO_ROOT
OUT_DIR = params.OUT_ROOT

TARGETS = ["david", "goliath"]
SVG_PX = 6000  # position:fixed로 뗀 svg의 CSS 너비(px) — 120단위 viewBox 기준 50px/단위


def head_diameter(name):
    src = os.path.join(ROOT, "frontend/src/sketches/cast", f"{name}.jsx")
    with open(src, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"export const HEAD_DIAMETER\s*=\s*([0-9.]+)", text)
    if not m:
        sys.exit(f"{src}에서 HEAD_DIAMETER를 찾지 못했다")
    return float(m.group(1))


_PIN_JS = """([name, svgPx, THIN_SW]) => {
  const nameDivs = Array.from(document.querySelectorAll('[data-cast-sheet] div'));
  const nameDiv = nameDivs.find(d => d.firstChild && d.firstChild.nodeType === 3
    && d.firstChild.textContent.trim() === name);
  if (!nameDiv) return { error: 'name-not-found' };
  const row = nameDiv.nextElementSibling;
  const svg = row && row.querySelector('svg');
  if (!svg) return { error: 'svg-not-found' };
  svg.setAttribute('data-shoot-target', name);
  svg.style.setProperty('position', 'fixed', 'important');
  svg.style.setProperty('top', '0', 'important');
  svg.style.setProperty('left', '0', 'important');
  svg.style.setProperty('margin', '0', 'important');
  svg.style.setProperty('z-index', '99999', 'important');
  // 테마 불변 양피지 관용구(tourSketches.jsx TourSketchPanel과 같은 토큰 쌍) — 배경만 바꾸면
  // currentColor(어두운 테마의 밝은 잉크)가 크림 배경 위에서 안 보인다. color도 같이 지정한다.
  svg.style.setProperty('background', 'var(--paper)', 'important');
  svg.style.setProperty('color', 'var(--paper-ink)', 'important');
  svg.style.setProperty('width', svgPx + 'px', 'important');
  svg.style.setProperty('height', Math.round(svgPx * 64 / 120) + 'px', 'important');
  svg.style.setProperty('max-width', 'none', 'important');
  // 조건 입력에는 정본의 **기하만** 필요하다 — 굵기는 화면용이다.
  // 정본 머리는 8단위인데 구조 선이 2.6단위(= 머리 폭의 32%)라, 두상만 잘라 1024px로 키우면
  // 선이 100px대 흰 띠가 되고 다윗의 곱슬 8선은 한 덩어리로 뭉갠다. ControlNet scribble이 그 띠를
  // "굵게 그은 획"으로 읽어 고강도에서 그대로 재현한 것이 빈 타원·아기 얼굴의 뿌리였다
  // (사용자 UAT 2026-08-24). 캡처 시점에만 얇은 균일 굵기로 덮는다 — 소스는 건드리지 않는다.
  // 굵기 구분(구조 선/텍스처 선)은 여기서 의도적으로 버린다: 조건 입력이 나를 것은 형태다.
  let st = document.getElementById('cond-thin-stroke');
  if (!st) {
    st = document.createElement('style');
    st.id = 'cond-thin-stroke';
    document.head.appendChild(st);
  }
  st.textContent = 'svg[data-shoot-target] * { stroke-width: ' + THIN_SW + 'px !important; }';
  return { ok: true };
}"""

_CLIP_JS = """([name, halfW, topM, botM]) => {
  const svg = document.querySelector(`svg[data-shoot-target="${name}"]`);
  if (!svg) return null;
  const ctm = svg.getScreenCTM();
  const cx = 60, cy = 34; // CastCard 호출부 고정값(CastSheet.jsx)
  const p1 = svg.createSVGPoint(); p1.x = cx - halfW; p1.y = cy - topM;
  const p2 = svg.createSVGPoint(); p2.x = cx + halfW; p2.y = cy + botM;
  const a = p1.matrixTransform(ctm), b = p2.matrixTransform(ctm);
  return { x: Math.min(a.x, b.x), y: Math.min(a.y, b.y), width: Math.abs(b.x - a.x), height: Math.abs(b.y - a.y) };
}"""

_TEXT_COUNT_JS = """(name) => {
  const svg = document.querySelector(`svg[data-shoot-target="${name}"]`);
  if (!svg) return null;
  return svg.querySelectorAll('text, tspan, foreignObject').length;
}"""


def shoot(pw):
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={"width": 3600, "height": 2200}, device_scale_factor=1)
    page = ctx.new_page()
    errs = []
    page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errs.append(str(e)))
    meta = {}
    try:
        page.goto(f"{BASE}/#/cast", wait_until="domcontentloaded")
        page.wait_for_selector("[data-cast-sheet]", timeout=15000)
        page.wait_for_timeout(300)
        for name in TARGETS:
            d = head_diameter(name)
            half_w, top_m, bot_m = d, d * 1.1, d * 0.75
            pin = page.evaluate(_PIN_JS, [name, SVG_PX, params.THIN_SW])
            if not pin or pin.get("error"):
                sys.exit(f"{name}: {pin}")
            page.wait_for_timeout(100)
            box = page.evaluate(_CLIP_JS, [name, half_w, top_m, bot_m])
            if not box:
                sys.exit(f"{name}: 클립 계산 실패 — svg를 못 찾음")
            n_text = page.evaluate(_TEXT_COUNT_JS, name)
            if n_text != 0:
                sys.exit(f"{name}: svg 안에 글자 {n_text}개 — 촬영하지 않는다")
            out = os.path.join(OUT_DIR, f"cond-{name}.png")
            page.screenshot(path=out, clip=box)
            print(f"저장: {out}  clip={box}  half_w={half_w:.2f} top={top_m:.2f} bot={bot_m:.2f} text_nodes={n_text}")
            meta[name] = {
                "target": name, "source": f"frontend/src/sketches/cast/{name}.jsx",
                "head_diameter": d, "half_width": half_w, "top_margin": top_m, "bottom_margin": bot_m,
                "clip_box": box, "text_nodes": n_text, "ghost_strokes": 0,
                "path": out,
            }
        if errs:
            print("  ⚠ 콘솔에러:", errs[0][:160])
    finally:
        b.close()
    return meta


if __name__ == "__main__":
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        meta = shoot(pw)
    meta_out = os.path.join(params.NOTES, "cond-heads-meta.json")
    with open(meta_out, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"기록: {meta_out}")
