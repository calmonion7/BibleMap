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
    python3 scripts/render_scene.py --cast                 # 설정화 시트(#/cast)를 찍는다(task#307 S1)
    python3 scripts/render_scene.py GoliathScene --at 9000 --no-labels --delay-range 4920,7560
                                                             # delay 범위의 stroke만 찍는다(영역 마스크, task#315 S3)

**`--cast`**는 투어 정차지 탐색을 건너뛰고 개발 전용 라우트 `#/cast`(인물 정본 + 지물 참고 도상 격자,
ADR 260823-190821)를 찍는다. 그 화면엔 애니메이션이 없으므로(정지 시트) 아래 `_FREEZE_JS`/`_FILTER_JS`/
`_VISIBLE_JS`(투어 장면 전용, `[data-sketch-panel]` 가정)를 쓰지 않는다 — 시트 전용 선택자
`[data-cast-sheet]`로 화면 전체를 찍는다(두 선택자 가정이 섞이지 않게 완전히 분리된 경로).

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
import json
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
    "EnGediScene": ("david-united-kingdom", "엔게디 동굴의 자비 — 사무엘상 24장"),
    "GibeahHarpScene": ("david-united-kingdom", "수금과 위로 — 사무엘상 16장"),
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
    if (el.closest('.scene-wash')) continue;   // 마스크 안 복제분(task#306 S4) — 아래 주석 참조
    el.style.removeProperty('visibility');
    const cs = getComputedStyle(el);
    if (cs.stroke === 'none' || cs.stroke === 'transparent') continue;
    total++;
    const w = parseFloat(cs.strokeWidth);
    // !important 필수(task#306 S1) — .scene-draw가 이제 자체 CSS 애니메이션으로 visibility를
    // 몬다(index.css). 애니메이션 값은 cascade에서 author-normal(일반 인라인 스타일 포함)보다
    // 위이므로 !important 없는 인라인 지정은 진행 중/forwards인 애니메이션에 묻힌다.
    if (w >= th - tol) { kept++; } else { el.style.setProperty('visibility', 'hidden', 'important'); }
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

# eco: 읽기 전용 계측 한 줄(task#306 S1) — "그려지는 중인 획만 보이는가"를 육안 대신 숫자로
# 판정하기 위함. stroke 요소 중 getComputedStyle().visibility === 'visible' 개수를 센다.
# 동작(필터·프리즈)은 바꾸지 않는다 — 이 함수는 아무것도 쓰지 않고 세기만 한다.
#
# .scene-wash 제외(task#306 S4) — 채색층 장면은 <mask> 안에서 같은 Scene을 한 번 더 그린다.
# 그 복제분까지 세면 이 도구가 보고하는 "총선"이 실제 잉크 선 수의 2배가 되고(사무엘 197 → 394),
# --min-stroke-width 감선 계단으로 밀도를 재는 사람이 조용히 2배를 읽는다(task#305의 D_human·
# D_model이 이 도구로 측정된 값이다). 잉크만 센다 — 마스크는 연출 장치이고 밀도가 아니다.
_VISIBLE_JS = """() => {
  const panel = document.querySelector('[data-sketch-panel]');
  const svg = panel && panel.querySelector('svg');
  if (!svg) return null;
  let total = 0, visible = 0, inked = 0;
  for (const el of svg.querySelectorAll('path,circle,ellipse,line,polyline,rect')) {
    if (el.closest('.scene-wash')) continue;   // 마스크 안 복제분(task#306 S4) — 아래 주석 참조
    const cs = getComputedStyle(el);
    if (cs.stroke === 'none' || cs.stroke === 'transparent') continue;
    total++;
    if (cs.visibility !== 'visible') continue;
    visible++;
    // **visibility만 보면 유령 선을 센다**(task#308 실측). 교체 페이드(한 그림을 다른 그림으로
    // 갈아끼우는 연출)는 opacity로 하므로, 사라진 쪽 선이 visibility:visible 인 채 DOM에 남아
    // 잉크를 0 기여하면서 계수에는 잡힌다 — GoliathScene은 --at 1000000에서 218선 중 88선이
    // 이 유령이었고(상세 골리앗), 그 상태를 래스터 조건 입력으로 넣으면 모델은 거인을 못 본다.
    let op = 1, n = el;
    while (n && n !== svg.parentNode) {
      const o = parseFloat(getComputedStyle(n).opacity);
      if (!isNaN(o)) op *= o;
      n = n.parentNode;
    }
    const so = parseFloat(cs.strokeOpacity);
    if (!isNaN(so)) op *= so;
    if (op >= 0.02) inked++;
  }
  return { total, visible, inked };
}"""


