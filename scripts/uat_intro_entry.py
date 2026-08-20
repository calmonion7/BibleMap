#!/usr/bin/env python3
"""무해시 첫 진입이 인트로 관문에 도달하는지 실측 UAT (task#281 S1).

`backend/scripts/validate_intro_entry_route.py`가 **소스 불변식**("무타깃 판정이 한 곳에서만
선언되고 두 소비처가 그것을 쓴다")을 단언하고, 이 스크립트는 그 선언이 **실제 브라우저에서
화면이 됐는지**를 잰다. 둘은 서로를 대신하지 못한다(ADR 260821-000937) — 이 결함은 초기값이
`'intro'`로 **옳게 계산된 다음** 프레임에서 복원 effect가 덮는 형태였으므로, 초기값 계산만 읽는
정적 검사는 초록이면서 화면은 허브일 수 있었다.

실행법:
    python3 scripts/uat_intro_entry.py             # 무타깃 3형태 + 대조군 2종
    python3 scripts/uat_intro_entry.py --selftest   # 자(尺)의 대조군
    BASE=http://localhost:8080 python3 scripts/uat_intro_entry.py

**`scripts/check.sh`에 배선하지 않는다.** `deploy.sh`는 빌드 **전**에 check.sh를 부르므로 그 시점의
:8080은 옛 빌드를 서빙한다 — 게이트에 넣으면 방금 고친 코드가 아니라 이전 배포본을 재서 초록·빨강이
둘 다 거짓이 된다(`uat_intro_gutter.py`가 확립한 이유). 게이트에는 브라우저 없이 항상 도는 소스
불변식(validate_intro_entry_route)만 둔다. 프론트 빌드 후 nginx 재시작이 선행 조건이다
(`cd frontend && npm run build && docker compose restart nginx` — dist inode 교체로 마운트가 끊긴다).

측정 방법 — **URL마다 새 컨텍스트**로 진입한다. SPA에서 같은 문서의 해시만 바꾸면 스테이지가
리마운트되지 않아(`useStageNavigation`의 복원은 마운트 1회) 이 결함이 재현되지 않는다. 그래서
케이스마다 컨텍스트를 새로 만든다. 판정은 두 축을 함께 본다:
  ① `[data-intro-layer="0"]` 존재 — 인트로 필름이 **오프닝 비트부터** 실제로 렌더됐다.
  ② 수렴한 `location.hash` — 상태 머신이 그 스테이지로 갔다(ADR-0009의 encodeHash 계약:
     인트로 `#/intro` · 허브 `#/` · 개요 `#/books`).
해시만 보면 렌더가 죽어도 초록일 수 있고, 레이어만 보면 주소 replace 누락을 놓친다.

**실패 계층을 자가 구별한다**(회고 260820-190352·260821-001058, 누적 4건이 값을 냈다). 종료 코드:
    0 = 통과 · 1 = 라우팅 결함(제품) · 2 = 측정 환경 이상(자)
헤더(`<header>`, 전 스테이지 상시 렌더)가 떴는데 스테이지가 틀린 것은 **제품 결함(1)**이고,
헤더 자체가 안 뜨거나 dist가 낡았거나 응답이 200이 아닌 것은 **환경 이상(2)**이다. 구별 없는
체크는 백지 렌더를 "라우팅 결함"으로 위장해 있지도 않은 결함에 fix-forward를 태운다.
"""
import glob
import os
import sys
import time

BASE = os.environ.get("BASE", "http://localhost:8080")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERDICT_TIMEOUT_MS = 8000       # 복원 effect → sync effect의 replaceState까지 수렴 대기
POLL_MS = 120
INTRO_KEY = "biblemap-intro"

# 케이스 = (라벨, 진입 경로, localStorage 주입, 기대 스테이지)
# 무타깃 3형태를 모두 돈다 — `/`는 hash `''`, `/#`도 브라우저가 `''`로 주고, `/#/`만 `'#/'`다.
# 세 입력이 코드의 서로 다른 분기를 타므로 하나로 줄이면 나머지 두 형태의 회귀를 놓친다.
CASES = [
    ("무타깃 `/`",            "/",       None,  "intro"),
    ("무타깃 `/#`",           "/#",      None,  "intro"),
    ("무타깃 `/#/`",          "/#/",     None,  "intro"),
    ("대조군 인트로 끄기",     "/",       "off", "hub"),
    ("대조군 딥링크 `#/books`", "/#/books", None,  "overview"),
]

