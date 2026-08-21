"""ERA_BANDS 시대 경계 정합 검증 — 7축 (task#255 S1 · task#284에서 3축 추가).

공유 설정이 없어 수동 복제된 시대 경계가 어긋나면 시대 분류·언약 리본이 조용히 깨진다.
task#284는 "만지면 기능이 **무음으로** 사라지는" 결합점 3축을 추가로 노출했다.

검사 대상:
  ① frontend/src/eraBands.js      : const ERA_BANDS = [{name, from}]  (task#271에 TimelineView.jsx에서 승급)
  ② backend/app/routes/stats.py   : ERA_BANDS = [(name, from)]
  ③ backend/app/curated.py        : ERA_ORDER = [name]  (순서만)
  ④ data/covenants/covenants.json : 각 언약 era ∈ 위 시대 이름 집합
  ⑤ data/tours/*.json             : 각 투어 era ∈ 시대 이름 집합 (task#284 — 저작자가 오타를 낼 수 있는 데이터 축)
  ⑥ frontend/src/PersonHub.jsx    : const ERA_ORDER 사본 == curated.py ERA_ORDER (이름·순서 모두)
  ⑦ frontend/src/**/*.{jsx,js}    : era 축 **기능 게이트**가 비교하는 문자열 리터럴 ∈ 시대 이름 집합

⑦이 왜 필요한가: `sec.era.name === '신약'`(TimelineView)과 `…?.era === '신약'`(ExploreStage)이
비유·기적 토글의 **유일한** 게이트다. 시대 이름을 바꾸면 토글이 어디서도 안 뜨고 **에러도 안 난다**.

⑦의 오탐 경계 — 파일 허용목록이 아니라 **클래스**로 좁혔다. `===` 바로 앞의 식별자 사슬 자체에
`era`/`Era` 토큰이 있어야 era 축으로 본다. 이 경계가 `BibleOverviewView.jsx`의 `t === '신약'`과
`StatsView.jsx`의 `['구약', '신약']`을 제외한다 — 그 둘은 **정경 구분**(OT/NT) 축이고 시대 축이
아니다(계획 3of3의 Non-goal). 주변 문맥에 era가 있는지로 판정하면 같은 파일의 무관한 비교
(`exploreView === 'map'`)까지 걸린다 — 실측으로 확인해 사슬 기준으로 좁혔다. 파일 목록으로
좁히지 않았으므로 **새 파일에 같은 게이트가 생기면 자동으로 검사 범위에 든다.**

각 축이 **몇 항목을 보았는지 출력에 찍고 0항목이면 실패**한다 — 0을 보고 통과하는 공허한 단언은
게이트가 아니다(ADR 260821-000937의 비공허 짝). ⑦이 0이 되는 경우는 게이트가 리팩터로 사라진
때인데, 그때는 통과가 아니라 **실패가 맞다**(리터럴 게이트를 없앴다면 이 축도 함께 갱신해야 한다).

정규식 스크래핑이라는 취약성은 ADR 260819-205242가 인정하고 남겨둔 결정이다. 포매팅 변화로
파싱이 깨지면 assert로 죽어 **배포를 막는다**(fail-closed — 안전 방향). 오탐이 나면 예외 목록을
두지 말고 불변식의 조건을 좁히고 그 근거를 여기에 남긴다.

--selftest는 인메모리 사본에 축마다 고의 드리프트를 주입해 모든 단언이 실제로 FAIL하는지
순회 확인한다. 기준선 PASS만으론 게이트가 살아있음을 증명하지 못한다(ADR 260820-003946).
"""
import glob
import json
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ⑦의 경계: `===` 직전 식별자 사슬에 era/Era 토큰이 있는 문자열 리터럴 비교.
_GATE_RE = re.compile(r"([A-Za-z_$][\w$?.\[\]]*(?:era|Era)[\w$?.\[\]]*)\s*\)?\s*===\s*'([^']+)'")


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as f:
        return f.read()


def _norm(v):
    v = v.strip()
    if "inf" in v.lower():  # -Infinity(JS) · float("-inf")(Py) · 정규식이 끊은 float("-inf" 모두 수용
        return float("-inf")
    return float(v)


def _timeline_bands():
    block = re.search(r"const ERA_BANDS = \[(.*?)\]", _read("frontend/src/eraBands.js"), re.S).group(1)
    return [(m.group(1), _norm(m.group(2)))
            for m in re.finditer(r"\{\s*name:\s*'([^']+)',\s*from:\s*([^,]+),", block)]


