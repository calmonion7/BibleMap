"""인트로 비트 컨테이너의 좌우 여백 불변식 검증 (task#280 S1).

이 프로젝트에는 `box-sizing: border-box` 전역 리셋이 없어 모든 요소가 `content-box`다. 그래서
`width: '100%'` + 좌우 패딩 조합은 박스를 뷰포트보다 패딩 2배만큼 넓게 만들고, 부모의
`alignItems:center`가 그것을 좌우 대칭으로 삐져나가게 놓아 **선언된 패딩이 시각적으로 정확히
0이 된다**(실측: 375px 폭에서 `left:-22, width:419`). 소스에는 패딩이 멀쩡히 적혀 있으므로
**코드 리뷰로는 잡히지 않는다** — 그래서 게이트가 소스 불변식을 단언한다(ADR 260820-232144).

단언하는 불변식 3종:
  (a) 명시 폭(`width`)과 좌우 패딩을 함께 쓰는 스타일 객체는 `boxSizing: 'border-box'`를 선언한다.
      — ADR 260820-232144의 국소 규약 그 자체. 인트로 안 어디서든 이 결함 클래스를 막는다.
  (b) 그런 객체는 파일 전체에 **정확히 1개**다(= 비트 공용 프레임). 같은 삼종을 손으로 복사하면
      선언 지점이 늘어나고, 늘어난 지점은 다음 사람이 (a)를 잊는 자리가 된다.
  (c) 그 프레임은 `wordBreak: 'keep-all'`을 선언한다 — 한국어를 어절 단위로 끊는다. 기본값
      (`normal`)은 "어디서나 찾 / 고"처럼 어절 중간에서 줄을 넘긴다. 여백과 같은 프레임이 책임진다.
  (d) 텍스트를 담는 비트 5곳(오프닝·지도·몽타주·메뉴장면·도착지)이 그 프레임을 통과한다.
      프레임 없이 맨몸으로 렌더되는 비트는 지금 당장 여백 결함이 아니어도 같은 함정에 열려 있다.

앱을 실행하지 않고 소스에서 정적으로 판정한다(import 부작용 0·실행 0) — `validate_intro_menu_parity`
와 같은 JSX 정규식 형태. 실측 여백 하한은 이 검증기가 아니라 `scripts/uat_intro_gutter.py`가 잰다.
소스 불변식과 실측은 서로를 대신하지 못한다: 이 검증기는 브라우저 없이 항상 돌고(check.sh 배선),
UAT는 "선언이 실제로 픽셀이 됐는가"를 잰다.

--selftest는 인메모리 사본에 고의 결함을 주입해 이 검사가 실제로 FAIL하는지 확인한다. 기준선에서
통과하는 게이트는 PASS만으로 아무것도 증명하지 못하고, 주입 대상을 하나로 고정하면 검사가 그
항목에 우연히 묶였는지 가릴 수 없다(회고 260820-003946·260820-190352) — 그래서 비트 5곳을 순회한다.
"""
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SRC = "frontend/src/IntroView.jsx"

# 프레임을 통과해야 하는 비트 렌더 지점 — 텍스트를 담는 비트 5곳.
# 오프닝(비트 0)은 자기 컴포넌트가 아니라 renderBeat의 p===0 분기에서 감싼다(Hero는 도착지와 공용).
# eco: 이름 하드코딩. 새 비트 컴포넌트가 늘면 여기 추가해야 하고, 안 하면 이 검증기는 침묵한다 —
# 그 구멍은 UAT(8비트 실측 순회)가 덮는다. 자동 발견이 필요해지면 renderBeat 분기를 파싱할 것.
_BEAT_RENDERERS = ["renderBeat", "MapBeat", "MontageBeat", "MenuScene", "Destination"]

_ZERO = re.compile(r"0(?:px|em|rem|%|vw|vh)?$")


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as f:
        return f.read()


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
    raise AssertionError("%s: 중괄호가 닫히지 않았다(offset %d)" % (_SRC, open_at))


