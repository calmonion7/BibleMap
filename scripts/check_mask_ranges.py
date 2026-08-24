#!/usr/bin/env python3
"""GoliathScene에서 다윗·골리앗 영역 마스크용 delay 범위를 소스에서 파생하고, 두 범위가
연속(끊김 없음)하며 겹치지 않는지 단정한다(task#315 S3, ADR 260823-221839 따름 정리 3).

`.forge/reports/canon-pilot/make_masks.py`가 derive_ranges()를 그대로 가져다 쓴다 — 범위를
두 곳에 손으로 옮겨 적으면 드리프트한다(ADR 260820-003946과 같은 이유, render_scene.py의
stroke_scale()과 같은 파생 방식).

두 충돌의 처분(자세한 근거는 .forge/reports/canon-pilot/MASKS.md):
  (가) 쓰러진 골리앗(delay 30~1110)은 --at 9000에서 opacity 0인 유령(교체 페이드 전)이라
       render_scene.py의 delay-range 필터가 잉크 기준으로 자동 제외한다 — 이 검사는 소스의
       delay 리터럴 "존재"만 보므로 무관하다(잉크 여부는 런타임 값이라 정적 검사가 못 잰다).
  (나) 물맷돌 충격 표시(delay 7680)·흙먼지(7800·7920)는 다윗 구획 뒤쪽에 있지만 다윗의 몸이
       아니다(충격 표시는 골리앗 이마 위, 흙먼지는 두 인물 사이 허공). 어느 인물 범위에도
       넣지 않는다 — `excluded` 구획으로 갈라 두 인물 범위 밖에 둔다(배경 여집합으로 자동 처리).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENE_FILE = os.path.join(ROOT, "frontend/src/sketches/davidUnitedKingdom.jsx")

_D_CALL = re.compile(r'\bd\((\d+)')
_COMPONENT_CALL = re.compile(r'<(David|Goliath)\b[^>]*?delay=\{(\d+)\}', re.S)

# 구획 경계 앵커 — 주 세션이 실측표를 만든 것과 같은 방법(정규식으로 delay를 뽑고 구획 주석으로
# 가른다). 장면 소스가 이 문구를 바꾸면 이 검사도 함께 갱신해야 한다 — 장면 특정 게이트라 결합은
# 의도된 것이다(check_cast_axes.py가 cast/*.jsx의 AXES 리터럴에 결합된 것과 같은 수준).
_ANCHOR_GOLIATH_START = '골리앗 — 다리·팔에 겉·안 두 선으로'
_ANCHOR_FALLEN_START = '쓰러진 자세 — 위 회전 그룹과 달리'
_ANCHOR_DAVID_START = '다윗 — 다리(겉·안 두 선)'
_ANCHOR_EXCLUDED_START = '물맷돌이 이마에 박히다'


def _cast_steps(name):
    """인물 정본 컴포넌트가 delay 하나로 내부적으로 소비하는 STEPS·STEP_GAP을 cast/*.jsx에서
    파생한다(복사 금지 — 위 docstring 참조)."""
    path = os.path.join(ROOT, "frontend/src/sketches/cast", f"{name.lower()}.jsx")
    src = open(path, encoding="utf-8").read()
    steps = int(re.search(r'STEPS\s*=\s*(\d+)', src).group(1))
    gap = int(re.search(r'STEP_GAP\s*=\s*(\d+)', src).group(1))
    return steps, gap


def extract_delays(segment):
    """구획 안의 모든 delay '슬롯'을 파생한다 — d(N) 리터럴 + 인물 정본 호출
    (<David|Goliath delay={N}/>)이 내부적으로 소비하는 STEPS개 슬롯까지 전개한다."""
    vals = set()
    for m in _D_CALL.finditer(segment):
        vals.add(int(m.group(1)))
    for m in _COMPONENT_CALL.finditer(segment):
        name, n = m.group(1), int(m.group(2))
        steps, gap = _cast_steps(name)
        for i in range(steps):
            vals.add(n + i * gap)
    return sorted(vals)


def slice_scene(src):
    """GoliathScene 함수 본문을 구획별로 가른다."""
    start = src.index('function GoliathScene')
    end = src.index('\nfunction ', start + len('function GoliathScene'))
    body = src[start:end]
    g0 = body.index(_ANCHOR_GOLIATH_START)
    f0 = body.index(_ANCHOR_FALLEN_START)
    d0 = body.index(_ANCHOR_DAVID_START)
    e0 = body.index(_ANCHOR_EXCLUDED_START)
    return {
        "background": body[:g0],
        "goliath": body[g0:f0],
        "fallen_ghost": body[f0:d0],
        "david": body[d0:e0],
        "excluded": body[e0:],
    }


def assert_contiguous(delays, step, label):
    for i in range(1, len(delays)):
        gap = delays[i] - delays[i - 1]
        if gap != step:
            raise AssertionError(
                f"{label}: delay 불연속 {delays[i - 1]}→{delays[i]} (간격 {gap}, 기대 {step})")


def derive_ranges(src=None):
    """마스크 생성용 (LO,HI) 두 쌍을 소스에서 파생하고, 연속성·비중첩·제외 구획 격리를 단정한다.
    반환: {"goliath": (lo,hi), "david": (lo,hi)}"""
    if src is None:
        src = open(SCENE_FILE, encoding="utf-8").read()
    sec = slice_scene(src)
    goliath = extract_delays(sec["goliath"])
    david = extract_delays(sec["david"])
    excluded = extract_delays(sec["excluded"])
    if not goliath or not david:
        raise AssertionError("골리앗 또는 다윗 구획에서 delay를 하나도 못 찾았다 — 앵커가 어긋났다")
    assert_contiguous(goliath, 120, "골리앗")
    assert_contiguous(david, 120, "다윗")
    if max(goliath) >= min(david):
        raise AssertionError(f"두 인물 delay 범위가 겹친다: 골리앗 ≤{max(goliath)}, 다윗 ≥{min(david)}")
    if set(excluded) & set(goliath) or set(excluded) & set(david):
        raise AssertionError("제외 구획(충격 표시·흙먼지)의 delay가 인물 범위에 섞여 들어갔다")
    return {"goliath": (min(goliath), max(goliath)), "david": (min(david), max(david))}


# ── selftest 재료 — 실제 장면과 같은 구조를 가진 최소 합성 소스. 앵커 4개만 있으면 되므로
# strokes는 더미다. david2의 값을 바꿔 "고의로 범위를 섞는다"(골리앗 구획과 겹치게 만든다). ──
def _fake_src(david2):
    return f"""
function GoliathScene({{ reduce }}) {{
  return (
    <g>
      <g style={{d(0, reduce)}}><path d="M0 0" /></g>
      {{/* 골리앗 — 다리·팔에 겉·안 두 선으로 부피를 준다 */}}
      <g style={{d(120, reduce)}}><path d="M0 0" /></g>
      <g style={{d(240, reduce)}}><path d="M0 0" /></g>
      {{/* 쓰러진 자세 — 위 회전 그룹과 달리 처음부터 */}}
      <g style={{d(30, reduce)}}><path d="M0 0" /></g>
      {{/* 다윗 — 다리(겉·안 두 선) */}}
      <g style={{d(360, reduce)}}><path d="M0 0" /></g>
      <g style={{d({david2}, reduce)}}><path d="M0 0" /></g>
      {{/* 물맷돌이 이마에 박히다(삼상 17:49) */}}
      <g style={{d(600, reduce)}}><path d="M0 0" /></g>
    </g>
  )
}}
function NextScene() {{ return <g/> }}
"""


def _selftest():
    good = derive_ranges(_fake_src(480))
    assert good == {"goliath": (120, 240), "david": (360, 480)}, f"정상 소스 파싱이 어긋났다: {good}"
    print(f"selftest: 정상 소스 PASS {good}")

    # 고의 위반 1 — 겹침: 다윗 구획의 두 번째 delay를 골리앗 구획과 같은 값으로 섞는다.
    try:
        derive_ranges(_fake_src(240))
    except AssertionError as e:
        print(f"selftest: 겹침 주입이 정확히 실패했다 — {e}")
    else:
        raise SystemExit("selftest 실패 — 겹침을 주입했는데 통과했다")

    # 고의 위반 2 — 불연속: 다윗 구획에 120 간격이 아닌 값을 섞는다(730은 360과 370 떨어져 있다).
    try:
        derive_ranges(_fake_src(730))
    except AssertionError as e:
        print(f"selftest: 불연속 주입이 정확히 실패했다 — {e}")
    else:
        raise SystemExit("selftest 실패 — 불연속을 주입했는데 통과했다")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        ranges = derive_ranges()
        for name, (lo, hi) in ranges.items():
            print(f"{name}: delay [{lo}, {hi}] — 연속 확인 PASS")
        print("PASS — 두 인물 delay 범위 연속 + 비중첩 + 제외 구획 격리")
