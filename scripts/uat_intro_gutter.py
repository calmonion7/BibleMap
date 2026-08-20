#!/usr/bin/env python3
"""인트로 텍스트 잉크의 좌우 여백 실측 UAT (task#280 S1).

`backend/scripts/validate_intro_gutter.py`가 **소스 불변식**을 단언하고, 이 스크립트는 그 선언이
**실제로 픽셀이 됐는지**를 잰다. 둘은 서로를 대신하지 못한다 — 전역 `content-box` 함정은 소스에
패딩이 멀쩡히 적힌 채로 시각적 여백을 0으로 만들었다(ADR 260820-232144).

실행법:
    python3 scripts/uat_intro_gutter.py                      # 모바일 4폭 + 데스크톱
    python3 scripts/uat_intro_gutter.py --viewports mobile   # 320/360/375/390
    python3 scripts/uat_intro_gutter.py --viewports desktop  # 1280
    python3 scripts/uat_intro_gutter.py --selftest           # 자(尺)의 대조군
    BASE=http://localhost:8080 python3 scripts/uat_intro_gutter.py

**`scripts/check.sh`에 배선하지 않는다.** `deploy.sh`는 빌드 **전**에 check.sh를 부르므로 그
시점의 :8080은 옛 빌드를 서빙한다 — 게이트에 넣으면 방금 고친 코드가 아니라 이전 배포본을 재서
초록/빨강이 둘 다 거짓이 된다. 소스 불변식(validate_intro_gutter)만 게이트에 있고, 이 실측은
인트로 레이아웃을 만질 때 사람이 부르는 자다. 프론트 빌드 후 nginx 재시작이 선행 조건이다
(`cd frontend && npm run build && docker compose restart nginx` — dist inode 교체로 마운트가 끊긴다).

측정 방법 — **컨테이너가 아니라 텍스트 잉크를 잰다.** 블록 요소의 rect는 `textAlign:center`
아래서 프레임 패딩 경계일 뿐이라 여백을 과소평가한다. 그래서 텍스트 노드마다 `Range`를 만들고
`getClientRects()`로 **줄 단위 실제 필적 사각형**을 얻는다. 줄바꿈된 각 줄이 따로 잡히므로
"어느 한 줄이 화면에 붙었다"를 놓치지 않는다.

진입은 `#/intro` 딥링크로 한다(`urlState.parseHash`의 `/intro`) — 이 자가 재는 것은 여백이지
라우팅이 아니므로 비트 8곳에 가장 짧게 도달하는 경로를 쓴다. (task#281에서 무해시 진입도 다시
인트로에 도달하게 고쳤다. 진입 계약 자체는 `scripts/uat_intro_entry.py`와
`backend/scripts/validate_intro_entry_route.py`가 전담한다.)

여백과 함께 **금색 구분선(.intro-line)의 프레임 대비 좌우 대칭**도 잰다(task#281 S4) — 블록 자식이라
`margin: '18px 0'`이면 좌측에 붙고, 프레임이 flex+center인 비트에서만 우연히 가운데였다. 같은 프레임
안의 시각적 정렬이므로 여백과 한 자에서 본다.

**실패 계층을 자가 구별한다**(회고 260820-190352). 백지 렌더·마운트 끊김·옛 빌드는 "제품이
틀렸다"가 아니라 "자가 죽었다"이고, 구별 없는 체크는 있지도 않은 결함에 fix-forward를 태우거나
사람이 할 수 있는 일이 없는 벽을 만든다. 종료 코드로 갈라 출력한다:
    0 = 통과 · 1 = 여백 결함(제품) · 2 = 측정 환경 이상(자)
"""
import os
import subprocess
import sys
import time

BASE = os.environ.get("BASE", "http://localhost:8080")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BEATS = list(range(8))          # ①오프닝 ②지도 ③몽타주 ④인물 ⑤성경책 ⑥투어 ⑦전역기능 ⑧도착지
MOBILE = [320, 360, 375, 390]
DESKTOP = [1280]
MIN_GUTTER = {"mobile": 20, "desktop": 32}
SETTLE_MS = 900                 # 비트 등장 후 전환(TRANS_MS=700)이 끝나기를 기다린다