def _style_objects(src):
    """(라벨, 본문) — JSX 인라인 style={{…}} 과 최상위 const 스타일 객체."""
    out = []
    for m in re.finditer(r"style=\{", src):
        i, j = _span(src, m.end() - 1)   # 바깥 {  (JSX 표현식 중괄호)
        k = src.index("{", i)            # 안쪽 {  (객체 리터럴)
        a, b = _span(src, k)
        out.append(("%s:%d style={{…}}" % (_SRC, src.count("\n", 0, m.start()) + 1), src[a:b]))
    for m in re.finditer(r"^const (\w+) = \{", src, re.M):
        a, b = _span(src, m.end() - 1)
        out.append(("%s:%d const %s" % (_SRC, src.count("\n", 0, m.start()) + 1, m.group(1)), src[a:b]))
    assert out, "%s에서 스타일 객체를 하나도 못 뽑았다" % _SRC
    return out


def _decl(body, key):
    """스타일 객체 본문에서 key 선언의 값 텍스트(다음 최상위 콤마까지). 없으면 None."""
    m = re.search(r"(?<![\w])%s:\s*" % key, body)
    if not m:
        return None
    depth, j = 0, m.end()
    while j < len(body):
        c = body[j]
        if c in "{[(":
            depth += 1
        elif c in "}])":
            if depth == 0:
                break
            depth -= 1
        elif c == "," and depth == 0:
            break
        j += 1
    return body[m.end():j].strip()


def _h_padding(body):
    """좌우 패딩을 선언하면 그 값 텍스트, 아니면 None. 삼항·템플릿 리터럴도 좌우 성분을 본다."""
    for key in ("paddingLeft", "paddingRight", "paddingInline", "paddingInlineStart", "paddingInlineEnd"):
        v = _decl(body, key)
        if v is not None and not _ZERO.match(v.strip("'\"")):
            return "%s: %s" % (key, v)
    v = _decl(body, "padding")
    if v is None:
        return None
    if "`" in v:
        return "padding: %s" % v   # 템플릿 리터럴 — 값 평가 불가, 좌우 패딩이 있다고 본다
    for lit in re.findall(r"'([^']*)'", v) or [v]:
        parts = lit.split()
        if not parts:
            continue
        h = [parts[1], parts[3]] if len(parts) == 4 else [parts[1] if len(parts) >= 2 else parts[0]]
        if any(not _ZERO.match(p) for p in h):
            return "padding: %s" % v
    return None


def _framed(body):
    """명시 폭 + 좌우 패딩을 함께 쓰는 컨테이너인가 — 결함 클래스의 정의."""
    w = _decl(body, "width")
    return w is not None and "auto" not in w and _h_padding(body) is not None


def _fn_body(src, name):
    """function name(…) { … } 또는 const name = (…) => { … } 의 본문."""
    m = re.search(r"function %s\s*\(" % name, src) or re.search(r"const %s\s*=\s*\(" % name, src)
    assert m, "%s에서 %s 정의를 못 찾았다" % (_SRC, name)
    a, b = _span(src, src.index("{", src.index(")", m.end() - 1)))
    return src[a:b]


def _errors(src):
    errs = []
    frames = [(label, body) for label, body in _style_objects(src) if _framed(body)]

    # (a) 결함 클래스 컨테이너는 border-box를 명시한다
    for label, body in frames:
        if _decl(body, "boxSizing") != "'border-box'":
            errs.append("%s — 명시 폭 + 좌우 패딩(%s)인데 boxSizing: 'border-box'가 없다 "
                        "(content-box라 패딩이 시각적으로 0이 된다)" % (label, _h_padding(body)))

    # (c) 프레임은 한국어 어절 단위 줄바꿈을 선언한다
    for label, body in frames:
        if _decl(body, "wordBreak") != "'keep-all'":
            errs.append("%s — 비트 공용 프레임인데 wordBreak: 'keep-all'이 없다 "
                        "(기본값은 어절 중간에서 줄을 넘긴다)" % label)

    # (b) 선언 지점은 공용 프레임 하나
    if len(frames) != 1:
        errs.append("폭+좌우패딩 컨테이너가 %d곳이다 — 공용 프레임 1곳으로 승급해야 한다: %s"
                    % (len(frames), " · ".join(l for l, _ in frames)) if frames
                    else "폭+좌우패딩 컨테이너가 0곳이다 — 비트 공용 프레임이 없다")

    # (d) 비트 5곳이 프레임을 통과한다
    if len(frames) == 1:
        frame = _frame_component(src, frames[0][0])
        for name in _BEAT_RENDERERS:
            if ("<%s" % frame) not in _fn_body(src, name):
                errs.append("%s가 공용 프레임 <%s>를 통과하지 않는다 — 맨몸 렌더는 같은 함정에 열려 있다"
                            % (name, frame))
    return errs