# 스테이지 → (기대 해시, 인트로 레이어 존재 여부). 해시는 encodeHash의 계약(urlState.js).
EXPECT = {
    "intro":    ("#/intro", True),
    "hub":      ("#/",      False),
    "overview": ("#/books", False),
}

_VERDICT_JS = """
() => ({
  hash: location.hash,
  intro0: !!document.querySelector('[data-intro-layer="0"]'),
  anyLayer: !!document.querySelector('[data-intro-layer]'),
  header: !!document.querySelector('header'),
})
"""


class EnvError(Exception):
    """측정 환경 이상 — 제품 결함이 아니다(종료 코드 2)."""


def _freshness():
    """dist가 소스보다 낡았으면 옛 빌드를 재는 것이다 — 제품이 아니라 자의 문제."""
    dist = os.path.join(ROOT, "frontend/dist/index.html")
    if not os.path.exists(dist):
        raise EnvError("frontend/dist/index.html이 없다 — `cd frontend && npm run build` 선행 필요")
    srcs = glob.glob(os.path.join(ROOT, "frontend/src/**/*.js*"), recursive=True)
    if not srcs:
        raise EnvError("frontend/src에서 소스를 못 찾았다 — 저장소 루트 해석 실패")
    newest = max(srcs, key=os.path.getmtime)
    if os.path.getmtime(dist) < os.path.getmtime(newest):
        raise EnvError("dist가 %s보다 낡았다 — 옛 빌드를 재고 있다. "
                       "`cd frontend && npm run build && docker compose restart nginx` 후 재시도"
                       % os.path.relpath(newest, ROOT))


def _observe(pw, path, intro_flag):
    """새 컨텍스트로 진입해 스테이지 판정이 수렴할 때까지 관측 → 마지막 판정 dict."""
    b = pw.chromium.launch()
    try:
        ctx = b.new_context(viewport={"width": 1280, "height": 780},
                            reduced_motion="no-preference")  # reduce면 phase=END로 시작해 오프닝 비트가 없다
        if intro_flag is not None:
            # 앱 부팅 **전에** 심는다 — 마운트 시점 초기값 계산이 이 값을 읽는다.
            ctx.add_init_script("localStorage.setItem('%s', '%s')" % (INTRO_KEY, intro_flag))
        page = ctx.new_page()
        statuses = []
        page.on("response", lambda r: statuses.append(r.status) if r.url.rstrip("/") == BASE else None)
        try:
            try:
                page.goto(BASE + path, wait_until="domcontentloaded")
            except Exception as e:
                raise EnvError("%s%s 진입 실패: %s" % (BASE, path, str(e).splitlines()[0]))
            if statuses and statuses[0] != 200:
                raise EnvError("%s 응답이 %d다 (nginx 마운트 끊김 의심 — docker compose restart nginx)"
                               % (BASE, statuses[0]))
            try:
                page.wait_for_selector("header", timeout=15000)
            except Exception:
                raise EnvError("전역 헤더가 15초 안에 나타나지 않았다 — 앱이 뜨지 않았다(백지 렌더). "
                               "라우팅 결함이 아니라 측정 환경 이상")
            # 판정 수렴 대기 — 복원 effect가 setRestored → sync effect가 replaceState를 찍는다.
            deadline = time.time() + VERDICT_TIMEOUT_MS / 1000.0
            v = page.evaluate(_VERDICT_JS)
            while time.time() < deadline:
                if _settled(v):
                    break
                page.wait_for_timeout(POLL_MS)
                v = page.evaluate(_VERDICT_JS)
            return v
        finally:
            # 컨텍스트가 이미 죽었으면 close도 던진다 — 그 예외가 원인 예외를 덮으면
            # 실패 계층 구별(제품 vs 환경)이 무의미해진다.
            try:
                ctx.close()
            except Exception:
                pass
    finally:
        b.close()


def _settled(v):
    """어떤 기대값과도 맞으면 수렴한 것으로 본다 — 틀린 스테이지에서 타임아웃을 다 태우지 않게."""
    return any(v["hash"] == h and v["intro0"] == i for h, i in EXPECT.values())


def _observe_retry(pw, path, intro_flag):
    """환경 이상은 1회 재시도한다 — 렌더러 일시 장애 선례가 있다(회고 260820-190352)."""
    try:
        return _observe(pw, path, intro_flag)
    except EnvError as e:
        print("  ⟳ 환경 이상 — 1회 재시도: %s" % e, flush=True)
        return _observe(pw, path, intro_flag)