# 레이어의 텍스트 잉크 줄 사각형 — 자식 없는 요소가 아니라 텍스트 노드의 Range를 잰다.
_INK_JS = """
(p) => {
  const layer = document.querySelector('[data-intro-layer="' + p + '"]');
  if (!layer) return { missing: true };
  const vw = window.innerWidth, lines = [];
  const w = document.createTreeWalker(layer, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = w.nextNode())) {
    const t = n.textContent.trim();
    if (!t) continue;
    const r = document.createRange();
    r.selectNodeContents(n);
    for (const box of r.getClientRects()) {
      if (box.width < 1 || box.height < 1) continue;
      lines.push({ text: t.slice(0, 22), left: box.left, right: vw - box.right });
    }
  }
  return { vw, lines, scrollW: document.documentElement.scrollWidth,
           clientW: document.documentElement.clientWidth };
}
"""


# 금색 구분선(Hero의 .intro-line)의 프레임 content-box 대비 좌우 여백 — 가운데 정렬 여부.
# 블록 자식이라 `margin: '18px 0'`이면 좌측에 붙고, 부모가 flex+center인 비트에서만 우연히 가운데였다.
# 결함 클래스 = "금선이 어느 비트에서든 프레임 안에서 좌우 비대칭이다"(특정 비트 하드코딩이 아니다).
_LINE_JS = """
(p) => {
  const layer = document.querySelector('[data-intro-layer="' + p + '"]');
  if (!layer) return { missing: true };
  const line = layer.querySelector('.intro-line');
  if (!line) return { absent: true };
  const frame = line.closest('[data-intro-frame]');
  if (!frame) return { noframe: true };
  const f = frame.getBoundingClientRect(), l = line.getBoundingClientRect();
  const cs = getComputedStyle(frame);
  const cl = f.left + parseFloat(cs.paddingLeft), cr = f.right - parseFloat(cs.paddingRight);
  return { left: l.left - cl, right: cr - l.right };
}
"""

LINE_SKEW_MAX = 1.0             # 좌우 여백 차 허용치(px) — 서브픽셀 반올림만 허용


class EnvError(Exception):
    """측정 환경 이상 — 제품 결함이 아니다(종료 코드 2)."""


def _freshness():
    """dist가 소스보다 낡았으면 옛 빌드를 재는 것이다 — 제품이 아니라 자의 문제."""
    dist = os.path.join(ROOT, "frontend/dist/index.html")
    src = os.path.join(ROOT, "frontend/src/IntroView.jsx")
    if not os.path.exists(dist):
        raise EnvError("frontend/dist/index.html이 없다 — `cd frontend && npm run build` 선행 필요")
    if os.path.getmtime(dist) < os.path.getmtime(src):
        raise EnvError("dist가 IntroView.jsx보다 낡았다 — 옛 빌드를 재고 있다. "
                       "`cd frontend && npm run build && docker compose restart nginx` 후 재시도")


def _measure(page, css=None):
    """한 뷰포트에서 비트 0~7을 순회 측정 → {beat: {min_left, min_right, lines, scroll_over}}."""
    try:
        page.goto(BASE + "/#/intro", wait_until="domcontentloaded")
    except Exception as e:
        # 원격 BASE(프로덕션)에서는 내비게이션 자체가 일시적으로 실패한다 — 제품 결함이 아니라
        # 측정 경로의 문제이므로 환경 이상으로 승격해 재시도를 태운다.
        raise EnvError("%s/#/intro 진입 실패: %s" % (BASE, str(e).splitlines()[0]))
    if css:
        page.add_style_tag(content=css)
    out = {}
    for p in BEATS:
        try:
            page.wait_for_selector('[data-intro-layer="%d"]' % p, timeout=15000)
        except Exception:
            raise EnvError("비트 %d 레이어가 15초 안에 나타나지 않았다 (필름이 돌지 않거나 렌더 실패)" % p)
        page.wait_for_timeout(SETTLE_MS)
        r = page.evaluate(_INK_JS, p)
        if r.get("missing") or not r.get("lines"):
            raise EnvError("비트 %d에서 텍스트 잉크를 하나도 못 읽었다 (백지 렌더 — 제품 결함이 아니라 렌더 환경)" % p)
        out[p] = {
            "min_left": min(l["left"] for l in r["lines"]),
            "min_right": min(l["right"] for l in r["lines"]),
            "worst": min(r["lines"], key=lambda l: min(l["left"], l["right"])),
            "n": len(r["lines"]),
            "scroll_over": r["scrollW"] - r["clientW"],
            "line": page.evaluate(_LINE_JS, p),
        }
    return out


