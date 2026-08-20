"""무타깃(해시 없는) 진입 판정의 단일 선언 불변식 검증 (task#281 S1).

task#280 주행에서 발견된 결함: `useStageNavigation.js`의 `activeStage` 초기값은 무해시 진입에서
조건대로 `'intro'`로 **옳게 계산되는데**, 직후 딥링크 복원 effect가 `parseHash('')`의 결과
`{stage:'hub'}`를 `applyParsedHash`에 넘겨 그 초기값을 덮었다. 즉 "이 진입은 무타깃인가"라는
**하나의 질문에 코드가 두 곳에서 서로 다르게 답하고 있었다** — 초기값 계산은 "무타깃이다"라고
보고 인트로를 골랐고, 복원 effect는 그 개념을 아예 갖지 않은 채 모든 해시를 딥링크로 취급했다.

그래서 이 검증기가 단언하는 결함 클래스는 **"무타깃 진입의 뜻이 두 곳에서 갈린다"**이고,
알려진 위반 목록(그때 그 두 줄)이 아니다(ADR 260821-000937). 불변식 4종:

  (a) 무타깃을 판정하는 지점이 **정본 밖에는 0곳**이다. 판정 지점 = 원시 해시
      (`window.location.hash`) 형태인 `'#'`·`'#/'` 리터럴과의 동등 비교. 정본 밖에 하나라도
      생기는 순간 한쪽만 고치는 결함이 다시 열린다. (술어 본문 안의 비교 **개수**는 세지
      않는다 — `'#'`와 `'#/'`를 함께 보는 것이 정상이다. 세면 옳은 구현이 빨강이 된다.)
      함께 단언: 그 술어가 **공허하지 않다**(무타깃 형태를 실제로 비교한다).
  (b) 정본은 `urlState.js`의 **export된 `isNoTarget`**이다 — 해시 계약의 정본이 사는 파일이고,
      export여야 소비처가 복사하지 않고 쓴다.
  (c) 초기값 계산(`biblemap-intro`를 읽는 `useState` 초기화자)이 `isNoTarget`을 쓴다.
  (d) 마운트 복원 effect(`restoredRef.current`를 쓰는 그 effect)가 `isNoTarget`을 **`applyParsedHash`
      호출보다 먼저** 참조한다. 그 effect의 계약은 딥링크 복원이고, 해시 없는 진입은 딥링크가
      아니므로 걸러내고 나가야 한다. "먼저"까지 단언하는 이유: 뒤에서 참조하면 이미 덮은 뒤다.

`parseHash`의 계약(`''`/`'/'` → `{stage:'hub'}`)은 **건드리지 않는다** — `#/`는 정상적인 허브 URL이고
`handleGoToHash`(저장·이어보기 카드 복원)와 공용이다. 그래서 (a)의 탐지 대상은 `'#'`·`'#/'`
리터럴이며, `parseHash`가 `^#`를 떼고 비교하는 `''`·`'/'`는 세지 않는다.

앱을 실행하지 않고 소스에서 정적으로 판정한다(import 부작용 0·실행 0). 실측은 이 검증기가 아니라
`scripts/uat_intro_entry.py`가 한다 — 이 결함은 초기값이 옳게 계산된 **다음** 프레임에서 덮이는
형태였으므로, 정적 검사만으로는 초록이면서 화면은 허브일 수 있었다. 둘은 서로를 대신하지 못한다.

--selftest는 인메모리 사본에 고의 결함을 주입해 이 검사가 실제로 FAIL하는지 확인한다. 기준선
PASS만으로는 게이트가 살아있음을 증명하지 못하고, 주입 대상을 하나로 고정하면 검사가 그 항목에
우연히 묶였는지 가릴 수 없다(회고 260820-003946·260821-001058) — 그래서 불변식 4종을 모두 순회한다.
"""
import glob
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SRC_DIR = "frontend/src"
_URLSTATE = "frontend/src/urlState.js"
_NAV = "frontend/src/useStageNavigation.js"
_PREDICATE = "isNoTarget"

# 판정 지점의 정의 — 원시 해시 형태 리터럴('#' 또는 '#/')과의 동등 비교.
# eco: 정규식 판정. 주석·문자열 안의 우연한 일치는 아래 _strip으로 걷어낸다.
_SITE = re.compile(r"[!=]==?\s*(['\"])#/?\1")


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as f:
        return f.read()