# 콘티(조건 입력) 전용 — 이름표를 숨긴다. FINDINGS 결함 2: 조건 입력에 글자가 있으면 래스터에
# 그대로 구워진다(task#304 실측). `<Label>`은 SVG <text>이므로 밀도 계수(_FILTER_JS의
# path/circle/... 목록)에는 애초에 안 잡히고, 여기서만 따로 숨긴다.
# 이름표만이 아니라 **svg 밖 패널 내용 전부**를 숨긴다. element.screenshot()은 요소의 바운딩 박스에
# 겹쳐 그려진 것까지 담으므로, svg를 찍어도 그 위에 뜬 확대 버튼 아이콘(tourSketches.jsx의 Maximize2
# 오버레이)이 조건 입력에 구워진다 — 글자가 아니라 아이콘이라 텍스트 단정에는 안 걸린다(실측으로 잡음).
_HIDE_TEXT_JS = """() => {
  const panel = document.querySelector('[data-sketch-panel]');
  const svg = panel && panel.querySelector('svg');
  if (!svg) return null;
  const t = svg.querySelectorAll('text, tspan, foreignObject');
  for (const el of t) { el.style.setProperty('visibility', 'hidden', 'important'); }
  // svg 자신·그 조상·그 자손이 아닌 것은 전부 숨긴다(캡션·설명·확대 버튼).
  for (const el of panel.querySelectorAll('*')) {
    if (el === svg || el.contains(svg) || svg.contains(el)) continue;
    el.style.setProperty('visibility', 'hidden', 'important');
  }
  return t.length;
}"""

# delay(ms) 범위로 stroke를 가른다(task#315 S3 — 영역 마스크 파생). d()가 놓은 --sym-delay는 CSS
# 커스텀 프로퍼티라 자손에 그대로 상속된다(index.css .scene-draw가 var(--sym-delay)로 읽는 바로 그
# 값) — 조상을 손으로 훑지 않고 getComputedStyle 한 번으로 상속값을 그대로 얻는다.
# 필터는 「delay 범위 ∧ 잉크(_VISIBLE_JS와 같은 누적 opacity 기준)」다 — delay만 보면 절정 전
# 유령(opacity 0, task#308 실측)까지 마스크 픽셀로 잡힌다.
_DELAY_FILTER_JS = """([lo, hi]) => {
  const panel = document.querySelector('[data-sketch-panel]');
  const svg = panel && panel.querySelector('svg');
  if (!svg) return null;
  let total = 0, kept = 0;
  for (const el of svg.querySelectorAll('path,circle,ellipse,line,polyline,rect')) {
    if (el.closest('.scene-wash')) continue;   // 마스크 안 복제분 — 위 두 JS와 같은 기준
    el.style.removeProperty('visibility');
    const cs = getComputedStyle(el);
    if (cs.stroke === 'none' || cs.stroke === 'transparent') continue;
    total++;
    const raw = cs.getPropertyValue('--sym-delay').trim();
    const delay = raw ? parseFloat(raw) : NaN;
    let op = 1, n = el;
    while (n && n !== svg.parentNode) {
      const o = parseFloat(getComputedStyle(n).opacity);
      if (!isNaN(o)) op *= o;
      n = n.parentNode;
    }
    const so = parseFloat(cs.strokeOpacity);
    if (!isNaN(so)) op *= so;
    const inRange = !isNaN(delay) && delay >= lo && delay <= hi;
    // !important 필수(task#306 S1과 같은 이유 — .scene-draw 애니메이션이 인라인보다 위다).
    if (inRange && op >= 0.02) { kept++; } else { el.style.setProperty('visibility', 'hidden', 'important'); }
  }
  return { total, kept };
}"""


