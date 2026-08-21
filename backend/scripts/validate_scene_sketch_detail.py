"""장면 스케치 저작 규약 경계 B1~B6 검증 (task#286 S4 — 파일럿).

투어 정차지 장면 스케치의 밀도가 중앙 10선에 그쳐 "그려지는" 연출이 한 박에 끝나 버렸다.
task#286이 목표 밀도(35~40선)와 붓질 단계 경계를 규약으로 확정했고, 이 검증기가 그것을 강제한다.
규약 정본은 `frontend/src/sketches/lib.jsx`의 "장면 저작 규약" 절이다.

  B1 밀도       장면당 stroke >= 30
  B2 단계 상한  어떤 붓질 단계(= 같은 지연값)도 선 3개 초과 금지
  B3 단계 하한  단계 수 >= ceil(선 수 / 3)
  B4 시간 예산  드로인 총 길이(= max(지연) + --dur-draw) <= 7,000ms
  B5 절정 순서  그 장면의 모든 SMIL begin >= 드로인 종료 시각
  B6 종속 관계  패널 대기(450ms) + 드로인 총 길이 <= min(stepDuration)
  B7 구조 밀도  굵기 >= 2.0인 stroke >= 12개 (사람·사물의 구조)
  B8 배경 상한  반투명(opacity < 1) stroke가 전체의 40% 이하
  B9 연출 완료  패널 대기 + 마지막 연출(SMIL·이름표) **종료** 시각 <= min(stepDuration)
  B10 배치 분리 이름표(글) 상자에 어떤 stroke도 들어오지 않고, 상자가 프레임 안에 있다
  B11 구조 연결 구조 선(굵기 >= 2.0)은 다른 구조 선과 2.0단위 안에서 만난다 — 부위가 떠 있지 않다

**경계를 이 파일에 박지 않는다 — 실제 소스에서 파생한다.** `--dur-draw`는 `index.css`,
패널 대기는 `tourSketches.jsx`, `stepDuration` 공식은 `useTourPlayback.js`, note 길이는
`data/tours/*.json`에서 읽는다. 상수를 복사해 두면 누가 타이밍을 바꿨을 때 게이트가 조용히
거짓 초록이 된다(불변식은 개수가 아니라 경계다 — ADR 260821-000937).

**단계는 `<g>` 개수가 아니라 지연값으로 센다.** 같은 지연을 가진 `<g>`를 여러 개로 쪼개도
관객에겐 한 박에 우수수 나타나는 것과 같기 때문이다 — 그렇게 세면 B2/B3가 게임된다.

--selftest는 각 경계를 **개별로** 위반하는 합성 장면을 **같은 판정 함수**에 주입해 6건 모두
빨강이 되는지 확인한다. 기준선 PASS만으론 게이트가 살아있음을 증명하지 못한다
(ADR 260820-003946). 실제 소스는 건드리지 않는다.
B6은 B4(7,000ms)보다 느슨해 장면을 늘리는 방식으로는 단독 위반을 만들 수 없다 —
그래서 대조군은 재생 쪽 레버(min(stepDuration))를 줄여 관계가 깨지는 것을 확인한다.
"""
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
]

MIN_STROKES = 30           # B1
MAX_PER_STEP = 3           # B2
MAX_DRAWIN_MS = 7000       # B4
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

_DUR = re.compile(r'\bdur\s*=\s*"([^"]+)"')
_LABEL_AT = re.compile(r'<Label[^>]*\bat="([0-9.]+)"')
_LABEL_FADE_MS = 400
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


def _dur_draw_ms():
    m = re.search(r"--dur-draw:\s*(\d+)ms", _read("frontend/src/index.css"))
    assert m, "index.css에서 --dur-draw를 찾지 못했다 — 타이밍 모델이 바뀌었다면 이 검증기도 갱신하라"
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
    """장면 본문 → (지연별 stroke 수, SMIL begin(ms), [(굵기, 반투명)], 연출 종료 시각(ms))."""
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
    return steps, begins, weights, ends


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
    for tag in re.findall(r"<(?:path|circle|ellipse|line|polyline|rect)\b[^>]*>", body, re.S):
        sw = _SW.search(tag)
        half = (float(sw.group(1)) if sw else _DEFAULT_WEIGHT) * 0.55 / 2
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


def judge(steps, begins, weights, ends, dur_draw, panel_delay, min_step, body=None):
    """B1~B6 판정 → 위반 메시지 목록(비었으면 통과). 검사와 대조군이 공유하는 유일한 판정."""
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
    last = max(ends + [drawin])
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
    """모듈의 레지스트리 → [(정차지 키, 장면함수명)]. 이 모듈이 무엇을 렌더하는지의 정본."""
    src = _read(f"frontend/src/sketches/{mod}")
    return re.findall(r"['\"](authored-[A-Za-z0-9-]+)['\"]\s*:\s*\{\s*Scene:\s*([A-Za-z0-9_]+)", src)