def _strip(src):
    """주석을 공백으로 치환 — 주석 안의 예시 코드가 판정 지점으로 오인되지 않게.
    길이를 보존해 오프셋 비교(불변식 d)가 원본과 일치한다."""
    def blank(m):
        return re.sub(r"\S", " ", m.group(0))
    return re.sub(r"//[^\n]*|/\*.*?\*/", blank, src, flags=re.S)


def _span(src, open_at):
    """open_at의 '{'부터 짝이 맞는 '}'까지 — 중첩 객체·템플릿 `${}`를 함께 통과한다."""
    depth, j = 0, open_at
    while j < len(src):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                return open_at + 1, j
        j += 1
    raise AssertionError("중괄호가 닫히지 않았다(offset %d)" % open_at)


def _sources():
    """frontend/src 전체의 (상대경로, 주석 제거된 소스)."""
    out = []
    for p in sorted(glob.glob(os.path.join(_ROOT, _SRC_DIR, "**", "*.js*"), recursive=True)):
        out.append((os.path.relpath(p, _ROOT), _strip(_read(os.path.relpath(p, _ROOT)))))
    assert out, "%s에서 소스를 하나도 못 찾았다" % _SRC_DIR
    return out


def _sites(sources):
    """무타깃 판정 지점 전부 — (상대경로, 오프셋, "파일:행", 매치 텍스트)."""
    out = []
    for rel, src in sources:
        for m in _SITE.finditer(src):
            out.append((rel, m.start(), "%s:%d" % (rel, src.count("\n", 0, m.start()) + 1), m.group(0)))
    return out


def _fn_body(src, name):
    """function name(…) { … } 의 본문. 없으면 None."""
    m = re.search(r"function\s+%s\s*\(" % name, src)
    if not m:
        return None
    return _span(src, src.index("{", src.index(")", m.end() - 1)))


def _initializer(src):
    """`biblemap-intro`를 읽는 useState 초기화자의 본문 — 초기값 계산 지점."""
    for m in re.finditer(r"useState\(\(\)\s*=>\s*\{", src):
        a, b = _span(src, m.end() - 1)
        if "biblemap-intro" in src[a:b]:
            return src[a:b]
    return None


def _restore_effect(src):
    """`restoredRef.current`를 쓰는 useEffect의 본문 — 마운트 딥링크 복원 effect."""
    for m in re.finditer(r"useEffect\(\(\)\s*=>\s*\{", src):
        a, b = _span(src, m.end() - 1)
        body = src[a:b]
        if "restoredRef.current" in body:
            return body
    return None


def _errors(sources):
    errs = []
    by_rel = dict(sources)
    sites = _sites(sources)

    us = by_rel.get(_URLSTATE)
    assert us is not None, "%s를 못 읽었다" % _URLSTATE
    span = _fn_body(us, _PREDICATE)

    # (b) 정본 술어가 존재하고 export된다
    if span is None:
        errs.append("%s에 %s 선언이 없다 — 무타깃 판정의 정본이 없다" % (_URLSTATE, _PREDICATE))
    elif not re.search(r"export\s+function\s+%s\s*\(" % _PREDICATE, us):
        errs.append("%s의 %s가 export되지 않았다 — 소비처가 복사하게 된다" % (_URLSTATE, _PREDICATE))

    # (a) 정본 밖에서 무타깃을 판정하는 지점이 0곳이다 — 결함 클래스 그 자체.
    #     술어 본문 안에 비교가 몇 개인지는 무관하다('#'와 '#/' 둘을 함께 보는 게 정상이다).
    outside = [t for rel, off, t, _ in sites
               if not (span and rel == _URLSTATE and span[0] <= off < span[1])]
    if outside:
        errs.append("정본(%s의 %s) 밖에서 무타깃을 판정하는 지점이 %d곳이다 — 뜻이 갈린다: %s"
                    % (_URLSTATE, _PREDICATE, len(outside), " · ".join(outside)))

    # (a') 정본이 공허하지 않다 — 무타깃 형태를 실제로 비교한다
    if span and not any(rel == _URLSTATE and span[0] <= off < span[1] for rel, off, _, _ in sites):
        errs.append("%s의 %s가 무타깃 형태('#'·'#/')를 실제로 비교하지 않는다 — 공허한 술어다"
                    % (_URLSTATE, _PREDICATE))

    nav = by_rel.get(_NAV)
    assert nav is not None, "%s를 못 읽었다" % _NAV

    # (c) 초기값 계산이 그 술어를 쓴다
    init = _initializer(nav)
    if init is None:
        errs.append("%s에서 biblemap-intro를 읽는 useState 초기화자를 못 찾았다" % _NAV)
    elif _PREDICATE not in init:
        errs.append("%s의 초기값 계산이 %s를 쓰지 않는다 — 판정을 자체 구현하고 있다" % (_NAV, _PREDICATE))

    # (d) 복원 effect가 applyParsedHash보다 **먼저** 그 술어를 참조한다
    eff = _restore_effect(nav)
    if eff is None:
        errs.append("%s에서 restoredRef를 쓰는 복원 effect를 못 찾았다" % _NAV)
    else:
        pi, ap = eff.find(_PREDICATE), eff.find("applyParsedHash")
        if pi < 0:
            errs.append("%s의 복원 effect가 %s로 무타깃을 걸러내지 않는다 — 해시 없는 진입까지 "
                        "딥링크로 취급해 초기값을 덮는다" % (_NAV, _PREDICATE))
        elif ap >= 0 and pi > ap:
            errs.append("%s의 복원 effect가 %s를 applyParsedHash **뒤에서** 참조한다 — 이미 덮은 뒤다"
                        % (_NAV, _PREDICATE))
    return errs


