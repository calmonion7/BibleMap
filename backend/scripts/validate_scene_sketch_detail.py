"""장면 스케치 저작 규약 경계 B1~B6 검증 (task#286 S4 — 파일럿).

투어 정차지 장면 스케치의 밀도가 중앙 10선에 그쳐 "그려지는" 연출이 한 박에 끝나 버렸다.
task#286이 목표 밀도(35~40선)와 붓질 단계 경계를 규약으로 확정했고, 이 검증기가 그것을 강제한다.
규약 정본은 `frontend/src/sketches/lib.jsx`의 "장면 저작 규약" 절이다.

  B1 밀도       장면당 stroke >= 30
  B2 단계 상한  어떤 붓질 단계(= 같은 지연값)도 선 3개 초과 금지
  B3 단계 하한  단계 수 >= ceil(선 수 / 3)
  B4 시간 예산  드로인 총 길이(= max(지연) + --dur-draw-scene) <= 10,000ms(task#303 S1 천장 상향)
  B5 절정 순서  그 장면의 모든 SMIL begin >= 드로인 종료 시각
  B6 종속 관계  패널 대기(450ms) + 드로인 총 길이 <= min(stepDuration)
  B7 구조 밀도  굵기 >= 2.0인 stroke >= 12개 (사람·사물의 구조)
  B8 배경 상한  반투명(opacity < 1) stroke가 전체의 40% 이하
  B9 연출 완료  패널 대기 + 마지막 연출(SMIL·이름표) **종료** 시각 <= min(stepDuration)
  B10 배치 분리 이름표(글) 상자에 어떤 stroke도 들어오지 않고, 상자가 프레임 안에 있다
  B11 구조 연결 구조 선(굵기 >= 2.0)은 다른 구조 선과 2.0단위 안에서 만난다 — 부위가 떠 있지 않다
  B12 정본 강제  장면에 인물 이름표가 있고 그 인물의 정본(cast/*.jsx)이 있으면 그 장면은 정본
                컴포넌트를 써야 한다(task#307 S3, ADR 260823-190821 3항). 이름표 없이 그려진
                인물은 기계 신호가 없어 대상에서 빠진다 — 대안 없음(미결로 남긴다).

**정본 컴포넌트 인라인 전개(B12와 짝)**: `<David cx={..} .../>`는 커스텀 컴포넌트라 위 태그
스캐너에 안 걸린다 — 그대로 두면 B1·B2·B7·B8·B10·B11이 정본 사용 장면에서 조용히 헛돈다
(ADR 260821-000937 "초록인데 결함이 남는다"). `<Label>`을 label_boxes()로 따로 읽는 전례를 따라,
`cast/*.jsx`(직속 파일만 — `cast/props/*.jsx`는 지물 참고 도상이라 비강제, 열거에서 자연히 빠진다)
소스를 직접 읽어 호출부 리터럴로 치환·평가한 뒤(expand_cast) 그 결과를 장면 본문에 끼워 넣는다.
강제 대상 명단은 상수로 박지 않고 매 호출 디렉터리 열거에서 파생한다(ADR 260822-220823).

**경계를 이 파일에 박지 않는다 — 실제 소스에서 파생한다.** `--dur-draw-scene`(장면 스케치 전용,
인물·책 인장의 `--dur-draw`와는 분리된 토큰)은 `index.css`,
패널 대기는 `tourSketches.jsx`, `stepDuration` 공식은 `useTourPlayback.js`, note 길이는
`data/tours/*.json`에서 읽는다. 상수를 복사해 두면 누가 타이밍을 바꿨을 때 게이트가 조용히
거짓 초록이 된다(불변식은 개수가 아니라 경계다 — ADR 260821-000937).

**단계는 `<g>` 개수가 아니라 지연값으로 센다.** 같은 지연을 가진 `<g>`를 여러 개로 쪼개도
관객에겐 한 박에 우수수 나타나는 것과 같기 때문이다 — 그렇게 세면 B2/B3가 게임된다.

--selftest는 각 경계를 **개별로** 위반하는 합성 장면을 **같은 판정 함수**에 주입해 6건 모두
빨강이 되는지 확인한다. 기준선 PASS만으론 게이트가 살아있음을 증명하지 못한다
(ADR 260820-003946). 실제 소스는 건드리지 않는다.
B6은 B4(10,000ms)보다 느슨해 장면을 늘리는 방식으로는 단독 위반을 만들 수 없다 —
그래서 대조군은 재생 쪽 레버(min(stepDuration))를 줄여 관계가 깨지는 것을 확인한다.
"""
import functools
import glob
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _svgpath import points as _path_points  # noqa: E402  경로 d → 절대 좌표 점

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SKETCH_DIR = os.path.join(_ROOT, "frontend/src/sketches")

# 검사 대상. "모듈.jsx:장면함수" = 그 장면만, "모듈.jsx" = 그 모듈의 전 장면.
# 파일럿(task#286)은 3장면으로 시작하고, 확장 파트(task#288~296)가 모듈을 통째로 추가한다.
TARGETS = [
    "ageOfJudges.jsx:SamuelCircuitScene",
    "gospelOfJesus.jsx:TransfigurationScene",
    "davidUnitedKingdom.jsx:GoliathScene",
    "davidUnitedKingdom.jsx:EnGediScene",       # task#307 S4 — 다윗 정본 배선
    "davidUnitedKingdom.jsx:GibeahHarpScene",   # task#307 S4 — 다윗 정본 배선
]

MIN_STROKES = 35           # B1 — task#303 S5: 30→35로 소폭 래칫(바닥은 개수가 아니라 경계로 다시
                           # 매길수록 안전하다 — ADR 260821-000937). 3장면 실측(191~198선)의
                           # 90%(~172)까지 올리지 않은 이유: TARGETS는 지금 이 3장면뿐이지만
                           # 9파트 확장(.forge/backlog/scene-sketch-detail-*)이 모듈째 편입되면
                           # 이 상수는 그 모듈의 **전 장면**(단순한 2인 장면 포함)에 적용된다.
                           # 191~198은 "상한형"(다인물 밀집 장면) 실측이지 lib.jsx가 참고치로 적은
                           # "기본형"(40~45)의 대체값이 아니다 — 그대로 172로 올리면 앞으로
                           # 추가될 단순 장면 다수가 이 바닥에 못 미쳐 게이트가 빨강이 된다.
                           # 35는 그 참고치(40~45)에 근접한 최소 보수치로, 셀프테스트 대조군
                           # 전역이 쓰는 36선 기준선(_synthetic(36, ...))보다 낮아 무해하다.
                           # 9파트가 적용할 목표 밀도 자체는 **task#305 미결**이다(lib.jsx B1 참조) —
                           # 이 바닥은 그 결정과 독립적으로 유효하고, 결정 뒤 재래칫 대상이다.
MAX_PER_STEP = 3           # B2
MAX_DRAWIN_MS = 10000      # B4 — task#303 S1: 선 천장을 54→240 수준으로 올리며 함께 상향(구 7,000).
                           # --dur-draw-scene을 1000→500ms로 낮춘 것과 짝이다(구멍 B 대응) — 그대로
                           # 두면 간격만 좁혀 선을 늘릴 때 동시 진행 선 수가 폭발한다(lib.jsx 참조).
STRUCT_WEIGHT = 2.0        # B7 — 이 굵기 이상을 "구조 선"(주역·지물)으로 본다
MIN_STRUCT = 12            # B7
MAX_FAINT_RATIO = 0.40     # B8

# B7·B8은 **B1이 개수만 재고 값어치를 못 재던 구멍**을 막는다(파일럿 판정, 2026-08-21).
# 파일럿 재작도 실측: 사무엘 구조 3/36(8%)·반투명 81%, 변화산 4/36(11%)·반투명 61% —
# 경계 B1을 통과했지만 늘어난 선이 대부분 옅은 배경 획이라 화면 인상이 그만큼 달라지지 않았다.
# 기준점은 원래 제대로 그려져 있던 GoliathScene: 구조 15/39(38%) · 반투명 11/39(28%).
# 두 경계가 각각 다른 회피를 막는다 — B7은 구조를 실제로 그리게 하고, B8은 유령 획으로 개수를
# 채우지 못하게 한다. 굵기 위계의 의미는 lib.jsx 규약 주석이 정본이다.
_SW = re.compile(r"sw\(\s*([0-9.]+)\s*(?:,\s*([0-9.]+))?\s*\)")