# 남아 있는 '보이는 글자'를 센다 — 0이 아니면 촬영하지 않는다(사후 주장이 아니라 렌더 시각의 단정).
_TEXT_COUNT_JS = """() => {
  const svg = document.querySelector('[data-sketch-panel] svg');
  if (!svg) return null;
  let shown = 0;
  for (const el of svg.querySelectorAll('text, tspan, foreignObject')) {
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    if ((el.textContent || '').trim() === '') continue;
    shown++;
  }
  return shown;
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


def shoot(pw, scene, out, scale, at_ms, rungs=None, no_labels=False, meta_out=None, delay_range=None):
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
        meta = {"scene": scene, "at_ms": at_ms, "scale": scale, "no_labels": no_labels,
                "shots": []}
        if no_labels:
            # 연출 종료 후인지를 **숫자로** 단정한다(FINDINGS 파생 규칙 ① — 조건 입력은 완성 상태여야
            # 한다). 필터 전에 재야 한다: 필터 뒤에는 보이는 획 = 잔존 선이라 의미가 뒤집힌다.
            pre = page.evaluate(_VISIBLE_JS)
            if not pre:
                sys.exit("패널 svg를 찾지 못했다")
            if pre["visible"] != pre["total"]:
                sys.exit(f"연출이 끝나지 않았다 — 보이는 획 {pre['visible']}/{pre['total']} "
                         f"(--at {at_ms}). 조건 입력은 완성 상태여야 한다")
            meta["post_performance"] = True
            meta["total_strokes"] = pre["total"]
            meta["inked_strokes"] = pre["inked"]
            ghost = pre["total"] - pre["inked"]
            meta["ghost_strokes"] = ghost
            if ghost:
                print(f"  ⚠ 유령 선 {ghost}개 — visibility는 visible인데 opacity가 0이라 "
                      f"잉크를 남기지 않는다(교체 페이드). 이 --at({at_ms})의 실제 잉크는 "
                      f"{pre['inked']}선이다. 조건 입력의 밀도로는 total이 아니라 이 값을 써라.")
            page.evaluate(_HIDE_TEXT_JS)
        el = (page.query_selector("[data-sketch-panel] svg") if no_labels
              else page.query_selector("[data-sketch-panel]"))
        if not el:
            sys.exit("패널이 렌더되지 않았다")

        def assert_no_text():
            """촬영 직전에 센다 — 프리즈를 다시 걸 때 글자가 되살아날 여지를 남기지 않는다."""
            if not no_labels:
                return None
            n = page.evaluate(_TEXT_COUNT_JS)
            if n != 0:
                sys.exit(f"조건 입력에 글자가 {n}개 남았다 — 촬영하지 않는다(FINDINGS 결함 2)")
            return 0

        if delay_range:
            lo, hi = delay_range
            got = page.evaluate(_DELAY_FILTER_JS, [lo, hi])
            if got is None:
                sys.exit("패널 svg를 찾지 못했다 — 선택자가 바뀌었는지 확인하라")
            page.evaluate(_FREEZE_JS, at_ms)   # 안전판 — _FILTER_JS와 같은 이유
            page.wait_for_timeout(120)
            tn = assert_no_text()
            el.screenshot(path=out)
            print(f"저장: {out}  delay [{lo:g},{hi:g}]  선 {got['kept']}/{got['total']}  "
                  f"배율 {scale}x  --at {at_ms}")
            meta["shots"].append({"path": out, "delay_range": [lo, hi],
                                  "kept": got["kept"], "total": got["total"], "text_nodes": tn})
        elif not rungs:
            vis = page.evaluate(_VISIBLE_JS)
            tn = assert_no_text()
            el.screenshot(path=out)
            vis_str = f", 보이는 획 {vis['visible']}/{vis['total']} (잉크 {vis['inked']})" if vis else ""
            print(f"저장: {out}  (배율 {scale}x, --at {at_ms}, 콘솔에러 {len(errs)}건{vis_str})")
            meta["shots"].append({"path": out, "rung": None,
                                  "kept": vis and vis["visible"], "total": vis and vis["total"],
                                  "text_nodes": tn})
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
                vis = page.evaluate(_VISIBLE_JS)
                path = f"{stem}-mw{n:g}{ext}"
                tn = assert_no_text()
                el.screenshot(path=path)
                meta["shots"].append({"path": path, "rung": n, "threshold_dom": round(n * W, 4),
                                      "kept": got["kept"], "total": got["total"],
                                      "text_nodes": tn})
                vis_str = f"  보이는 획 {vis['visible']}/{vis['total']} (잉크 {vis['inked']})" if vis else ""
                print(f"저장: {path}  임계 n>={n:g} (DOM {n * W:.4f}) "
                      f"선 {got['kept']}/{got['total']}  배율 {scale}x  --at {at_ms}{vis_str}")
        if errs:
            print("  ⚠ 콘솔에러:", errs[0][:160])
        if meta_out:
            meta["console_errors"] = errs[:5]
            os.makedirs(os.path.dirname(os.path.abspath(meta_out)), exist_ok=True)
            with open(meta_out, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            print(f"기록: {meta_out}")
    finally:
        b.close()


def shoot_cast(pw, out, scale):
    """설정화 시트(#/cast)를 찍는다 — 정차지 탐색을 건너뛴다(task#307 S1). 정지 화면이라
    _FREEZE_JS/_FILTER_JS/_VISIBLE_JS는 쓰지 않는다 — 시트 전용 선택자 [data-cast-sheet]로
    화면 전체를 찍는다."""
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={"width": 1280, "height": 900}, device_scale_factor=scale)
    page = ctx.new_page()
    errs = []
    page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errs.append(str(e)))
    try:
        page.goto(f"{BASE}/#/cast", wait_until="domcontentloaded")
        page.wait_for_selector("[data-cast-sheet]", timeout=15000)
        page.wait_for_timeout(300)
        el = page.query_selector("[data-cast-sheet]")
        if not el:
            sys.exit("설정화 시트가 렌더되지 않았다")
        el.screenshot(path=out)
        print(f"저장: {out}  (배율 {scale}x, 콘솔에러 {len(errs)}건)")
        if errs:
            print("  ⚠ 콘솔에러:", errs[0][:160])
    finally:
        b.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("scene", nargs="?", choices=sorted(SCENES), help="장면 이름(--cast와 배타)")
    ap.add_argument("--cast", action="store_true",
                    help="투어 정차지 탐색을 건너뛰고 설정화 시트(#/cast)를 찍는다(task#307 S1)")
    ap.add_argument("--out")
    ap.add_argument("--scale", type=int, default=3, help="촬영 배율(기본 3 — 선 겹침이 보인다)")
    ap.add_argument("--no-build", action="store_true", help="빌드·재시작을 생략(직전 빌드 재사용)")
    ap.add_argument("--at", type=int, default=1000000,
                    help="이 시각(ms)에 애니메이션을 고정. 기본은 전부 끝난 상태. "
                         "절정 뒤 상태를 보려면 예: --at 8500 (--cast에는 적용되지 않는다 — 정지 화면)")
    ap.add_argument("--min-stroke-width", dest="rungs",
                    help="굵기 임계(sw()의 n)로 선을 깎아 밀도 계단을 만든다. 쉼표로 여러 개를 주면 "
                         "한 세션에서 계단별로 한 장씩 촬영하고 파일명에 -mw<n>을 붙인다. "
                         "0은 전체(무필터). 예: 2.0,1.8,1.4,1.3,0")
    ap.add_argument("--no-labels", dest="no_labels", action="store_true",
                    help="이름표(SVG <text>)를 숨기고 패널 대신 svg만 촬영한다 — 래스터 조건 입력(콘티)용. "
                         "글자가 남았거나 연출이 안 끝났으면 촬영하지 않고 실패한다.")
    ap.add_argument("--delay-range", dest="delay_range",
                    help="LO,HI(ms) — --sym-delay가 이 범위 ∧ 잉크(opacity>=0.02)인 stroke만 남기고 "
                         "나머지를 숨긴다. 영역 마스크 파생용(task#315 S3). --no-labels와 함께 쓰고 "
                         "--min-stroke-width와는 배타. 예: --delay-range 4920,7560")
    ap.add_argument("--meta-out", dest="meta_out",
                    help="촬영 결과(계단별 잔존 선·텍스트 노드 수·--at)를 JSON으로 남긴다")
    a = ap.parse_args()
    if not a.cast and not a.scene:
        ap.error("scene 또는 --cast 중 하나가 필요하다")
    rungs = None
    if a.rungs:
        rungs = [float(v) for v in a.rungs.split(",") if v.strip() != ""]
    delay_range = None
    if a.delay_range:
        if rungs:
            ap.error("--delay-range와 --min-stroke-width는 함께 쓰지 않는다")
        if not a.no_labels:
            ap.error("--delay-range는 --no-labels와 함께 써야 한다(마스크는 글자를 포함하지 않는다)")
        lo_s, hi_s = a.delay_range.split(",")
        delay_range = (float(lo_s), float(hi_s))
    out = a.out or os.path.join(ROOT, ".forge/scratch", f"render-{'cast' if a.cast else a.scene}.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if not a.no_build:
        build()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        if a.cast:
            shoot_cast(pw, out, a.scale)
        else:
            shoot(pw, a.scene, out, a.scale, a.at, rungs, a.no_labels, a.meta_out, delay_range)