def _mismatch(v, want_stage):
    """기대 스테이지와 어긋난 점 — 없으면 빈 문자열."""
    want_hash, want_intro = EXPECT[want_stage]
    bad = []
    if v["hash"] != want_hash:
        bad.append("해시 %r (기대 %r)" % (v["hash"], want_hash))
    if v["intro0"] != want_intro:
        bad.append("오프닝 비트 %s (기대 %s)"
                   % ("있음" if v["intro0"] else "없음", "있음" if want_intro else "없음"))
    return " · ".join(bad)


def _check(pw):
    bad = []
    for label, path, flag, want in CASES:
        v = _observe_retry(pw, path, flag)
        m = _mismatch(v, want)
        print("  %s %-22s → %s (해시 %r · 오프닝 비트 %s)"
              % ("✗" if m else "✓", label, want, v["hash"], "있음" if v["intro0"] else "없음"), flush=True)
        if m:
            bad.append("%s (%s) — %s로 가야 하는데 %s" % (label, path, want, m))
    return bad


def _selftest(pw):
    """자의 대조군 — 기대 입력을 뒤집었을 때 검출기가 발화하는지. 발화하지 않으면 이 UAT는
    아무것도 재고 있지 않다. 주입 대상은 케이스 전체를 순회한다(회고 260820-003946·260821-001058)."""
    base_bad = _check(pw)
    assert not base_bad, "기준선이 이미 FAIL이라 대조군을 돌릴 수 없다:\n  " + "\n  ".join(base_bad)
    n = 0
    # ① 무타깃 3형태에 인트로 끄기를 주입 — 인트로 기대가 깨져야 한다.
    for label, path, _, want in CASES:
        if want != "intro":
            continue
        v = _observe_retry(pw, path, "off")
        assert _mismatch(v, "intro"), "«%s»에 %s='off'를 주입했는데 인트로 기대가 그대로 통과했다" % (label, INTRO_KEY)
        print("  ✓ 주입 «%s + 인트로 끄기» → 발화 (%s)" % (label, _mismatch(v, "intro")))
        n += 1
    # ② 끄기 대조군에서 그 플래그를 뗀다 — 허브 기대가 깨져야 한다(인트로가 나타나므로).
    v = _observe_retry(pw, "/", None)
    assert _mismatch(v, "hub"), "인트로 끄기 플래그를 뗐는데 허브 기대가 그대로 통과했다"
    print("  ✓ 주입 «끄기 플래그 제거» → 발화 (%s)" % _mismatch(v, "hub"))
    n += 1
    # ③ 딥링크 대조군을 무타깃으로 바꾼다 — 개요 기대가 깨져야 한다.
    v = _observe_retry(pw, "/", None)
    assert _mismatch(v, "overview"), "딥링크를 무타깃으로 바꿨는데 개요 기대가 그대로 통과했다"
    print("  ✓ 주입 «딥링크 → 무타깃» → 발화 (%s)" % _mismatch(v, "overview"))
    n += 1
    print("대조군: 주입 %d종 전부 발화 확인 (무타깃 3형태 + 대조군 2종 순회)" % n)


def main():
    _freshness()
    from playwright.sync_api import sync_playwright
    t0 = time.time()
    with sync_playwright() as pw:
        if "--selftest" in sys.argv:
            print("=== 자의 대조군 ===", flush=True)
            _selftest(pw)
            print("PASS (%.0fs)" % (time.time() - t0))
            return
        print("=== 진입 계약 (무타깃 3형태 + 대조군 2종) ===", flush=True)
        bad = _check(pw)
    if bad:
        print("\n=== FAIL — 진입이 계약대로 라우팅되지 않는다 (%d건) ===" % len(bad))
        for b in bad:   # 실패는 머리부터 전부 본다 — tail로 자르지 않는다(회고 260820-190352)
            print("  " + b)
        sys.exit(1)
    print("PASS (%.0fs) — 무타깃 3형태 인트로 도달 · 끄기/딥링크 대조군 유지" % (time.time() - t0))


if __name__ == "__main__":
    try:
        main()
    except EnvError as e:
        print("\n=== 측정 환경 이상 (제품 결함 아님) ===\n  %s" % e)
        sys.exit(2)