def _run(pw, width, css=None):
    b = pw.chromium.launch()
    try:
        ctx = b.new_context(viewport={"width": width, "height": 780},
                           reduced_motion="no-preference")  # reduce면 phase=END로 시작해 필름이 안 돈다
        page = ctx.new_page()
        resp_ok = []
        page.on("response", lambda r: resp_ok.append(r.status) if r.url.rstrip("/") == BASE else None)
        try:
            res = _measure(page, css)
        finally:
            # 컨텍스트가 이미 죽었으면 close도 던진다 — 그 예외가 원인 예외를 덮으면
            # 실패 계층 구별(제품 vs 환경)이 무의미해지므로 삼킨다.
            try:
                ctx.close()
            except Exception:
                pass
        if resp_ok and resp_ok[0] != 200:
            raise EnvError("%s 응답이 %d다 (nginx 마운트 끊김 의심 — docker compose restart nginx)"
                           % (BASE, resp_ok[0]))
        return res
    finally:
        b.close()


def _run_retry(pw, width, css=None):
    """환경 이상은 1회 재시도한다 — 렌더러 일시 장애 선례가 있다(회고 260820-190352)."""
    try:
        return _run(pw, width, css)
    except EnvError as e:
        print("  ⟳ 환경 이상 — 1회 재시도: %s" % e, flush=True)
        return _run(pw, width, css)


def _line_violations(res):
    """금선이 프레임 안에서 좌우 비대칭인 비트 — (비트, 좌, 우, 차)."""
    out = []
    for p, d in sorted(res.items()):
        ln = d.get("line") or {}
        if "left" not in ln:
            continue        # 그 비트엔 금선이 없다(비트 1~6) — 측정 대상 아님
        skew = abs(ln["left"] - ln["right"])
        if skew > LINE_SKEW_MAX:
            out.append((p, ln["left"], ln["right"], skew))
    return out


def _violations(res, floor):
    return [(p, d) for p, d in sorted(res.items())
            if min(d["min_left"], d["min_right"]) < floor or d["scroll_over"] > 0]


def _check(pw, kind):
    floor = MIN_GUTTER[kind]
    bad = []
    for w in (MOBILE if kind == "mobile" else DESKTOP):
        res = _run_retry(pw, w)
        v = _violations(res, floor)
        worst_p, worst = min(res.items(), key=lambda kv: min(kv[1]["min_left"], kv[1]["min_right"]))
        print("  %s %4dpx — 최소 여백 %.1fpx (비트 %d «%s») · 가로 overflow %dpx · 잉크 줄 %d"
              % ("✗" if v else "✓", w, min(worst["min_left"], worst["min_right"]), worst_p,
                 worst["worst"]["text"], max(d["scroll_over"] for d in res.values()),
                 sum(d["n"] for d in res.values())), flush=True)
        for p, d in v:   # 실패는 머리부터 전부 본다 — tail로 자르지 않는다(회고 260820-190352)
            bad.append("%dpx 비트 %d — 좌 %.1fpx · 우 %.1fpx (하한 %dpx) · overflow %dpx · «%s»"
                       % (w, p, d["min_left"], d["min_right"], floor, d["scroll_over"], d["worst"]["text"]))
        lv = _line_violations(res)
        measured = [p for p, d in sorted(res.items()) if "left" in (d.get("line") or {})]
        print("  %s %4dpx — 금선 좌우 여백 차: %s (허용 %.0fpx, 비트 %s)"
              % ("✗" if lv else "✓", w,
                 " · ".join("비트 %d %.1fpx" % (p, s) for p, _, _, s in _line_violations(res)) or
                 "전부 %.1fpx 이내" % LINE_SKEW_MAX,
                 LINE_SKEW_MAX, "·".join(str(p) for p in measured) or "없음"), flush=True)
        if not measured:
            raise EnvError("금선(.intro-line)을 어느 비트에서도 못 찾았다 — 측정 훅이 사라졌다")
        for p, l, r, skew in lv:
            bad.append("%dpx 비트 %d 금선 — 프레임 대비 좌 %.1fpx · 우 %.1fpx (차 %.1fpx > 허용 %.0fpx)"
                       % (w, p, l, r, skew, LINE_SKEW_MAX))
    return bad