# B9 — B5·B6은 드로인까지만 본다. 절정이 드로인 뒤에 오고(B5) 드로인이 step 안에 끝나도(B6),
# **절정 자체가 step을 넘겨 끝나면 관객은 결말을 못 본다.** 2차 재작도에서 사무엘의 여유가
# 90ms로 측정돼(연출 종료 8,900ms + 패널 450ms = 9,350ms / step 9,440ms) 실물에서 잘릴 상태였다.
# B6과 같은 보수적 형태(min(stepDuration) 기준)를 쓴다 — 그 정차지의 step으로만 재면 note가 짧은
# 정차지로 장면이 옮겨졌을 때 조용히 깨진다. 대가는 필요보다 엄격하다는 것이고, 그게 맞는 대가다.
# `<Label at="Ns">`는 0.4s 페이드인이다(SceneLabel.jsx) — 이름표도 연출이므로 함께 센다.
# `<Label after={i}>`(task#306 S2, ADR 260823-112504)는 드로인 완료(drawin)에서 파생한다 —
# 종료 시각 = drawin + i*250(스태거) + 400(페이드). at=처럼 수동값이 아니라 drawin에 종속되므로
# scan_scene이 아니라 여기(drawin을 아는 judge)에서 계산해 ends에 합류시킨다.
#
# has_color(task#306 S4, 적대적 리뷰로 드러난 구멍 — 재검증에서 메움): 레지스트리에 color 필드가
# 있는 장면은 드로인 뒤 "압축 색칠 붓"(wash)이 끼어들어 이름표가 drawin이 아니라
# --reveal-end(= drawin + washSpan, tourSketches.jsx)에서 페이드인한다. 이 축을 모르면 게이트가
# wash로 늘어난 실제 종료 시각을 못 보고 조용히 초록이 된다 — ADR 260823-112504가 고치려던
# "게이트가 이 축을 보지 않는다" 결함 클래스가 색층에서 좁게 재발한 사례. _reveal_last()가
# tourSketches.jsx의 washSpan 공식을 그대로 이식해 재현한다(GLOBAL_MIN_STEP_MS는 그 파일의
# 상수를 여기 min_step과 대조해 어긋남을 잡는다 — _global_min_step_ms_js() 참조).
# B10 — 사용자 지시(2026-08-21): "그림과 글이 겹치지 않게 배치".
# 이름표는 종이색 헤일로(SceneLabel.jsx의 stroke="var(--paper)")로 그림 위에서도 읽히게 돼 있지만,
# 그 장치는 겹침을 **견디는** 것이고 겹치지 않는 것과는 다르다. 실측 결과 세 장면 모두 이름표가
# 선을 관통했고("다윗" 하나에 34개 선이 걸렸다), "라마로 돌아오다"는 x=126까지 나가 프레임 밖이었다.
#
# 판정은 **선분 대 상자 교차**로 한다. 바운딩 박스끼리 비교하면 가로로 긴 지면선 하나가 그 띠 전체를
# 덮은 것으로 잡혀 과대평가되고, 점만 검사하면 상자를 관통하는 직선을 놓친다(끝점이 밖에 있으므로).
# 글자 폭은 한글 기준 1자 ≈ 0.98em로 어림한다 — 정확한 텍스트 메트릭은 브라우저만 알지만,
# 여백 LABEL_PAD가 그 오차를 흡수한다.
_LABEL = re.compile(r'<Label\b([^>]*)>(.*?)</Label>', re.S)
_ATTR = lambda a, k: (lambda m: float(m.group(1)) if m else None)(re.search(rf'\b{k}="([-0-9.]+)"', a))
LABEL_PAD = 1.0        # 이름표 상자 여백(단위)

# B11 — 사용자 지적(2026-08-21): "예수님 몸과 얼굴이 너무 떨어져있지 않음? 다윗의 몸과 다리가 안맞음".
# 실측하니 머리·팔·다리가 몸에서 2.4~5.9단위 떠 있었다(예수 머리 5.9 · 골리앗 다리 3.5 · 엘리야
# 지팡이 4.9 · 사무엘 팔 2.9 …). 저작 에이전트가 부위를 **잇지 않고 따로** 그린 결과다.
# 렌더 배율이 약 3.7px/단위라 3단위 공백은 11px — 눈에 그대로 보인다.
#
# **구조 선(굵기 >= 2.0)에만 적용한다.** 배경·질감(구름·새·지면 자갈)은 원래 떨어져 있는 것이 정상이고,
# 전체에 걸면 거짓 양성이 쏟아진다. 구조 선은 사람·사물의 형태를 이루므로 반드시 연결된 조립체여야 한다.
# 홀로 선 굵은 선(예: 외딴 기둥) 하나는 거짓 양성이 될 수 있다 — 그 경우 굵기를 낮추거나 이어 붙인다.
JOINT_GAP = 2.0        # B11 — 구조 선끼리 이 거리 안에서 만나야 한다(단위)
FRAME = (0, 0, 120, 64)  # viewBox

# ── 정본 컴포넌트 인라인 전개 (B12, task#307 S3, ADR 260823-190821 3항) ─────────
# 강제 대상은 `cast/*.jsx`를 **여기서 매 호출 열거**한다 — 명단을 상수로 박지 않는다
# (ADR 260822-220823 "위임된 정본은 미결을 미결로": 박으면 재작도가 이름표를 늘릴 때마다
# 이 파일도 고쳐야 하고, 고치는 걸 잊으면 새 정본이 강제되지 않은 채 조용히 통과한다).
# `glob("*.jsx")`는 하위 디렉터리로 내려가지 않으므로 `cast/props/*.jsx`(지물 참고 도상,
# 비강제)는 별도 제외 코드 없이 자연히 빠진다.
_CAST_DIR = os.path.join(_SKETCH_DIR, "cast")
_CAST_SIG = re.compile(r"export default function ([A-Za-z0-9_]+)\s*\(\{([^}]*)\}\)\s*\{")
_CAST_ALIASES = re.compile(r"export const aliases\s*=\s*\[([^\]]*)\]")
_CAST_GAP = re.compile(r"export const STEP_GAP\s*=\s*(\d+)")
_CALL_PROPS = {"cx", "cy", "scale", "delay"}