def _stats_bands():
    block = re.search(r"ERA_BANDS = \[(.*?)\]", _read("backend/app/routes/stats.py"), re.S).group(1)
    return [(m.group(1), _norm(m.group(2)))
            for m in re.finditer(r'\(\s*"([^"]+)",\s*([^)]+)\)', block)]


def _persons_order():
    block = re.search(r"ERA_ORDER = \[(.*?)\]", _read("backend/app/curated.py"), re.S).group(1)
    return re.findall(r'"([^"]+)"', block)


def _covenant_eras():
    data = json.loads(_read("data/covenants/covenants.json"))
    covs = data["covenants"] if isinstance(data, dict) else data
    return [c.get("era") for c in covs]


def _tour_eras():
    """⑤ [(파일명, era)] — data/tours/*.json."""
    out = []
    for path in sorted(glob.glob(os.path.join(_ROOT, "data/tours/*.json"))):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        out.append((os.path.basename(path), data.get("era")))
    return out


def _personhub_order():
    """⑥ PersonHub.jsx의 ERA_ORDER 사본 (이름·순서)."""
    m = re.search(r"const ERA_ORDER = \[(.*?)\]", _read("frontend/src/PersonHub.jsx"), re.S)
    assert m, "PersonHub.jsx에서 const ERA_ORDER 리스트 리터럴을 찾지 못함"
    return re.findall(r"'([^']+)'", m.group(1))


def _gate_literals():
    """⑦ [(상대경로, 줄번호, 좌변, 리터럴)] — era 축 기능 게이트가 비교하는 문자열."""
    out = []
    roots = ("frontend/src/**/*.jsx", "frontend/src/**/*.js")
    for pattern in roots:
        for path in sorted(glob.glob(os.path.join(_ROOT, pattern), recursive=True)):
            rel = os.path.relpath(path, _ROOT)
            src = open(path, encoding="utf-8").read()
            for m in _GATE_RE.finditer(src):
                out.append((rel, src[:m.start()].count("\n") + 1, m.group(1), m.group(2)))
    return out


def _load_all():
    return {
        "timeline": _timeline_bands(),
        "stats": _stats_bands(),
        "curated_order": _persons_order(),
        "covenant_eras": _covenant_eras(),
        "tour_eras": _tour_eras(),
        "personhub_order": _personhub_order(),
        "gate_literals": _gate_literals(),
    }


def _errors(d):
    """위반 메시지 목록. 빈 리스트 == 7축 전부 성립."""
    errs = []
    tl, st, po = d["timeline"], d["stats"], d["curated_order"]

    # ①② 파싱 자체가 비어 있으면 공허 통과 — 먼저 막는다
    if not tl:
        errs.append("eraBands.js ERA_BANDS 파싱 실패(0항목) — 포매팅이 바뀌었다")
    if not st:
        errs.append("stats.py ERA_BANDS 파싱 실패(0항목) — 포매팅이 바뀌었다")
    if errs:
        return errs

    if tl != st:
        errs.append(f"eraBands.js ↔ stats.py ERA_BANDS(이름·순서·경계) 불일치:\n    TL={tl}\n    ST={st}")
    names = [n for n, _ in tl]
    if names != po:
        errs.append(f"③ 시대 이름/순서 불일치: eraBands={names} vs curated.ERA_ORDER={po}")

    valid = set(names)

    # ④ 언약 era
    bad = [e for e in d["covenant_eras"] if e not in valid]
    if bad:
        errs.append(f"④ covenants.json era가 유효 시대 아님: {bad} (유효={sorted(valid)})")
    if not d["covenant_eras"]:
        errs.append("④ 언약이 0건 — covenants.json 구조가 바뀌었다(공허 통과 방지)")

    # ⑤ 투어 era
    for fname, era in d["tour_eras"]:
        if era not in valid:
            errs.append(f"⑤ data/tours/{fname}의 era가 유효 시대 아님: {era!r} (유효={sorted(valid)})")
    if not d["tour_eras"]:
        errs.append("⑤ 투어가 0건 — data/tours/*.json이 비었다(공허 통과 방지)")

    # ⑥ PersonHub 사본
    ph = d["personhub_order"]
    if not ph:
        errs.append("⑥ PersonHub.jsx ERA_ORDER가 0항목 — 포매팅이 바뀌었다(공허 통과 방지)")
    elif ph != po:
        errs.append(f"⑥ PersonHub.jsx ERA_ORDER 사본이 curated.py와 불일치(이름·순서):\n"
                    f"    PersonHub={ph}\n    curated  ={po}")

    # ⑦ 기능 게이트 리터럴
    for rel, line, lhs, lit in d["gate_literals"]:
        if lit not in valid:
            errs.append(f"⑦ {rel}:{line} era 기능 게이트가 없는 시대와 비교한다: "
                        f"{lhs} === {lit!r} (유효={sorted(valid)}) — 토글이 조용히 사라진다")
    if not d["gate_literals"]:
        errs.append("⑦ era 기능 게이트 비교가 0건 — 게이트가 리팩터로 사라졌다면 이 축도 함께 갱신할 것"
                    "(공허 통과 방지)")
    return errs