def _selftest(pw):
    """자의 대조군 — 여백을 고의로 무너뜨렸을 때 검출기가 발화하는지. 발화하지 않으면 이 UAT는 아무것도 재지 않는다."""
    w, floor = 375, MIN_GUTTER["mobile"]
    base = _run_retry(pw, w)
    assert not _violations(base, floor), "기준선이 이미 FAIL이라 대조군을 돌릴 수 없다"
    print("  기준선 %dpx 통과 — 최소 여백 %.1fpx"
          % (w, min(min(d["min_left"], d["min_right"]) for d in base.values())))
    for label, css in [
        ("프레임 좌우 패딩 제거", "[data-intro-frame]{padding-left:0!important;padding-right:0!important}"),
        ("프레임 content-box 회귀", "[data-intro-frame]{box-sizing:content-box!important}"),
    ]:
        v = _violations(_run_retry(pw, w, css), floor)
        assert v, "주입 «%s»에도 검출기가 발화하지 않았다 — 이 UAT는 여백을 재고 있지 않다" % label
        print("  ✓ 주입 «%s» → 비트 %d곳에서 발화 (최악 %s)"
              % (label, len(v), min(("좌%.1f/우%.1f" % (d["min_left"], d["min_right"]) for _, d in v))))
    # 금선 검출기의 대조군 — 가운데 정렬을 고의로 무너뜨린다.
    lv = _line_violations(_run_retry(pw, w, ".intro-line{margin-left:0!important;margin-right:auto!important}"))
    assert lv, "주입 «금선 좌측 정렬»에도 검출기가 발화하지 않았다 — 이 UAT는 금선 정렬을 재고 있지 않다"
    print("  ✓ 주입 «금선 좌측 정렬» → 비트 %d곳에서 발화 (최악 차 %.1fpx)"
          % (len(lv), max(s for _, _, _, s in lv)))
    print("대조군: 주입 3종 모두 발화 확인 (여백 2종 비트 8곳 순회 + 금선 정렬 1종)")


def main():
    kinds = ["mobile", "desktop"]
    if "--viewports" in sys.argv:
        a = sys.argv[sys.argv.index("--viewports") + 1]
        kinds = ["mobile", "desktop"] if a == "all" else [a]
    _freshness()
    from playwright.sync_api import sync_playwright
    t0 = time.time()
    with sync_playwright() as pw:
        if "--selftest" in sys.argv:
            _selftest(pw)
            print("PASS (%.0fs)" % (time.time() - t0))
            return
        bad = []
        for k in kinds:
            print("=== %s (하한 %dpx) ===" % (k, MIN_GUTTER[k]), flush=True)
            bad += _check(pw, k)
    if bad:
        print("\n=== FAIL — 인트로 여백·정렬 불변식 위반 (%d건) ===" % len(bad))
        for b in bad:
            print("  " + b)
        sys.exit(1)
    print("PASS (%.0fs) — 비트 8곳 × %s 전부 여백 하한 통과"
          % (time.time() - t0, "·".join(kinds)))


if __name__ == "__main__":
    try:
        main()
    except EnvError as e:
        print("\n=== 측정 환경 이상 (제품 결함 아님) ===\n  %s" % e)
        sys.exit(2)