def _brace_body(src, open_idx):
    """src[open_idx] == '{'의 매칭되는 '}' 안쪽 텍스트. 문자열·백틱(템플릿 리터럴)을 존중한다 —
    백틱 안의 `${...}`는 그 자체가 데이터이므로 depth에 영향을 주지 않는다(여기서 필요한 건 함수
    몸통의 바깥쪽 중괄호 짝뿐, 백틱 내부 문법 해석이 아니다)."""
    assert src[open_idx] == "{"
    depth, i, n, quote = 0, open_idx, len(src), ""
    while i < n:
        c = src[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = ""
        elif c in "\"'`":
            quote = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[open_idx + 1:i]
        i += 1
    raise AssertionError(f"중괄호 짝을 찾지 못했다(open_idx={open_idx})")


@functools.lru_cache(maxsize=1)
def _cast_components():
    """`cast/*.jsx`(직속 파일만) → {컴포넌트명: {aliases, step_gap, body, path}}.
    정본 컴포넌트 규약(lib.jsx "정본 컴포넌트 규약" 절 — 호출 prop 4개·transform 금지·조건 분기
    금지)을 여기서도 검사한다: 위반이면 전개기가 파서로 남을 수 없으므로 즉시 멈춘다."""
    out = {}
    for path in sorted(glob.glob(os.path.join(_CAST_DIR, "*.jsx"))):
        rel = os.path.relpath(path, _ROOT)
        src = _read(rel)
        m = _CAST_SIG.search(src)
        assert m, (f"{rel}: 정본 컴포넌트 규약 위반 — "
                    "`export default function Name({ cx, cy, scale, delay })` 형태가 아니다")
        name = m.group(1)
        params = {p.strip() for p in m.group(2).split(",")}
        assert params == _CALL_PROPS, (
            f"{rel}: 호출 규약 위반 — prop은 cx·cy·scale·delay 넷만 허용한다(실제 {sorted(params)})")
        gap_m = _CAST_GAP.search(src)
        assert gap_m, f"{rel}: export const STEP_GAP이 없다"
        alias_m = _CAST_ALIASES.search(src)
        aliases = re.findall(r"['\"]([^'\"]+)['\"]", alias_m.group(1)) if alias_m else []
        body = _brace_body(src, m.end() - 1)
        assert "transform" not in body, f"{rel}: 정본 컴포넌트 규약 위반 — transform 금지"
        assert not re.search(r"&&|\?[^:]*:|\bif\s*\(", body), f"{rel}: 정본 컴포넌트 규약 위반 — 조건 분기 금지"
        out[name] = {"aliases": aliases, "step_gap": int(gap_m.group(1)), "body": body, "path": rel}
    return out


def _fmt_num(v):
    v = round(float(v), 4)
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


_EVAL_SAFE = re.compile(r"^[-0-9+*/.() \s]+$")


def _eval_arith(expr):
    """리터럴로 치환된 산술식만 평가한다 — 다른 토큰이 남아 있으면(규약 위반) 여기서 멈춘다."""
    expr = expr.strip()
    assert _EVAL_SAFE.match(expr), f"정본 컴포넌트 규약 위반 — 리터럴 산술이 아닌 표현식: {expr!r}"
    return _fmt_num(eval(expr, {"__builtins__": {}}, {}))  # noqa: S307 — 위에서 산술 문자만 걸렀다


_D_CALL = re.compile(r"\bd\(([^,]+),\s*(\w+)\)")
_BACKTICK_D = re.compile(r"d=\{`([^`]*)`\}")
_DOLLAR_EXPR = re.compile(r"\$\{([^}]*)\}")
_LITERAL_ATTR = re.compile(r"\b(cx|cy|r)=\{([^{}]*)\}")


def _expand_component_body(comp, cx0, cy0, scale0, delay0):
    """정본 컴포넌트 로컬 좌표 소스 → 호출부 리터럴로 아핀 변환된 JSX 조각.
    좌표 계약(cast/david.jsx 주석 정본): (x,y) → (cx+x*scale, cy+y*scale), 델타는 *scale만,
    지연은 delay+K*STEP_GAP. stroke-width(sw(...))는 계약 밖이라 손대지 않는다 — 정본 규약이
    scale로 굵기를 곱하지 않기 때문이다(작을수록 상대적으로 굵어지는 쪽이 실루엣을 지킨다,
    cast/david.jsx 주석)."""
    subs = {
        "cx": _fmt_num(cx0), "cy": _fmt_num(cy0), "scale": _fmt_num(scale0),
        "delay": _fmt_num(delay0), "STEP_GAP": str(comp["step_gap"]),
    }
    text = comp["body"]
    for name, val in subs.items():
        # (?!=) — attrName= 형태(예: `cx={cx + 0*scale}`의 속성 '이름' cx)는 건드리지 않는다.
        # 그 자리를 리터럴로 바꾸면 `cx=`가 `60=`가 되어 이후 stroke_segments/structural_polylines의
        # cx="..." cy="..." 리터럴 매칭이 원을 통째로 놓친다(적대적 리뷰로 드러난 결함, B10·B11 재발).
        text = re.sub(rf"\b{name}\b(?!=)", val, text)
    text = _D_CALL.sub(lambda m: f"d({_eval_arith(m.group(1))}, {m.group(2)})", text)
    text = _BACKTICK_D.sub(
        lambda m: 'd="' + _DOLLAR_EXPR.sub(lambda d: _eval_arith(d.group(1)), m.group(1)) + '"', text)
    text = _LITERAL_ATTR.sub(lambda m: f'{m.group(1)}="{_eval_arith(m.group(2))}"', text)
    # 위 제외 때문에 속성 '이름' cx=/cy=는 위 루프에서 치환되지 않고 그대로 남는다(의도됨 —
    # _LITERAL_ATTR가 그 뒤에 값만 리터럴 문자열로 바꿔 cx="60" 형태를 만든다). 그래서 여기 잔존
    # 검사도 같은 (?!=) 제외를 써야 한다 — 아니면 정상 출력의 `cx="60"`까지 "남은 심볼"로 오탐한다.
    assert not re.search(r"\b(cx|cy|scale|delay|STEP_GAP)\b(?!=)", text), (
        f"{comp['path']}: 전개 후에도 남은 심볼 — 정본 컴포넌트 규약 위반(리터럴이 아닌 참조가 있었다)")
    return text


_CALL_TAG_PROPS = re.compile(r"(\w+)=\{([^{}]*)\}")


def expand_cast(body, registry):
    """장면 본문에서 정본 컴포넌트 호출(`<Name cx={..} cy={..} scale={..} delay={..} />`)을 찾아
    인라인 전개한 본문으로 치환한다. 호출부 규약(숫자 리터럴 4개만, transform 금지)을 어기면
    AssertionError. 반환: (전개된 본문, 사용된 컴포넌트명 집합) — 집합은 B12 판정 입력이다."""
    used = set()
    if not registry:
        return body, used
    call_re = re.compile(r"<(" + "|".join(re.escape(n) for n in registry) + r")\b([^>]*?)/>")
    out, pos = [], 0
    for m in call_re.finditer(body):
        out.append(body[pos:m.start()])
        name, attrs = m.group(1), m.group(2)
        assert "transform" not in attrs, f"{name} 호출부에 transform이 있다 — 정본 호출 규약 위반"
        props = dict(_CALL_TAG_PROPS.findall(attrs))
        assert set(props) == _CALL_PROPS, (
            f"{name} 호출부 prop이 규약과 다르다(cx·cy·scale·delay 넷만 허용): {sorted(props)}")
        for k, v in props.items():
            assert re.fullmatch(r"-?[0-9]+(\.[0-9]+)?", v.strip()), (
                f"{name} 호출부의 {k} prop이 숫자 리터럴이 아니다(표현식·변수 금지): {v!r}")
        out.append(_expand_component_body(
            registry[name], float(props["cx"]), float(props["cy"]),
            float(props["scale"]), float(props["delay"])))
        used.add(name)
        pos = m.end()
    out.append(body[pos:])
    return "".join(out), used


_DUR = re.compile(r'\bdur\s*=\s*"([^"]+)"')
_LABEL_AT = re.compile(r'<Label[^>]*\bat="([0-9.]+)"')
_LABEL_FADE_MS = 400
# after={i}(task#306 S2, ADR 260823-112504) — 드로인 완료(drawin)에서 파생하는 이름표. i*250ms
# 스태거 + 400ms 페이드(index.css .scene-label-last, SceneLabel.jsx). drawin은 scan_scene 시점엔
# 아직 모르므로(steps 집계가 끝나야 나온다) 인덱스만 여기서 모으고, 종료 시각 계산은 judge()가 한다.
_LABEL_AFTER = re.compile(r'<Label[^>]*\bafter=\{(\d+)\}')
_DEFAULT_WEIGHT = 1.1      # sw() 없이 {...P}만 쓴 선 — svg 루트의 strokeWidth 기본값

_STROKE_TAGS = {"path", "circle", "ellipse", "line", "polyline", "rect"}
_SMIL_TAGS = {"animate", "animateTransform", "animateMotion", "set"}
# `export function`도 장면 정의다 — introMontage.jsx로 옮긴 인트로 5씬이 그 형태다(task#287).
_SCENE_DEF = re.compile(r"^(?:export\s+)?function\s+([A-Za-z0-9_]*Scene)\s*\(", re.M)
# d(...)의 첫 인자에 든 정수의 **최대값**을 지연으로 본다. `d(reduce ? 0 : 5000, reduce)` 형태가
# 실제로 쓰이며(davidUnitedKingdom.jsx), 첫 정수만 읽으면 0으로 오독해 게이트가 거짓 초록이 된다
# — 브라우저 실측(6,000ms)과 정적 파싱(2,700ms)이 어긋나 잡힌 결함이다. reduce 분기는 항상 0이므로
# 최대값이 곧 재생 시 지연이다.
_DELAY = re.compile(r"\bd\(([^,)]*)")
_BEGIN = re.compile(r'\bbegin\s*=\s*"([^"]+)"')


# ── 소스에서 파생하는 상수 ────────────────────────────────────────────────────
def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as f:
        return f.read()


@functools.lru_cache(maxsize=1)
def _stroke_scale():
    # sw(n)이 DOM에 내보내는 굵기는 n x W다 — W를 여기에 복사하지 않고 lib.jsx에서 파생한다.
    # 상수를 복사하면 누가 W를 바꿨을 때 기하 판정(B10·B11)이 조용히 어긋난다
    # (ADR 260820-003946 - 스크립트 가드는 게이트에서 재현된다 / 260821-000937).
    m = re.search(r"^export const W\s*=\s*([0-9.]+)", _read("frontend/src/sketches/lib.jsx"), re.M)
    assert m, "lib.jsx에서 export const W를 찾지 못했다 - 굵기 배율이 바뀌었다면 이 검증기도 갱신하라"
    return float(m.group(1))


def _dur_draw_ms():
    # 장면 스케치는 --dur-draw-scene을 쓴다(task#303 S1) — 인물·책 인장·가계도 실이 쓰는 공용
    # --dur-draw(1000ms 그대로)와는 별개 토큰이라 이걸 읽어야 실제 재생 속도와 일치한다.
    m = re.search(r"--dur-draw-scene:\s*(\d+)ms", _read("frontend/src/index.css"))
    assert m, "index.css에서 --dur-draw-scene을 찾지 못했다 — 타이밍 모델이 바뀌었다면 이 검증기도 갱신하라"
    return int(m.group(1))


def _panel_delay_ms():
    m = re.search(r"setReady\(true\),\s*(\d+)\)", _read("frontend/src/tourSketches.jsx"))
    assert m, "tourSketches.jsx에서 패널 대기(setReady 타이머)를 찾지 못했다"
    return int(m.group(1))


def _min_step_ms():
    """useTourPlayback.js의 실제 공식 + 실제 note 길이로 계산한 최소 step."""
    src = _read("frontend/src/useTourPlayback.js")
    m = re.search(
        r"return\s+(\d+)\s*\+\s*\(note\s*\?\s*Math\.min\(note\.length\s*\*\s*(\d+),\s*(\d+)\)",
        src,
    )
    assert m, "useTourPlayback.js에서 stepDuration 공식을 파싱하지 못했다"
    base, mult, cap = (int(g) for g in m.groups())
    lens = [
        len(s.get("note") or "")
        for f in glob.glob(os.path.join(_ROOT, "data/tours/*.json"))
        for s in json.load(open(f, encoding="utf-8"))["stops"]
    ]
    assert lens, "투어 정차지를 하나도 읽지 못했다"
    return min(base + min(n * mult, cap) for n in lens)


def _global_min_step_ms_js():
    # tourSketches.jsx의 GLOBAL_MIN_STEP_MS(task#306 S4 재검증) — 채색 wash가 예산을 정할 때 쓰는
    # 전역 보수 상한. _min_step_ms()가 매번 data/tours/*.json 전건을 다시 읽어 계산한 값과
    # _check()가 대조한다 — 그 파일에 값을 그냥 복사해 둔 게 아니라는 살아있는 증거(ADR 260820-003946).
    m = re.search(r"GLOBAL_MIN_STEP_MS\s*=\s*(\d+)", _read("frontend/src/tourSketches.jsx"))
    assert m, "tourSketches.jsx에서 GLOBAL_MIN_STEP_MS를 찾지 못했다 — 채색 wash 예산 상수 이름이 바뀌었다면 이 검증기도 갱신하라"
    return int(m.group(1))


# ── JSX 스캔 ─────────────────────────────────────────────────────────────────
def _delay_of(attrs, inherited):
    """이 태그 자신의 지연. d(...)가 없으면 상속값."""
    m = _DELAY.search(attrs)
    if not m:
        return inherited
    nums = re.findall(r"\d+", m.group(1))
    assert nums, f"d(...)의 지연을 읽지 못했다(정수 없음): {m.group(0)!r}"
    return max(int(n) for n in nums)


def _tags(src):
    """<tag ...> / </tag> / <tag ... /> 를 순서대로 흘린다. 속성 안의 {}·따옴표를 존중한다."""
    i, n = 0, len(src)
    while True:
        i = src.find("<", i)
        if i < 0:
            return
        m = re.match(r"</?([A-Za-z][A-Za-z0-9]*)", src[i:])
        if not m:
            i += 1
            continue
        closing = src[i + 1] == "/"
        name = m.group(1)
        j, depth, quote = i + m.end(), 0, ""
        while j < n:
            c = src[j]
            if quote:
                if c == quote:
                    quote = ""
            elif c in "\"'":
                quote = c
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            elif c == ">" and depth == 0:
                break
            j += 1
        attrs = src[i + m.end(): j]
        yield name, closing, attrs.rstrip().endswith("/"), attrs
        i = j + 1


def _begin_ms(value):
    m = re.match(r"\s*([0-9.]+)\s*(ms|s)?\s*$", value)
    if not m:
        return None  # 이벤트 기반 begin(예: "click") — 시각 판정 대상 아님
    v = float(m.group(1))
    return v if m.group(2) == "ms" else v * 1000


def scan_scene(body):
    """장면 본문 → (지연별 stroke 수, SMIL begin(ms), [(굵기, 반투명)], 연출 종료 시각(ms),
    after= 이름표 인덱스 목록)."""
    steps, begins, weights, ends, stack = {}, [], [], [], [0]
    for name, closing, self_closing, attrs in _tags(body):
        if closing:
            if name == "g" and len(stack) > 1:
                stack.pop()
            continue
        delay = _delay_of(attrs, stack[-1])
        if name == "g":
            if not self_closing:
                stack.append(delay)
            continue
        if name in _STROKE_TAGS:
            # 지연은 <g>뿐 아니라 stroke 요소 자신에게도 걸린다(예: <circle style={d(3500, false)}>).
            steps[delay] = steps.get(delay, 0) + 1
            sw = _SW.search(attrs)
            if sw:
                weights.append((float(sw.group(1)), sw.group(2) is not None and float(sw.group(2)) < 1))
            else:
                weights.append((_DEFAULT_WEIGHT, False))
        elif name in _SMIL_TAGS:
            m = _BEGIN.search(attrs)
            if m:
                ms = _begin_ms(m.group(1))
                if ms is not None:
                    begins.append(ms)
                    d = _DUR.search(attrs)
                    ends.append(ms + ((_begin_ms(d.group(1)) or 0) if d else 0))
    # 이름표 페이드인도 연출이다 — <Label>은 컴포넌트라 태그 스캔에 안 걸리므로 따로 읽는다.
    ends += [float(a) * 1000 + _LABEL_FADE_MS for a in _LABEL_AT.findall(body)]
    afters = [int(a) for a in _LABEL_AFTER.findall(body)]
    return steps, begins, weights, ends, afters


def label_boxes(body):
    """<Label> → (텍스트, x0, y0, x1, y1). 기준선은 y, 폭은 글자수 * size * 0.98."""
    out = []
    for m in _LABEL.finditer(body):
        a, txt = m.group(1), re.sub(r"\{[^}]*\}", "", m.group(2)).strip()
        if not txt:
            continue
        size = _ATTR(a, "size") or 4.6
        x = _ATTR(a, "x") or 0.0
        y = _ATTR(a, "y") or 0.0
        anc = (re.search(r'anchor="(\w+)"', a) or [None, "middle"])[1]
        w = len(txt) * size * 0.98
        x0 = x - w / 2 if anc == "middle" else (x if anc == "start" else x - w)
        out.append((txt, x0, y - size * 0.82, x0 + w, y + size * 0.20))
    return out


def stroke_segments(body):
    """모든 stroke의 절대 좌표 선분 [(x1,y1,x2,y2,half굵기)]."""
    segs = []
    scale = _stroke_scale()
    for tag in re.findall(r"<(?:path|circle|ellipse|line|polyline|rect)\b[^>]*>", body, re.S):
        sw = _SW.search(tag)
        half = (float(sw.group(1)) if sw else _DEFAULT_WEIGHT) * scale / 2
        d = re.search(r'\bd="([^"]+)"', tag)
        if d:
            pts = _path_points(d.group(1))
            segs += [(*pts[i], *pts[i + 1], half) for i in range(len(pts) - 1)]
            if len(pts) == 1:
                segs.append((*pts[0], *pts[0], half))
            continue
        c = re.search(r'cx="([-0-9.]+)"\s*cy="([-0-9.]+)"\s*r="([0-9.]+)"', tag)
        if c:
            cx, cy, r = (float(v) for v in c.groups())
            ring = [(cx + r * math.cos(t * math.pi / 6), cy + r * math.sin(t * math.pi / 6)) for t in range(13)]
            segs += [(*ring[i], *ring[i + 1], half) for i in range(12)]
    return segs


def _seg_hits_box(x1, y1, x2, y2, half, box):
    """선분이 상자(여백 포함)와 만나는가 — Liang-Barsky."""
    bx0, by0, bx1, by1 = box[0] - half, box[1] - half, box[2] + half, box[3] + half
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x1 - bx0), (dx, bx1 - x1), (-dy, y1 - by0), (dy, by1 - y1)):
        if p == 0:
            if q < 0:
                return False
            continue
        r = q / p
        if p < 0:
            if r > t1:
                return False
            t0 = max(t0, r)
        else:
            if r < t0:
                return False
            t1 = min(t1, r)
    return t0 <= t1