def _frame_component(src, label):
    """프레임 스타일 객체가 들어있는 컴포넌트 이름 — 라벨의 행 번호 이전 마지막 함수 선언."""
    line = int(re.search(r":(\d+) ", label).group(1))
    off = sum(len(l) + 1 for l in src.split("\n")[:line - 1])
    names = re.findall(r"function (\w+)\s*\(", src[:off])
    assert names, "프레임 스타일 객체를 담은 컴포넌트를 못 찾았다 (%s)" % label
    return names[-1]


def _selftest():
    src = _read(_SRC)
    assert not _errors(src), "기준선이 이미 FAIL이라 대조군을 돌릴 수 없다:\n  " + "\n  ".join(_errors(src))
    frame = _frame_component(src, [l for l, b in _style_objects(src) if _framed(b)][0])
    n = 0

    # ① 프레임에서 border-box를 뗀다 — 결함 클래스가 그대로 되살아난다
    hurt = src.replace("boxSizing: 'border-box',", "", 1)
    assert hurt != src, "주입 대상 boxSizing: 'border-box'를 프레임에서 못 찾았다"
    assert _errors(hurt), "border-box 제거에도 검사가 통과했다"
    n += 1

    # ② 프레임에서 keep-all을 뗀다 — 한국어가 어절 중간에서 끊긴다
    hurt = src.replace("wordBreak: 'keep-all',", "", 1)
    assert hurt != src, "주입 대상 wordBreak: 'keep-all'을 프레임에서 못 찾았다"
    assert _errors(hurt), "keep-all 제거에도 검사가 통과했다"
    n += 1

    # ③ 비트마다 손 패딩 컨테이너를 재주입한다 — 선언 지점이 다시 늘어난다 (전 비트 순회)
    for name in _BEAT_RENDERERS:
        body = _fn_body(src, name)
        k = src.index(body) + body.index("return (") + len("return (")
        hurt = src[:k] + "\n    <div style={{ width: '100%', padding: '0 22px' }} />" + src[k:]
        assert _errors(hurt), "%s에 손 패딩 컨테이너를 재주입했는데 검사가 통과했다" % name
        n += 1

    # ④ 비트마다 프레임 통과를 끊는다 — 맨몸 렌더 회귀 (전 비트 순회)
    for name in _BEAT_RENDERERS:
        body = _fn_body(src, name)
        assert ("<%s" % frame) in body, "%s가 프레임을 통과하지 않는다(기준선 이상)" % name
        hurt = src.replace(body, body.replace("<%s" % frame, "<div", 1), 1)
        assert _errors(hurt), "%s의 프레임 통과를 끊었는데 검사가 통과했다" % name
        n += 1

    print("대조군: 고의 결함 %d종(border-box 제거 · keep-all 제거 · 손 패딩 재주입 · 프레임 이탈, 비트 %d곳 순회) 전부 FAIL 확인"
          % (n, len(_BEAT_RENDERERS)))
    print("PASS")


def main():
    if "--selftest" in sys.argv:
        _selftest()
        return
    src = _read(_SRC)
    errs = _errors(src)
    assert not errs, "인트로 비트 컨테이너 여백 불변식 위반:\n  " + "\n  ".join(errs)
    frames = [l for l, b in _style_objects(src) if _framed(b)]
    print("검사: 폭+좌우패딩 선언 지점 1곳(%s, border-box·keep-all 명시) · 비트 %d곳 전부 프레임 통과"
          % (frames[0], len(_BEAT_RENDERERS)))
    print("PASS")


if __name__ == "__main__":
    main()
