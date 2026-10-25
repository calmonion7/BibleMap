"""task 408 — 크기 기준표(scale.json) 읽개. 가이드 그림·명세 검사·판정 문항이 크기 숫자를 여기서만 읽는다(규칙 derive.scale-table).

  import scale as S; S.height_rel("tall") → 1.205 · S.cm(6, "cubit") → 267.0 · S.fill("키의 {{1/[body.head]|1}}분의 1") → "키의 7.5분의 1"
  task 409: S.crowd_stage(36) → ("large", (0.35, 0.5)) · S.scene_horizon(spec) → 눈높이 지평선 y · S.screen_height(발 y, 지평선, 키 등급)
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "scale.json")
WHY = re.compile(r"^\[(직접|추론)\]|^\[저작\]\([^)]+\)")
_T = None


def table():
    global _T
    if _T is None:
        with open(PATH, encoding="utf-8") as fh:
            _T = json.load(fh)
    return _T


def v(path):
    """점 경로(body.head · height.tall · figures.david-youth.0) → 값. 잎 {"v": …}는 값으로 푼다."""
    node = table()
    for k in path.split("."):
        if isinstance(node, dict) and "v" in node and k not in node:
            node = node["v"]
        node = node[int(k)] if isinstance(node, list) else node[k]
    return node["v"] if isinstance(node, dict) and "v" in node else node


def height_rel(cls):
    return v(f"height.{cls}")


def head_ratio(age):
    return v(f"age_head.{age}") if age in table()["age_head"] else v("body.head")


def build_width(cls=None):
    """체격 등급 몸 너비 — 등급이 없거나 모르면 average."""
    return v(f"build_width.{cls}") if cls in table()["build_width"] else v("build_width.average")


def guide_head_r():
    """가이드 꼴 머리 반지름(구역 높이 비) — {person, person_duck}."""
    return {"person": v("guide.head_r_person"), "person_duck": v("guide.head_r_duck")}


def cm(n, unit):
    """규빗·뼘·손바닥 수 → cm."""
    return n * v({"cubit": "unit.cubit_cm", "span": "unit.span_cm", "handbreadth": "unit.handbreadth_cm"}[unit])


def ref(name):
    """지물 크기 기준 길이(사전 look.size.ref) — 어른 남자 키 비."""
    return v(f"refs.{name}")


def crowd_stage(n):
    """task 409 — 장면 사람 수 → (무리 단계 이름, (초점 화면 키 하한, 위 한도))."""
    for name, node in table()["crowd_stage"].items():
        if name.startswith("_"):
            continue
        st = node["v"]
        if st["max"] is None or n <= st["max"]:
            return name, tuple(st["focus_h"])
    raise ValueError(f"[Scale] 무리 단계에 위 끝 없는 단계가 없다: {n}")


def people_count(spec):
    """장면 사람 수 = figures 수 + crowds[].count(본문 근거 — 칸이 없으면 0으로 셈)."""
    return len(spec.get("figures") or []) + sum(c.get("count", 0) for c in spec.get("crowds") or [])


def horizon(foot_y, screen_h, height_rel=1.0):
    """눈높이 카메라 지평선 y(화면 높이 비, 위 = 0) — 초점 인물 발 y·화면 키·키 등급에서."""
    return foot_y - v("perspective.eye") * screen_h / height_rel


def screen_height(foot_y, hy, height_rel=1.0):
    """발 y에 서 있는 사람의 화면 키 — (발 y − 지평선) ÷ 눈높이 비 × 키 등급."""
    return (foot_y - hy) / v("perspective.eye") * height_rel


SEATED_SHAPES = {"sit"}   # 앉은 한 사람 꼴(make_guide) — 배 안 머리·어깨 줄(seated)은 무리 꼴이라 뺌


def _figures(spec, pick):
    import derive_scene as ds   # 늦은 읽기 — derive_scene 쪽 무거운 읽기를 표만 쓰는 곳에 끌어오지 않게
    g = spec.get("guide") or {}
    sh, pose = g.get("shape", {}), g.get("pose", {})
    out = []
    for f in spec.get("figures") or []:
        k = f["region"]
        if pick(str(sh.get(k, "")), k in pose):
            cls = ds._cast_in_scene(f).get("card", {}).get("heightRel")
            out.append((k, height_rel(cls) if cls in table()["height"] else height_rel("average")))
    return out


def standing(spec):
    """가이드 사람 꼴(person*)·뼈대로 그리는 figures → [(구역 이름, 카드 키 등급 값)]. 꿇음·엎드림·앉음 꼴은 빠짐."""
    return _figures(spec, lambda shape, posed: shape.startswith("person") or posed)


def seated(spec):
    """가이드 앉은 꼴(SEATED_SHAPES)로 그리는 figures → [(구역 이름, 카드 키 등급 값)]."""
    return _figures(spec, lambda shape, posed: shape in SEATED_SHAPES)


def scene_horizon(spec):
    """장면 지평선 — 화면 키가 가장 큰(가장 가까운) 서 있는 인물이 초점. 서 있는 인물이 없으면 앉은 인물 중 가장 큰 이의
    서 있을 때 키(구역 높이 ÷ body.seated)로(task 416 — 홀로 앉은 밧세바), 그도 없으면 표 기본값."""
    R = spec.get("regions", {})
    people = standing(spec)
    if people:
        k, hr = max(people, key=lambda p: R[p[0]][3] - R[p[0]][1])
        return horizon(R[k][3], R[k][3] - R[k][1], hr)
    sat = seated(spec)
    if sat:
        k, hr = max(sat, key=lambda p: R[p[0]][3] - R[p[0]][1])
        return horizon(R[k][3], (R[k][3] - R[k][1]) / v("body.seated"), hr)
    return v("perspective.horizon_default")


def _lexicon():
    with open(os.path.join(HERE, "..", "..", "data", "scripture_words", "words.json"), encoding="utf-8") as fh:
        return {w["id"]: w for w in json.load(fh)["words"]}


FILL = re.compile(r"\{\{(.+?)(?:\|(\d))?\}\}")
NAME = re.compile(r"\[([^\]]+)\]")


def fill(text):
    """판정 문항 자리표 {{식|소수 자리}}를 표·사전 값으로 채운다. 식 안 [점 경로]는 표 값, [w.<사전 id>.<경로>]는 낱말 사전 값.
    문항 글에 숫자를 손으로 쓰지 않으려고(task 408 S4) — 표 값을 바꾸면 문항 글 숫자도 바뀐다."""
    words = {}

    def val(m):
        p = m.group(1)
        if p.startswith("w."):
            if not words:
                words.update(_lexicon())
            wid, rest = p[2:].split(".", 1)
            node = words[wid]
            for k in rest.split("."):
                node = node[k]
            return repr(float(node))
        return repr(float(v(p)))

    def one(m):
        expr = NAME.sub(val, m.group(1))
        if not re.fullmatch(r"[0-9.eE+\-*/() ]+", expr):
            raise ValueError(f"[Scale] 자리표 식이 숫자 식이 아니다: {m.group(0)}")
        x = round(eval(expr, {"__builtins__": {}}), int(m.group(2) or 1))   # noqa: S307 — 위에서 숫자·연산자만 허용
        return f"{x:g}"
    return FILL.sub(one, text)


def why_errors():
    """값마다 근거 단계 — 잎 {"v": …}에 _why가 [직접]·[추론]·[저작](이유)로 시작해야 한다."""
    out = []

    def walk(node, path):
        if isinstance(node, dict) and "v" in node:
            if not WHY.match(node.get("_why") or ""):
                out.append(f"{path}: _why 근거 단계 머리말 없음")
            return
        if isinstance(node, dict):
            for k, x in node.items():
                if not k.startswith("_"):
                    walk(x, f"{path}.{k}" if path else k)
    walk(table(), "")
    return out


LITERAL = r"^({names})\b[^=\n]*=\s*[-0-9.{{(]"


def literal_errors(files=("batch/make_guide.py", "recheck.py")):
    """크기 숫자는 표에서만(규칙 derive.scale-table) — 지킴 이름(_guarded)이 코드에서 숫자·사전 리터럴로 다시 정해지면 걸림."""
    pat = re.compile(LITERAL.format(names="|".join(table()["_guarded"])), re.M)
    out = []
    for f in files:
        with open(os.path.join(HERE, f), encoding="utf-8") as fh:
            src = fh.read()
        out += [f"{f}: 「{m.group(0).strip()}」 — 크기 숫자를 코드에 다시 씀(scale.json에서 읽을 것)" for m in pat.finditer(src)]
    return out