def structural_polylines(body):
    """구조 선(굵기 >= 2.0)마다 절대 좌표 점 목록. B11 판정 입력."""
    out = []
    for tag in re.findall(r"<(?:path|circle|ellipse|line|polyline|rect)\b[^>]*>", body, re.S):
        sw = _SW.search(tag)
        if (float(sw.group(1)) if sw else _DEFAULT_WEIGHT) < STRUCT_WEIGHT:
            continue
        d = re.search(r'\bd="([^"]+)"', tag)
        if d:
            pts = _path_points(d.group(1))
            if pts:
                out.append((pts, d.group(1)[:40]))
            continue
        c = re.search(r'cx="([-0-9.]+)"\s*cy="([-0-9.]+)"\s*r="([0-9.]+)"', tag)
        if c:
            cx, cy, r = (float(v) for v in c.groups())
            out.append(([(cx + r * math.cos(t * math.pi / 6), cy + r * math.sin(t * math.pi / 6))
                         for t in range(12)], f"circle {cx},{cy} r{r}"))
    return out


def _reveal_last(ends, afters, drawin, min_step, panel_delay, has_color):
    """마지막 연출(SMIL·이름표) 종료 시각(ms). has_color가 참이면 이름표는 drawin이 아니라
    --reveal-end(= drawin + washSpan)에서 스태거된다 — tourSketches.jsx의 useLayoutEffect와
    같은 공식을 이식한다(judge()와 _check() 출력이 이 하나를 공유한다 — 판정 함수 이중화 금지)."""
    if has_color:
        label_count = len(afters)
        # index.css .scene-label-last 실제 종료식(revealEnd + label-i*250 + 400, label-i 최댓값은
        # labelCount-1)과 같은 식 — tourSketches.jsx의 labelRsv 수정(적대적 리뷰, 재검증)과 짝이다.
        label_rsv = ((label_count - 1) * 250 + _LABEL_FADE_MS) if label_count else 0
        budget = min_step - panel_delay  # tourSketches.jsx: Math.min(stepDuration(note), GLOBAL_MIN_STEP_MS) - 450
        wash_span = max(600, budget - drawin - label_rsv)
        reveal_end = drawin + wash_span
    else:
        reveal_end = drawin
    after_ends = [reveal_end + i * 250 + _LABEL_FADE_MS for i in afters]
    return max(ends + [drawin, reveal_end] + after_ends)