def _selftest():
    """7축 각각에 고의 드리프트를 인메모리로 주입해 FAIL하는지 순회 확인."""
    base = _load_all()
    assert not _errors(base), "기준선이 이미 FAIL이라 대조군을 돌릴 수 없다"
    n = 0

    def hurt(**over):
        return {**base, **over}

    # ① eraBands 경계 변조
    tl = list(base["timeline"])
    tl[1] = (tl[1][0], tl[1][1] + 999)
    assert _errors(hurt(timeline=tl)), "① 경계 변조 주입에도 통과했다"
    n += 1

    # ① eraBands 이름 변조 (stats와 갈라짐)
    tl = list(base["timeline"])
    tl[0] = ("없는시대", tl[0][1])
    assert _errors(hurt(timeline=tl)), "① 이름 변조 주입에도 통과했다"
    n += 1

    # ② stats 순서 바꿔치기
    st = list(base["stats"])
    st[0], st[1] = st[1], st[0]
    assert _errors(hurt(stats=st)), "② 순서 바꿔치기 주입에도 통과했다"
    n += 1

    # ③ curated.ERA_ORDER 이름 변조
    po = list(base["curated_order"])
    po[-1] = "신약시대"
    assert _errors(hurt(curated_order=po)), "③ curated 이름 변조 주입에도 통과했다"
    n += 1

    # ④ 언약 era 오타 / 0건
    assert _errors(hurt(covenant_eras=base["covenant_eras"] + ["없는시대"])), "④ 언약 era 오타 주입에도 통과했다"
    n += 1
    assert _errors(hurt(covenant_eras=[])), "④ 언약 0건에도 통과했다(공허)"
    n += 1

    # ⑤ 투어 era 오타 / 0건
    assert _errors(hurt(tour_eras=base["tour_eras"] + [("ghost.json", "없는시대")])), "⑤ 투어 era 오타 주입에도 통과했다"
    n += 1
    assert _errors(hurt(tour_eras=[])), "⑤ 투어 0건에도 통과했다(공허)"
    n += 1

    # ⑥ PersonHub 순서 바꿔치기 / 이름 변조 / 0항목
    ph = list(base["personhub_order"])
    ph[0], ph[1] = ph[1], ph[0]
    assert _errors(hurt(personhub_order=ph)), "⑥ PersonHub 순서 바꿔치기 주입에도 통과했다"
    n += 1
    ph = list(base["personhub_order"])
    ph[-1] = "신약시대"
    assert _errors(hurt(personhub_order=ph)), "⑥ PersonHub 이름 변조 주입에도 통과했다"
    n += 1
    assert _errors(hurt(personhub_order=[])), "⑥ PersonHub 0항목에도 통과했다(공허)"
    n += 1

    # ⑦ 기능 게이트 리터럴을 없는 시대 이름으로 / 0건
    gl = [(f, l, lhs, "신약시대") for f, l, lhs, _ in base["gate_literals"]]
    assert _errors(hurt(gate_literals=gl)), "⑦ 기능 게이트 리터럴 변조 주입에도 통과했다"
    n += 1
    assert _errors(hurt(gate_literals=[])), "⑦ 게이트 0건에도 통과했다(공허)"
    n += 1

    print(f"대조군: 고의 드리프트 {n}종(7축 전부 + 각 축의 공허 통과 4종) 전부 FAIL 확인")
    print("PASS")


def main():
    if "--selftest" in sys.argv:
        _selftest()
        return
    d = _load_all()
    errs = _errors(d)
    assert not errs, "시대(era) 결합점 정합 불일치:\n  " + "\n  ".join(errs)
    names = [n for n, _ in d["timeline"]]
    print(f"검사 7축: 시대 {len(names)}개 이름·순서·경계 3곳 일치 · "
          f"언약 era {len(d['covenant_eras'])}건 · 투어 era {len(d['tour_eras'])}건 · "
          f"PersonHub ERA_ORDER 사본 {len(d['personhub_order'])}항목 == curated · "
          f"era 기능 게이트 리터럴 {len(d['gate_literals'])}곳 전부 유효 시대")
    for rel, line, lhs, lit in d["gate_literals"]:
        print(f"    게이트 {rel}:{line}  {lhs} === {lit!r}")
    print("PASS")


if __name__ == "__main__":
    main()