def _resolve_targets():
    """TARGETS → [(표시이름, 본문)]. 모듈 통째 지정은 **레지스트리 기준**으로 열거한다 —
    파일 안 함수 목록으로 열거하면 다른 파일로 옮겨간 장면이 소리 없이 빠진다."""
    index = _all_scene_bodies()
    out = []
    for t in TARGETS:
        mod, _, scene = t.partition(":")
        assert os.path.exists(os.path.join(_ROOT, "frontend/src/sketches", mod)), f"대상 모듈 없음: {mod}"
        if scene:
            assert scene in index, f"{scene}의 정의를 어떤 스케치 파일에서도 찾지 못했다"
            out.append((t, index[scene]))
        else:
            entries = _registry(mod)
            assert entries, f"{mod}에 레지스트리 항목이 없다"
            for key, fn in sorted(entries):
                assert fn in index, (
                    f"{mod}의 레지스트리가 가리키는 {fn}의 정의를 찾지 못했다 — "
                    "다른 파일로 옮겼다면 그 파일도 sketches/ 아래에 있어야 한다")
                out.append((f"{mod}:{fn}", index[fn]))
    return out


def _check():
    dur_draw, panel_delay, min_step = _dur_draw_ms(), _panel_delay_ms(), _min_step_ms()
    print(
        f"검사: 장면 저작 규약 B1~B11 (대상 {len(TARGETS)}엔트리 · "
        f"--dur-draw {dur_draw}ms · 패널 대기 {panel_delay}ms · min(stepDuration) {min_step}ms)"
    )
    failures = []
    for label, body in _resolve_targets():
        steps, begins, weights, ends = scan_scene(body)
        bad = judge(steps, begins, weights, ends, dur_draw, panel_delay, min_step, body)
        drawin = (max(steps) if steps else 0) + dur_draw
        struct = sum(1 for w, _ in weights if w >= STRUCT_WEIGHT)
        faint = sum(1 for _, f in weights if f)
        mark = "✗" if bad else "✓"
        last = max(ends + [drawin])
        print(f"  {mark} {label} — {sum(steps.values())}선(구조 {struct} · 반투명 {faint}) · "
              f"{len(steps)}단계 · 드로인 {drawin}ms · 연출 종료 {last:.0f}ms")
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
    ok_body = _synthetic(36, 3, 450, begin_s=(450 * 11 + dur_draw) / 1000)
    ok = judge(*scan_scene(ok_body), dur_draw, panel_delay, min_step)
    assert not ok, f"대조군 기준선이 이미 빨강이다 — 합성 장면이 규약을 어긴다: {ok}"
    print(f"대조군 기준선: 합성 장면 36선/12단계 통과 (min(stepDuration) {min_step}ms)")

    # 각 경계를 개별로 위반하는 주입 — 같은 judge()가 그 경계를 지목해야 한다.
    cases = [
        ("B1", "밀도 미달(선 12개)", _synthetic(12, 3, 450), {}),
        ("B2", "한 단계에 선 6개", _synthetic(36, 6, 450), {}),
        ("B3", "단계 수 부족(선 36 / 단계 6)", _synthetic(36, 6, 450), {}),
        ("B4", "드로인 총 길이 초과", _synthetic(36, 3, 700), {}),
        ("B5", "절정이 드로인 종료 전", _synthetic(36, 3, 450, begin_s=0.5), {}),
        ("B6", "재생 step이 줄어 관계가 깨짐", ok_body, {"min_step": 1000}),
        ("B7", "전부 배경 굵기(구조 선 0개)", _synthetic(36, 3, 450, begin_s=6.0, weight=1.3), {}),
        ("B8", "반투명 획이 과반(20/36)", _synthetic(36, 3, 450, begin_s=6.0, faint_from=16), {}),
        # B5는 통과하되(절정이 드로인 뒤) B9만 위반하는 케이스 — 절정이 step을 넘겨 끝난다.
        ("B9", "절정이 step을 넘겨 종료", _synthetic(36, 3, 450, begin_s=8.0), {}),
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
    steps, _, _, _ = scan_scene(tricky)
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
        moved = [fn for _, fn in entries if fn not in infile]
        assert all(fn in index for _, fn in entries), f"{mod}: 레지스트리가 가리키는 장면을 못 찾는다"
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
    print(f"PASS — 경계 {len(cases) + 2}종(B1~B11) 각각의 위반 주입에서 검증기가 빨강이 된다")


if __name__ == "__main__":
    (_selftest if "--selftest" in sys.argv else _check)()