def judge(steps, begins, weights, ends, afters, dur_draw, panel_delay, min_step, body=None, has_color=False,
          cast_used=None, cast_registry=None):
    """B1~B12 판정 → 위반 메시지 목록(비었으면 통과). 검사와 대조군이 공유하는 유일한 판정.
    cast_registry/cast_used는 B12(정본 사용 강제) 입력 — 둘 다 없으면 B12는 건너뛴다(기존 호출부
    호환, 대부분의 selftest 대조군은 B12와 무관하다)."""
    bad = []
    total = sum(steps.values())
    if total < MIN_STROKES:
        bad.append(f"B1 밀도: stroke {total}개 < {MIN_STROKES}")
    over = {d: c for d, c in steps.items() if c > MAX_PER_STEP}
    if over:
        detail = ", ".join(f"{d}ms={c}선" for d, c in sorted(over.items()))
        bad.append(f"B2 단계 상한: 선 {MAX_PER_STEP}개 초과 단계 {len(over)}건 ({detail})")
    need = math.ceil(total / MAX_PER_STEP)
    if len(steps) < need:
        bad.append(f"B3 단계 하한: 단계 {len(steps)}개 < ceil({total}/{MAX_PER_STEP})={need}")
    drawin = (max(steps) if steps else 0) + dur_draw
    if drawin > MAX_DRAWIN_MS:
        bad.append(f"B4 시간 예산: 드로인 총 길이 {drawin}ms > {MAX_DRAWIN_MS}ms")
    early = [b for b in begins if b < drawin]
    if early:
        got = ", ".join(f"{b:.0f}ms" for b in sorted(early))
        bad.append(f"B5 절정 순서: 드로인 종료 {drawin}ms 전에 터지는 SMIL {len(early)}건 ({got})")
    if panel_delay + drawin > min_step:
        bad.append(
            f"B6 종속 관계: 패널 대기 {panel_delay}ms + 드로인 {drawin}ms "
            f"= {panel_delay + drawin}ms > min(stepDuration) {min_step}ms"
        )
    struct = sum(1 for w, _ in weights if w >= STRUCT_WEIGHT)
    if struct < MIN_STRUCT:
        bad.append(
            f"B7 구조 밀도: 굵기 {STRUCT_WEIGHT} 이상 선 {struct}개 < {MIN_STRUCT} — "
            "사람·사물의 구조를 그려라(배경 질감으로 개수를 채우지 말 것)"
        )
    faint = sum(1 for _, f in weights if f)
    if weights and faint / len(weights) > MAX_FAINT_RATIO:
        bad.append(
            f"B8 배경 상한: 반투명 획 {faint}/{len(weights)} "
            f"({faint * 100 // len(weights)}%) > {int(MAX_FAINT_RATIO * 100)}%"
        )
    if body is not None:
        labels = label_boxes(body)
        segs = stroke_segments(body)
        for txt, *lb in labels:
            pad = (lb[0] - LABEL_PAD, lb[1] - LABEL_PAD, lb[2] + LABEL_PAD, lb[3] + LABEL_PAD)
            if lb[0] < FRAME[0] or lb[1] < FRAME[1] or lb[2] > FRAME[2] or lb[3] > FRAME[3]:
                bad.append(
                    f"B10 배치 분리: 이름표 '{txt[:14]}' 상자가 프레임을 벗어난다 "
                    f"({lb[0]:.0f},{lb[1]:.0f}–{lb[2]:.0f},{lb[3]:.0f} / viewBox 120×64)")
            hit = [s for s in segs if _seg_hits_box(*s, pad)]
            if hit:
                bad.append(f"B10 배치 분리: 이름표 '{txt[:14]}'를 선 {len(hit)}개가 관통한다 — 글과 그림을 갈라 배치하라")
        for i, (t1, *a) in enumerate(labels):
            for t2, *b in labels[i + 1:]:
                if not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1]):
                    bad.append(f"B10 배치 분리: 이름표 '{t1[:10]}'와 '{t2[:10]}'가 겹친다")
    if body is not None:
        polys = structural_polylines(body)
        for i, (ps, src) in enumerate(polys):
            near = min((math.dist(p, q) for j, (qs, _) in enumerate(polys) if j != i
                        for p in ps for q in qs), default=0.0)
            if near > JOINT_GAP:
                bad.append(
                    f"B11 구조 연결: 구조 선이 {near:.1f}단위 떠 있다 (다른 부위와 {JOINT_GAP}단위 안에서 "
                    f"만나야 한다) — d=\"{src}\"")
    if body is not None and cast_registry:
        # B12 — 이름표가 있고 그 인물의 정본이 cast/에 있으면 정본을 써야 한다. 별칭은 정본
        # 파일의 aliases 선언에서 온다(아브람/아브라함처럼 이름표 여럿 → 정본 하나).
        # 한계(미결): 이름표 없이 그려진 인물은 기계 신호가 없어 이 검사 대상 밖이다.
        alias_to_name = {a: n for n, c in cast_registry.items() for a in c["aliases"]}
        for txt, *_ in label_boxes(body):
            name = alias_to_name.get(txt)
            if name and name not in (cast_used or set()):
                bad.append(
                    f"B12 정본 사용 강제: 이름표 '{txt}' 정본({name})이 cast/에 있는데 "
                    "이 장면이 정본 컴포넌트를 쓰지 않는다")
    last = _reveal_last(ends, afters, drawin, min_step, panel_delay, has_color)
    if panel_delay + last > min_step:
        bad.append(
            f"B9 연출 완료: 패널 대기 {panel_delay}ms + 마지막 연출 종료 {last:.0f}ms "
            f"= {panel_delay + last:.0f}ms > min(stepDuration) {min_step}ms — 절정이 step을 넘겨 잘린다"
        )
    return bad