def _selftest():
    sources = _sources()
    base = _errors(sources)
    assert not base, "기준선이 이미 FAIL이라 대조군을 돌릴 수 없다:\n  " + "\n  ".join(base)
    by_rel = dict(sources)
    n = 0

    def hurt(rel, before, after, why):
        nonlocal n
        src = by_rel[rel]
        assert before in src, "주입 대상 «%s»를 %s에서 못 찾았다" % (before, rel)
        mutated = [(r, src.replace(before, after, 1) if r == rel else s) for r, s in sources]
        assert _errors(mutated), "%s에도 검사가 통과했다" % why
        n += 1

    # ① 초기값 계산이 술어를 버리고 판정을 자체 구현한다 — 지점이 2곳으로 갈린다
    hurt(_NAV, "%s(window.location.hash)" % _PREDICATE,
         "(!window.location.hash || window.location.hash === '#' || window.location.hash === '#/')",
         "초기값 계산의 판정 인라인 복사")
    # ② 복원 effect의 무타깃 가드를 무력화한다 — 딥링크 복원이 초기값을 다시 덮는다.
    #    가드 줄을 지우면 중괄호가 깨져 파서가 죽는다(결함이 아니라 주입 실패) → 술어 호출만 상수로 바꾼다.
    hurt(_NAV, "%s(initialHashRef.current)" % _PREDICATE, "false",
         "복원 effect의 무타깃 가드 무력화")
    # ③ 다른 파일에 판정 지점을 하나 더 심는다 — 결함 클래스 그 자체
    hurt("frontend/src/App.jsx", "return (",
         "return (\n      {window.location.hash === '#/' ? null : null}", "타 파일에 판정 지점 재주입")
    # ④ 정본의 export를 뗀다 — 소비처가 복사하게 된다
    hurt(_URLSTATE, "export function %s" % _PREDICATE, "function %s" % _PREDICATE,
         "정본 술어의 export 제거")
    # ⑤ 정본 선언 자체를 없앤다 — 판정 지점 0곳
    hurt(_URLSTATE, _PREDICATE, "isNoTargetRenamed", "정본 술어 선언 제거")

    print("대조군: 고의 결함 %d종(판정 인라인 복사 · 복원 가드 제거 · 타 파일 재주입 · export 제거 · "
          "선언 제거) 전부 FAIL 확인" % n)
    print("PASS")


def main():
    if "--selftest" in sys.argv:
        _selftest()
        return
    sources = _sources()
    errs = _errors(sources)
    assert not errs, "무타깃 진입 판정 단일 선언 불변식 위반:\n  " + "\n  ".join(errs)
    print("검사: 무타깃 판정이 정본 1곳(%s의 export %s)에만 있고 · 초기값 계산·복원 effect 둘 다 "
          "그것을 사용 (effect는 applyParsedHash보다 먼저 걸러냄)" % (_URLSTATE, _PREDICATE))
    print("PASS")


if __name__ == "__main__":
    main()
