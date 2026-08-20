"""ERA_BANDS 시대 경계 3(+1)곳 정합 검증 (task#255 S1).

공유 설정이 없어 수동 복제된 시대 경계가 어긋나면 시대 분류·언약 리본이 조용히 깨진다.
검사 대상:
  - frontend/src/eraBands.js      : const ERA_BANDS = [{name, from}]  (task#271에 TimelineView.jsx에서 승급)
  - backend/app/routes/stats.py   : ERA_BANDS = [(name, from)]
  - backend/app/curated.py        : ERA_ORDER = [name]  (순서만)
  - data/covenants/covenants.json : 각 언약 era ∈ 위 시대 이름 집합
이름·순서·경계(from)가 세 곳에서 일치하고, 언약 era가 유효 시대인지 단언한다.
"""
import json
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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


def main():
    tl, st, po = _timeline_bands(), _stats_bands(), _persons_order()
    assert tl, "eraBands.js ERA_BANDS 파싱 실패"
    assert st, "stats.py ERA_BANDS 파싱 실패"
    assert tl == st, f"eraBands.js ↔ stats.py ERA_BANDS(이름·순서·경계) 불일치:\n  TL={tl}\n  ST={st}"
    names = [n for n, _ in tl]
    assert names == po, f"시대 이름/순서 불일치: eraBands={names} vs curated.ERA_ORDER={po}"
    valid = set(names)
    bad = [e for e in _covenant_eras() if e not in valid]
    assert not bad, f"covenants.json era가 유효 시대 아님: {bad} (유효={sorted(valid)})"
    print(f"검사: 시대 {len(names)}개 이름·순서·경계 3곳 일치, 언약 era {len(_covenant_eras())}건 전부 유효")
    print("PASS")


if __name__ == "__main__":
    main()