def _scene_bodies(path):
    """모듈 소스 → {장면함수명: 본문}. 본문은 다음 최상위 정의 직전까지."""
    src = _read(path)
    marks = [(m.group(1), m.start()) for m in _SCENE_DEF.finditer(src)]
    ends = [m.start() for m in re.finditer(r"^(?:export\s+)?(?:function|const)\b", src, re.M)]
    out = {}
    for name, start in marks:
        nxt = [e for e in ends if e > start]
        out[name] = src[start: nxt[0] if nxt else len(src)]
    return out


def _all_scene_bodies():
    """전 스케치 파일의 {장면함수명: 본문}. **장면 정의가 레지스트리와 다른 파일에 있을 수 있다** —
    인트로 몽타주 5씬은 introMontage.jsx로 옮겨졌고(task#287) 원 모듈은 그것을 import해 쓴다.
    파일 안만 뒤지면 그런 장면이 **조용히 검사에서 빠진다**(레지스트리 23건 vs 파일 내 함수 22개)."""
    out = {}
    for path in sorted(glob.glob(os.path.join(_SKETCH_DIR, "*.jsx"))):
        rel = "frontend/src/sketches/" + os.path.basename(path)
        for name, body in _scene_bodies(rel).items():
            out.setdefault(name, body)
    return out


def _registry(mod):
    """모듈의 레지스트리 → [(정차지 키, 장면함수명, color 필드 존재 여부)]. 이 모듈이 무엇을
    렌더하는지의 정본. color(task#306 S4)가 있으면 그 장면은 드로인 뒤 wash가 끼어든다 —
    _reveal_last()의 has_color 입력이 이걸로 정해진다."""
    src = _read(f"frontend/src/sketches/{mod}")
    out = []
    for m in re.finditer(r"['\"](authored-[A-Za-z0-9-]+)['\"]\s*:\s*\{([^{}]*)\}", src):
        key, entry = m.group(1), m.group(2)
        fn = re.search(r"\bScene:\s*([A-Za-z0-9_]+)", entry)
        assert fn, f"{mod}: {key} 레지스트리 항목에 Scene:이 없다"
        out.append((key, fn.group(1), "color:" in entry))
    return out


def _resolve_targets():
    """TARGETS → [(표시이름, 본문, has_color)]. 모듈 통째 지정은 **레지스트리 기준**으로 열거한다 —
    파일 안 함수 목록으로 열거하면 다른 파일로 옮겨간 장면이 소리 없이 빠진다."""
    index = _all_scene_bodies()
    out = []
    for t in TARGETS:
        mod, _, scene = t.partition(":")
        assert os.path.exists(os.path.join(_ROOT, "frontend/src/sketches", mod)), f"대상 모듈 없음: {mod}"
        entries = _registry(mod)
        if scene:
            assert scene in index, f"{scene}의 정의를 어떤 스케치 파일에서도 찾지 못했다"
            has_color = any(fn == scene and c for _, fn, c in entries)
            out.append((t, index[scene], has_color))
        else:
            assert entries, f"{mod}에 레지스트리 항목이 없다"
            for key, fn, has_color in sorted(entries):
                assert fn in index, (
                    f"{mod}의 레지스트리가 가리키는 {fn}의 정의를 찾지 못했다 — "
                    "다른 파일로 옮겼다면 그 파일도 sketches/ 아래에 있어야 한다")
                out.append((f"{mod}:{fn}", index[fn], has_color))
    return out


def _check():
    dur_draw, panel_delay, min_step = _dur_draw_ms(), _panel_delay_ms(), _min_step_ms()
    js_floor = _global_min_step_ms_js()
    assert js_floor == min_step, (
        f"tourSketches.jsx의 GLOBAL_MIN_STEP_MS({js_floor}ms)가 실측 min(stepDuration)({min_step}ms)과 "
        "어긋났다 — data/tours/*.json의 최단 note가 바뀌었으면 그 상수도 같이 갱신하라"
    )
    registry = _cast_components()
    print(
        f"검사: 장면 저작 규약 B1~B12 (대상 {len(TARGETS)}엔트리 · 정본 {sorted(registry)} · "
        f"--dur-draw-scene {dur_draw}ms · 패널 대기 {panel_delay}ms · min(stepDuration) {min_step}ms)"
    )
    failures = []
    for label, body, has_color in _resolve_targets():
        expanded, used = expand_cast(body, registry)
        steps, begins, weights, ends, afters = scan_scene(expanded)
        bad = judge(steps, begins, weights, ends, afters, dur_draw, panel_delay, min_step, expanded, has_color,
                    cast_used=used, cast_registry=registry)
        drawin = (max(steps) if steps else 0) + dur_draw
        struct = sum(1 for w, _ in weights if w >= STRUCT_WEIGHT)
        faint = sum(1 for _, f in weights if f)
        mark = "✗" if bad else "✓"
        last = _reveal_last(ends, afters, drawin, min_step, panel_delay, has_color)
        tag = "(채색 포함)" if has_color else ""
        cast_tag = f" · 정본 사용 {sorted(used)}" if used else ""
        print(f"  {mark} {label} — {sum(steps.values())}선(구조 {struct} · 반투명 {faint}) · "
              f"{len(steps)}단계 · 드로인 {drawin}ms · 연출 종료 {last:.0f}ms{tag}{cast_tag}")
        for b in bad:
            print(f"      {b}")
        if bad:
            failures.append(label)
    assert not failures, "규약 경계 위반 장면: " + ", ".join(failures)
    print("PASS")


# ── 대조군 ───────────────────────────────────────────────────────────────────
def _synthetic(strokes, per_step, gap, begin_s=None, weight=2, faint_from=None):
    """지연 간격 gap으로 strokes개 선을 per_step씩 나눠 담은 합성 장면 소스.
    weight = sw() 굵기(B7 주입용) · faint_from = 이 인덱스부터 반투명(B8 주입용)."""
    parts, i, delay = [], 0, 0
    while i < strokes:
        n = min(per_step, strokes - i)
        lines = "".join(
            f'<path d="M0 0 h1" {{...sw({weight}, 0.5)}} />'
            if faint_from is not None and i + k >= faint_from
            else f'<path d="M0 0 h1" {{...sw({weight})}} />'
            for k in range(n))
        parts.append(f"<g style={{d({delay}, reduce)}}>{lines}</g>")
        i += n
        delay += gap
    if begin_s is not None:
        parts.append(f'<animateTransform begin="{begin_s}s" dur="0.5s" />')
    return "<g>" + "".join(parts) + "</g>"


