"""CURATED 테이블 ↔ 데이터 디렉터리 3종 정합 검증 (task#278 S4).

ADR 260820-003946이 "같은 결함 클래스가 최소 1건 남아 있다"고 지목한 그 결함을 게이트에
재현한다: `backend/app/curated.py`의 `CURATED`(35 slug)가 `data/person_events/*.json`과
갈라지면 무가드 조회가 조용히 `KeyError` → 500이 된다. 갈라짐은 양방향 모두 결함이다.

검사:
  - CURATED 키 집합 == data/person_events/*.json 파일 집합 (양방향 — 죽은 키·미커버 파일 둘 다 위반)
  - data/god_reliance/*.json의 slug ⊆ CURATED 키 집합
  - person_slugs/seal_slugs.json의 slug ∩ CURATED 키 집합 == ∅ (인장 상위집합이 큐레이션과 겹치면 중복)
  - 각 CURATED[slug]["era"] ∈ ERA_ORDER

CURATED/ERA_ORDER는 `ast.literal_eval`로 curated.py 소스에서 직접 뽑는다(import 부작용 0,
두 벌이 되지 않게 — 같은 ADR의 경계, validate_approx_book_verses.py와 동일 패턴).
CURATED가 리터럴이 아니게 리팩터되면 이 추출이 실패해 assert가 터진다 — fail-closed.

--selftest는 인메모리 사본에 고의 드리프트를 주입해 이 검사가 실제로 FAIL하는지 확인한다.
기준선 PASS만으론 게이트가 살아있음을 증명하지 못한다(ADR 260820-003946) — 그래서 4개 단언
전부(첫 단언은 양방향이라 두 번) 각각 주입해 순회한다.
"""
import ast
import json
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as f:
        return f.read()


def _curated_table():
    src = _read("backend/app/curated.py")
    m = re.search(r"^CURATED: dict\[str, dict\] = \{.*?^\}", src, re.S | re.M)
    assert m, "curated.py에서 CURATED 딕셔너리 리터럴을 찾지 못함"
    return ast.literal_eval(m.group(0).split("=", 1)[1].strip())


def _era_order():
    src = _read("backend/app/curated.py")
    m = re.search(r"^ERA_ORDER = \[.*?\]", src, re.S | re.M)
    assert m, "curated.py에서 ERA_ORDER 리스트 리터럴을 찾지 못함"
    return ast.literal_eval(m.group(0).split("=", 1)[1].strip())


def _json_slugs(rel_dir):
    d = os.path.join(_ROOT, rel_dir)
    return {os.path.splitext(f)[0] for f in os.listdir(d) if f.endswith(".json")}


def _seal_slugs():
    data = json.loads(_read("data/person_slugs/seal_slugs.json"))
    return {k for k in data if k != "note"}


def _errors(curated, era_order, pe_slugs, gr_slugs, seal_slugs):
    keys = set(curated.keys())
    errs = []
    for slug in sorted(keys - pe_slugs):
        errs.append(f"CURATED 죽은 키 — {slug} (data/person_events/{slug}.json 없음)")
    for slug in sorted(pe_slugs - keys):
        errs.append(f"미커버 파일 — data/person_events/{slug}.json 이 CURATED에 없음")
    for slug in sorted(gr_slugs - keys):
        errs.append(f"god_reliance 슬러그가 CURATED에 없음 — {slug}")
    for slug in sorted(seal_slugs & keys):
        errs.append(f"seal_slugs.json 슬러그가 CURATED와 겹침 — {slug}")
    for slug, v in sorted(curated.items()):
        if v.get("era") not in era_order:
            errs.append(f"CURATED[{slug}].era가 ERA_ORDER에 없음 — {v.get('era')!r}")
    return errs


def _load_all():
    return (
        _curated_table(),
        _era_order(),
        _json_slugs("data/person_events"),
        _json_slugs("data/god_reliance"),
        _seal_slugs(),
    )


def _selftest():
    """4개 단언(첫 단언은 양방향)을 각각 인메모리로 주입해 FAIL하는지 확인."""
    curated, era_order, pe, gr, seal = _load_all()
    assert not _errors(curated, era_order, pe, gr, seal), "기준선이 이미 FAIL이라 대조군을 돌릴 수 없다"
    n = 0

    # ①-a 죽은 키 — person_events 파일 없는 slug를 CURATED에 추가
    hurt = dict(curated)
    hurt["유령슬러그"] = {"nameKo": "유령", "era": era_order[0]}
    assert _errors(hurt, era_order, pe, gr, seal), "죽은 키 주입에도 검사가 통과했다"
    n += 1

    # ①-b 미커버 파일 — CURATED에 없는 slug를 person_events 집합에 추가
    hurt_pe = pe | {"미커버슬러그"}
    assert _errors(curated, era_order, hurt_pe, gr, seal), "미커버 파일 주입에도 검사가 통과했다"
    n += 1

    # ② god_reliance ⊆ CURATED — CURATED 밖 slug를 god_reliance 집합에 추가
    hurt_gr = gr | {"god_reliance이탈슬러그"}
    assert _errors(curated, era_order, pe, hurt_gr, seal), "god_reliance 이탈 주입에도 검사가 통과했다"
    n += 1

    # ③ seal_slugs ∩ CURATED == ∅ — CURATED 안 slug를 seal_slugs 집합에 추가
    any_slug = next(iter(curated))
    hurt_seal = seal | {any_slug}
    assert _errors(curated, era_order, pe, gr, hurt_seal), "seal_slugs 겹침 주입에도 검사가 통과했다"
    n += 1

    # ④ era ∈ ERA_ORDER — 임의 항목의 era를 무효값으로 변경
    hurt = dict(curated)
    hurt[any_slug] = dict(curated[any_slug])
    hurt[any_slug]["era"] = "존재하지않는시대"
    assert _errors(hurt, era_order, pe, gr, seal), "era 무효값 주입에도 검사가 통과했다"
    n += 1

    print(f"대조군: 고의 드리프트 {n}종(죽은 키·미커버 파일·god_reliance 이탈·seal_slugs 겹침·era 무효) 전부 FAIL 확인")
    print("PASS")


def main():
    if "--selftest" in sys.argv:
        _selftest()
        return
    curated, era_order, pe, gr, seal = _load_all()
    errs = _errors(curated, era_order, pe, gr, seal)
    assert not errs, "CURATED 정합 불일치:\n  " + "\n  ".join(errs)
    print(f"검사: CURATED {len(curated)}항목 ↔ person_events {len(pe)}파일 양방향 일치, "
          f"god_reliance {len(gr)}건 ⊆ CURATED, seal_slugs {len(seal)}건 ∩ CURATED = ∅, "
          f"era 전부 ERA_ORDER({len(era_order)}) 유효")
    print("PASS")


if __name__ == "__main__":
    main()