def _selftest():
    dur_draw, panel_delay, min_step = _dur_draw_ms(), _panel_delay_ms(), _min_step_ms()
    js_floor = _global_min_step_ms_js()
    assert js_floor == min_step, (
        f"tourSketches.jsx의 GLOBAL_MIN_STEP_MS({js_floor}ms)가 실측 min(stepDuration)({min_step}ms)과 "
        "어긋났다 — data/tours/*.json의 최단 note가 바뀌었으면 그 상수도 같이 갱신하라"
    )
    print(f"  ✓ GLOBAL_MIN_STEP_MS 대조 → tourSketches.jsx({js_floor}ms) == min(stepDuration)({min_step}ms)")
    ok_body = _synthetic(36, 3, 450, begin_s=(450 * 11 + dur_draw) / 1000)
    ok = judge(*scan_scene(ok_body), dur_draw, panel_delay, min_step)
    assert not ok, f"대조군 기준선이 이미 빨강이다 — 합성 장면이 규약을 어긴다: {ok}"
    print(f"대조군 기준선: 합성 장면 36선/12단계 통과 (min(stepDuration) {min_step}ms)")

    # 각 경계를 개별로 위반하는 주입 — 같은 judge()가 그 경계를 지목해야 한다.
    # B4·B9의 gap·begin_s는 하드코딩 상수다(dur_draw·min_step처럼 소스에서 파생하지 않는다) —
    # task#303 S1로 MAX_DRAWIN_MS(10,000)·min(stepDuration)(12,360)이 올라가면서, 옛 값(700·8.0)은
    # 더 이상 새 경계를 넘기지 못해 대조군이 조용히 무의미해질 뻔했다. 여유를 두고 다시 골랐다:
    # B4는 11×900+500=10,400 > 10,000(마진 400ms), B9는 450+12,000+500=12,950 > 12,360(마진 590ms).
    cases = [
        ("B1", "밀도 미달(선 12개)", _synthetic(12, 3, 450), {}),
        ("B2", "한 단계에 선 6개", _synthetic(36, 6, 450), {}),
        ("B3", "단계 수 부족(선 36 / 단계 6)", _synthetic(36, 6, 450), {}),
        ("B4", "드로인 총 길이 초과", _synthetic(36, 3, 900), {}),
        ("B5", "절정이 드로인 종료 전", _synthetic(36, 3, 450, begin_s=0.5), {}),
        ("B6", "재생 step이 줄어 관계가 깨짐", ok_body, {"min_step": 1000}),
        ("B7", "전부 배경 굵기(구조 선 0개)", _synthetic(36, 3, 450, begin_s=6.0, weight=1.3), {}),
        ("B8", "반투명 획이 과반(20/36)", _synthetic(36, 3, 450, begin_s=6.0, faint_from=16), {}),
        # B5는 통과하되(절정이 드로인 뒤) B9만 위반하는 케이스 — 절정이 step을 넘겨 끝난다.
        ("B9", "절정이 step을 넘겨 종료", _synthetic(36, 3, 450, begin_s=12.0), {}),
        # after= 이름표(task#306 S2)가 drawin에서 파생한 종료 시각으로 B9를 위반시키는지.
        ("B9", "after= 이름표가 절정 종료를 늘림",
         ok_body + '<Label x="60" y="60" after={40} reduce={reduce}>연출</Label>', {}),
    ]
    for code, desc, body, over in cases:
        bad = judge(
            *scan_scene(body),
            dur_draw,
            panel_delay,
            over.get("min_step", min_step),
        )
        hit = [b for b in bad if b.startswith(code)]
        assert hit, f"{code} 위반({desc})을 주입했는데 검증기가 통과시켰다 — 게이트가 죽어있다"
        print(f"  ✓ {code} 위반 주입 → 검출: {hit[0]}")

    # has_color(task#306 S4, 적대적 리뷰로 드러난 구멍) — 라벨 5개로 label_rsv를 키우고 drawin을
    # B4 상한 바로 아래로 밀어 washSpan이 600ms 바닥에 걸리게 한다. has_color=False로 재면(수정 전
    # 게이트의 시야) 같은 body가 B9를 통과해 버려야 "이 축을 못 보고 있었다"는 게 재현된다.
    budget = min_step - panel_delay
    label_rsv5 = 4 * 250 + _LABEL_FADE_MS  # 라벨 5개 스태거 예약(labelCount-1=4)
    target_drawin = min(MAX_DRAWIN_MS - 20, budget - label_rsv5 - 550)  # 바닥(600ms) 안쪽으로 50ms
    gap = max(1, round((target_drawin - dur_draw) / 11))
    color_body = _synthetic(36, 3, gap) + "".join(
        f'<Label x="60" y="60" after={{{i}}} reduce={{reduce}}>연출{i}</Label>' for i in range(5)
    )
    color_bad = judge(*scan_scene(color_body), dur_draw, panel_delay, min_step, has_color=True)
    hit = [b for b in color_bad if b.startswith("B9")]
    assert hit, f"B9(색층 wash) 위반을 통과시켰다 — 게이트가 wash 축을 안 본다: {color_bad}"
    blind_bad = judge(*scan_scene(color_body), dur_draw, panel_delay, min_step)  # has_color=False(구 시야)
    assert not [b for b in blind_bad if b.startswith("B9")], (
        "대조 실패 — has_color=False로도 이미 B9 위반이면 wash 축을 분리해서 본 게 아니다"
    )
    print(f"  ✓ B9(색층 wash) 위반 주입 → 검출: {hit[0]} (has_color=False였다면 놓쳤을 위반)")

    # 파서 실명 대조군 — 아래 두 형태를 놓치면 지연을 0으로 오독해 게이트가 **조용히 거짓 초록**이
    # 된다. 실제로 그렇게 됐다(davidUnitedKingdom.jsx: 정적 2,700ms vs 브라우저 실측 6,000ms).
    # 경계 위반이 아니라 자(尺)가 눈먼 결함이므로 위 6케이스와 별도로 고정한다.
    tricky = (
        '<g>'
        '<g style={d(0, reduce)}><path d="M0 0 h1" /></g>'
        '<g style={d(reduce ? 0 : 5000, reduce)}><path d="M0 0 h1" /></g>'
        '<circle cx="1" cy="1" r="1" style={d(3500, false)} />'
        '</g>'
    )
    steps, _, _, _, _ = scan_scene(tricky)
    assert sorted(steps) == [0, 3500, 5000], (
        f"파서가 지연 형태를 놓쳤다 — 기대 [0, 3500, 5000], 실제 {sorted(steps)}. "
        "삼항 d(reduce ? 0 : N, reduce)와 stroke 요소 자체의 style={d(N, false)}를 읽어야 한다"
    )
    print("  ✓ 파서 실명 대조군 → 삼항 지연·stroke 직접 지연을 정확히 읽는다 (0/3500/5000ms)")

    # 열거 누락 대조군 — 모듈 통째 지정 시 **레지스트리 전건**이 대상이 되는지. 파일 안 함수 목록으로
    # 열거하면 다른 파일로 옮겨간 장면(introMontage의 인트로 5씬)이 조용히 빠진다(task#287이 만든 구멍).
    index = _all_scene_bodies()
    for mod in ("creationToFlood.jsx", "exodusToConquest.jsx", "davidUnitedKingdom.jsx",
                "gospelOfJesus.jsx", "theEarlyChurch.jsx"):
        entries = _registry(mod)
        infile = _scene_bodies("frontend/src/sketches/" + mod)
        moved = [fn for _, fn, _ in entries if fn not in infile]
        assert all(fn in index for _, fn, _ in entries), f"{mod}: 레지스트리가 가리키는 장면을 못 찾는다"
        if moved:
            print(f"  ✓ 열거 누락 대조군 → {mod}: 레지스트리 {len(entries)}건 중 파일 밖 정의 {moved} 를 전역 색인이 잡는다")
    # B10 — 이름표는 <Label> 컴포넌트라 합성 장면에 따로 붙인다. 세 결함을 각각 주입한다.
    base = '<g><g style={d(0, reduce)}><path d="M10 30 h100" {...sw(2)} /></g>'
    for desc, lab in [
        ("관통", '<Label x="60" y="32" reduce={reduce}>겹침</Label>'),
        ("프레임", '<Label x="118" y="50" reduce={reduce}>프레임밖</Label>'),
        ("이름표끼리", '<Label x="40" y="50" reduce={reduce}>가</Label><Label x="41" y="50" reduce={reduce}>나</Label>'),
    ]:
        body = base + lab + '</g>'
        bad = judge(*scan_scene(body), dur_draw, panel_delay, min_step, body)
        hit = [b for b in bad if b.startswith("B10")]
        assert hit, f"B10 {desc} 주입을 통과시켰다: {bad}"
        print(f"  ✓ B10 {desc} 주입 → {hit[0][:100]}")
    clean = base + '<Label x="60" y="6" reduce={reduce}>안겹침</Label></g>'
    assert not [b for b in judge(*scan_scene(clean), dur_draw, panel_delay, min_step, clean) if b.startswith("B10")], \
        "겹치지 않는 배치를 B10이 거짓 양성으로 잡는다"
    print("  ✓ B10 거짓 양성 없음 — 상단 띠에 둔 이름표는 통과한다")

    # B11 — 몸통에서 떨어진 머리를 주입한다. 얇은 배경 선은 원래 떨어져 있어도 정상이므로 함께 확인한다.
    torso = '<g><g style={d(0, reduce)}><path d="M40 50 v-14" {...sw(2.6)} /></g>'
    far = torso + '<g style={d(400, reduce)}><circle cx="40" cy="28" r="3" {...sw(2.6)} /></g></g>'
    hit = [b for b in judge(*scan_scene(far), dur_draw, panel_delay, min_step, far) if b.startswith("B11")]
    assert hit, "몸통에서 5단위 떠 있는 머리를 통과시켰다"
    print(f"  ✓ B11 떠 있는 부위 주입 → {hit[0][:96]}")
    near = torso + '<g style={d(400, reduce)}><circle cx="40" cy="33" r="3" {...sw(2.6)} /></g></g>'
    assert not [b for b in judge(*scan_scene(near), dur_draw, panel_delay, min_step, near) if b.startswith("B11")], \
        "붙어 있는 머리를 B11이 거짓 양성으로 잡는다"
    bg = torso + '<g style={d(400, reduce)}><path d="M5 10 q4 -2 8 0" {...sw(1.1, 0.4)} /></g></g>'
    assert not [b for b in judge(*scan_scene(bg), dur_draw, panel_delay, min_step, bg) if b.startswith("B11")], \
        "멀리 떨어진 얇은 배경 획을 B11이 잡는다 — 구조 선만 봐야 한다"
    print("  ✓ B11 거짓 양성 없음 — 붙은 부위와 멀리 떨어진 배경 획은 통과한다")

    # 정본 컴포넌트 인라인 전개 + B12(task#307 S3, ADR 260823-190821 3항) — 실제 cast/david.jsx를
    # 그대로 쓴다(가짜 정본을 새로 만들면 이 컴포넌트가 아니라 대조군 자체를 검증하게 된다.
    # "실제 소스는 건드리지 않는다"는 david.jsx를 읽기만 하고 쓰지 않는다는 뜻이다).
    registry = _cast_components()
    assert "David" in registry, "cast/david.jsx가 없다 — task#307 S2 산출물이 있어야 이 대조군을 돈다"

    # (a) 가장 중요한 대조군 — 전개 없이는 통과하지만 전개하면 위반하는 합성 장면. David의
    # delay=0 그룹은 실소스 그대로 stroke 3개(원 1 + 곱슬 2)다 — ok_body의 delay=0 그룹도 이미
    # 3개라 합치면 6개가 되어 B2(단계당 3개 상한)를 넘긴다. 전개 전엔 <David .../>가 미인식
    # 태그라 scan_scene이 무시하므로(path/circle/... 태그명만 본다) ok_body 기준선 그대로 통과한다.
    combo_raw = ok_body + '<David cx={0} cy={0} scale={1} delay={0} />'
    bad_before = judge(*scan_scene(combo_raw), dur_draw, panel_delay, min_step)
    assert not bad_before, f"대조군(a) 준비 실패 — 전개 없이 이미 빨강이다: {bad_before}"
    combo_expanded, combo_used = expand_cast(combo_raw, registry)
    assert combo_used == {"David"}, f"전개기가 David 호출을 인식하지 못했다: {combo_used}"
    bad_after = judge(*scan_scene(combo_expanded), dur_draw, panel_delay, min_step, combo_expanded)
    hit = [b for b in bad_after if b.startswith("B2") or b.startswith("B11")]
    assert hit, f"전개 후에도 위반이 검출되지 않았다 — 전개기가 stroke를 실제로 합치지 않는다: {bad_after}"
    print(f"  ✓ 대조군(a) 전개 없이 통과 → 전개 후 위반 검출(전개기가 stroke를 합친다는 증거): {hit[0]}")

    # (b) 표현식 prop — 호출부 규약(숫자 리터럴 4개만)을 어기면 전개기 자체가 실패해야 한다.
    expr_call = '<David cx={0+1} cy={0} scale={1} delay={0} />'
    try:
        expand_cast(expr_call, registry)
    except AssertionError as e:
        print(f"  ✓ 대조군(b) 표현식 prop 거부 → {e}")
    else:
        raise AssertionError("표현식 prop(cx={0+1})을 실패로 잡지 못했다 — 규약 위반 검사가 죽어있다")

    # (c) 정본이 있는데 안 쓴 이름표 장면 — B12.
    unwired = ok_body + f'<Label x="60" y="6" reduce={{reduce}}>{registry["David"]["aliases"][0]}</Label>'
    unwired_expanded, unwired_used = expand_cast(unwired, registry)
    assert unwired_used == set()
    bad_b12 = judge(*scan_scene(unwired_expanded), dur_draw, panel_delay, min_step, unwired_expanded,
                     cast_used=unwired_used, cast_registry=registry)
    hit = [b for b in bad_b12 if b.startswith("B12")]
    assert hit, f"정본 미사용 이름표 장면을 통과시켰다 — B12가 죽어있다: {bad_b12}"
    print(f"  ✓ 대조군(c) 정본 미사용 이름표 → B12 검출: {hit[0]}")

    # B12 거짓 양성 없음 — 정본을 실제로 쓰면 같은 이름표가 통과해야 한다. 델레이 6000은
    # ok_body(delay 0~4950)와 안 겹치게 골라 B2/B11 오염 없이 B12만 본다.
    wired = (ok_body + '<David cx={60} cy={30} scale={1} delay={6000} />'
             + f'<Label x="60" y="6" reduce={{reduce}}>{registry["David"]["aliases"][0]}</Label>')
    wired_expanded, wired_used = expand_cast(wired, registry)
    bad_wired = judge(*scan_scene(wired_expanded), dur_draw, panel_delay, min_step, wired_expanded,
                       cast_used=wired_used, cast_registry=registry)
    assert not [b for b in bad_wired if b.startswith("B12")], (
        f"정본을 실제로 쓴 장면을 B12가 거짓 양성으로 잡는다: {bad_wired}")
    print("  ✓ B12 거짓 양성 없음 — 정본을 쓴 장면은 통과한다")

    print(f"PASS — 경계 {len(cases) + 2}종(B1~B11) + B12/전개기 대조군 각각의 위반 주입에서 검증기가 빨강이 된다")


if __name__ == "__main__":
    (_selftest if "--selftest" in sys.argv else _check)()
