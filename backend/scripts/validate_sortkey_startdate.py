"""통합 시간축의 sortKey↔startDate 역전 검증 (task#283 S3).

[[사건 연대 (startDate)]]는 "sortKey(서사 순서)가 정본이고 startDate는 그와 같은 이야기를
해야 한다"를 **글로 못 박았지만 자가 없었다.** task#264~266의 게이트는 "그 태스크에서 신규로
들어온 21건이 걸린 인접쌍만" 보았기 때문에 david.json 안의 2년 역전이 어느 자에도 안 걸렸다.
그 잔여를 닫는다. 실측 3건(교차파일 1 + 파일 내 2).

**불변식은 개수가 아니라 경계로 쓴다**(ADR 260821-000937):

    모든 인물 파일의 저작 사건을 sortKey로 **전역** 정렬했을 때 인접쌍의 startDate 역전이 0곳

**전역·교차파일로 본다.** CONTEXT.md가 "통합 시간축"이라고 규정한 그 범위이며, 파일 단위로
좁히면 moses→joshua 경계의 역전(모세의 죽음 -1406 뒤에 여호수아 소명 -1407)이 **무음 통과**한다.
알려진 3건을 열거하지 않고 클래스 자체를 판정하므로 새로 들어온 역전도 걸린다.

**sortKey 동값 쌍은 판정에서 제외한다.** 순서가 데이터로 정해지지 않은 쌍에 역전을 물으면
어느 쪽으로 놓아도 위반이 되어 고칠 수 없는 빨강이 된다(ADR 260821-000937의 거짓 빨강).
제외 건수는 출력에 찍어 침묵하지 않는다.

**연도 파싱: 기존 파서를 재사용하지 않고 형식을 단언한다.** 계획은 재사용을 지시했으나
실측이 그것을 기각했다 — 기존 파서 3벌(`validate_event_chronology._year`·`load_books._parse_year`·
`nodes.py` 내부 `_year`)은 전부 **import 시점에 `NEO4J_PASSWORD`를 요구하는 모듈**에 살고,
`scripts/check.sh`의 파일 검증 루프는 `.env`를 읽기 **전에** 돌기 때문에 import 자체가 터진다.
즉 재사용하면 이 검증기는 항상 FAIL이고, 파일만 읽어 판정한다는 이 축의 설계(라이브 DB 비결합)도
깨진다. 그래서 관대한 파싱 대신 **"person_events의 startDate는 부호 있는 정수 문자열"을 단언**한다 —
월/일 정밀도가 들어오면 조용히 절삭하지 않고 터진다(fail-closed). 파서 3벌의 소거는 별건이다.

**둘째 축 — 표시 라벨도 같은 이야기를 해야 한다.** `TimelineView`는 저작 사건에서 startDate가
아니라 `yearLabel`을 그대로 표시한다(`isAuthored && rep.yearLabel ? rep.yearLabel : parseYear(...)`).
따라서 정렬만 고치고 라벨을 놔두면 **정렬은 초록인데 화면은 옛 연도**를 보여준다(실측: 여호수아
소명이 startDate -1407인데 라벨은 이미 'BC 1406경'이었고, 작별·죽음은 라벨만 선행 사건에서 복사돼
'BC 1380경'인데 startDate -1379였다). 그래서 두 번째 불변식을 같이 세운다:

    단일 연도를 가리키는 yearLabel(BC N / AD N, 접미 '경' 허용)의 연도 == startDate
    범위 라벨(BC N–N / AD N–N)이면 startDate가 그 범위 안

시대 단위 근사 라벨(`태초 무렵 (전통 BC 4000경)`)은 **여러 사건이 의도적으로 공유**하고 startDate가
그 안에서 순서를 벌리는 값이므로 제외한다 — 위반으로 세면 정상 데이터가 빨강이 된다. 제외는
id 목록이 아니라 **라벨 형태**로 좁히고 제외 건수를 출력에 찍는다(침묵하지 않는다).

--selftest는 인메모리 사본에 고의 드리프트를 주입해 이 검사가 실제로 FAIL하는지 확인한다.
기준선 PASS만으론 게이트가 살아있음을 증명하지 못한다(ADR 260820-003946).
"""
import glob
import json
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PERSON_EVENTS_GLOB = "data/person_events/*.json"
_INT_RE = re.compile(r"^-?\d+$")
# 단일연도 라벨: "BC 1406경" · "BC 1406" · "AD 33경"   /   범위 라벨: "BC 1897–1884경" · "AD 62–64"
_LABEL_SINGLE = re.compile(r"^(BC|AD)\s*(\d+)\s*경?$")
_LABEL_RANGE = re.compile(r"^(BC|AD)\s*(\d+)\s*[–-]\s*(\d+)\s*경?$")


def _label_errors(flat):
    """yearLabel↔startDate 축의 위반 목록 + (단일연도, 범위, 제외) 건수."""
    errs, single, ranged, skipped = [], 0, 0, 0
    for e in flat:
        yl = (e.get("yearLabel") or "").strip()
        m = _LABEL_SINGLE.match(yl)
        if m:
            single += 1
            year = -int(m.group(2)) if m.group(1) == "BC" else int(m.group(2))
            if year != e["sd"]:
                errs.append(f"{e['file']}/{e['id']}: yearLabel {yl!r}(연도 {year})가 "
                            f"startDate {e['sd']}와 다른 이야기를 한다 — 화면에는 라벨이 뜬다")
            continue
        m = _LABEL_RANGE.match(yl)
        if m:
            ranged += 1
            a, b = int(m.group(2)), int(m.group(3))
            lo, hi = sorted(((-a, -b) if m.group(1) == "BC" else (a, b)))
            if not lo <= e["sd"] <= hi:
                errs.append(f"{e['file']}/{e['id']}: startDate {e['sd']}가 범위 라벨 "
                            f"{yl!r}({lo}..{hi}) 밖")
            continue
        skipped += 1  # 시대 단위 근사·비수치 라벨 — 형태로 제외
    return errs, single, ranged, skipped


def _load_by_file():
    """{slug: [event, ...]} — 파일 경계를 유지해 읽는다(주입 대조군이 교차파일을 만들 수 있게)."""
    out = {}
    for path in sorted(glob.glob(os.path.join(_ROOT, PERSON_EVENTS_GLOB))):
        slug = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as f:
            out[slug] = json.load(f)
    return out


def _errors(by_file):
    """위반 메시지 목록. 빈 리스트 == 불변식 성립."""
    errs = []
    flat = []
    for slug in sorted(by_file):
        for ev in by_file[slug]:
            eid = ev.get("id")
            sd = ev.get("startDate")
            sk = ev.get("sortKey")
            if not isinstance(sd, str) or not _INT_RE.match(sd):
                errs.append(f"{slug}/{eid}: startDate가 부호 있는 정수 문자열이 아님 — {sd!r} "
                            f"(월/일 정밀도는 조용히 절삭하지 않고 여기서 막는다)")
                continue
            if not isinstance(sk, (int, float)) or isinstance(sk, bool):
                errs.append(f"{slug}/{eid}: sortKey가 수가 아님 — {sk!r}")
                continue
            flat.append({"id": eid, "file": slug, "sd": int(sd), "sk": sk,
                         "yearLabel": ev.get("yearLabel")})

    if errs:
        return errs  # 형식이 깨진 채로 정렬 판정을 하면 결과가 무의미하다

    # 비공허 짝(ADR 260821-000937) — 0건을 보고 통과하는 공허한 단언을 막는다.
    if not flat:
        errs.append(f"검사 대상 저작 사건이 0건 — {PERSON_EVENTS_GLOB}가 비었거나 구조가 바뀌었다(공허 통과 방지)")
        return errs

    flat.sort(key=lambda e: (e["sk"], e["id"]))
    for a, b in zip(flat, flat[1:]):
        if a["sk"] == b["sk"]:
            continue  # 순서 미정 쌍 — 판정 제외
        if a["sd"] > b["sd"]:
            cross = " [교차파일]" if a["file"] != b["file"] else ""
            errs.append(
                f"{a['sd'] - b['sd']}년 역전{cross} — {a['id']}({a['file']}, sortKey={a['sk']}, "
                f"startDate={a['sd']}) 뒤에 {b['id']}({b['file']}, sortKey={b['sk']}, startDate={b['sd']})"
            )

    label_errs, single, _, _ = _label_errors(flat)
    errs.extend(label_errs)
    # 라벨 축의 비공허 짝 — 단일연도 라벨을 0건 보고 통과하면 라벨 형식이 바뀐 것이다.
    if single == 0:
        errs.append("단일연도 yearLabel을 가진 사건이 0건 — 라벨 형식이 바뀌었다(공허 통과 방지)")
    return errs


def _counts(by_file):
    flat = [(ev.get("sortKey"), ev.get("id")) for evs in by_file.values() for ev in evs]
    ties = 0
    ordered = sorted(flat, key=lambda x: (x[0], x[1]))
    for a, b in zip(ordered, ordered[1:]):
        if a[0] == b[0]:
            ties += 1
    return len(flat), len(by_file), ties


def _selftest():
    """단언 4종 + 비공허 짝을 각각 인메모리로 주입해 FAIL하는지 순회 확인."""
    base = _load_by_file()
    assert not _errors(base), "기준선이 이미 FAIL이라 대조군을 돌릴 수 없다"
    n = 0

    def _copy():
        return {slug: [dict(ev) for ev in evs] for slug, evs in base.items()}

    # 전역 sortKey 정렬에서 인접한 쌍을 실제로 찾아 그 쌍에 주입한다(가짜 인접 회피).
    flat = sorted(
        ({"slug": s, "i": i, "sk": ev["sortKey"], "sd": int(ev["startDate"]), "id": ev["id"]}
         for s, evs in base.items() for i, ev in enumerate(evs)),
        key=lambda e: (e["sk"], e["id"]),
    )
    same_pair = next((a, b) for a, b in zip(flat, flat[1:]) if a["slug"] == b["slug"] and a["sk"] != b["sk"])
    cross_pair = next((a, b) for a, b in zip(flat, flat[1:]) if a["slug"] != b["slug"] and a["sk"] != b["sk"])

    # ① 파일 내 역전 — 선행 사건의 startDate를 후행보다 늦게 만든다
    a, b = same_pair
    hurt = _copy()
    hurt[a["slug"]][a["i"]]["startDate"] = str(b["sd"] + 5)
    assert _errors(hurt), "파일 내 역전 주입에도 검사가 통과했다"
    n += 1

    # ② 교차파일 역전 — 파일 단위로 좁힌 검사가 무음 통과하는 그 축
    a, b = cross_pair
    hurt = _copy()
    hurt[a["slug"]][a["i"]]["startDate"] = str(b["sd"] + 5)
    errs = _errors(hurt)
    assert errs, "교차파일 역전 주입에도 검사가 통과했다"
    assert any("[교차파일]" in e for e in errs), "교차파일 역전을 교차파일로 지목하지 못했다"
    n += 1

    # ③ startDate 형식 위반 — 월/일 정밀도를 조용히 절삭하지 않는다(fail-closed)
    hurt = _copy()
    hurt[a["slug"]][a["i"]]["startDate"] = "-1451-01"
    assert _errors(hurt), "월/일 정밀도 startDate에도 검사가 통과했다"
    n += 1

    # ④ sortKey 형식 위반 — 수가 아닌 값
    hurt = _copy()
    hurt[a["slug"]][a["i"]]["sortKey"] = "앞쪽"
    assert _errors(hurt), "sortKey 비수치 주입에도 검사가 통과했다"
    n += 1

    # ⑤ 단일연도 라벨 드리프트 — 정렬은 그대로인데 표시 연도만 어긋난 경우
    single_target = next(
        (e for e in flat if _LABEL_SINGLE.match((base[e["slug"]][e["i"]].get("yearLabel") or "").strip())),
        None,
    )
    assert single_target, "단일연도 라벨을 가진 사건이 없어 라벨 대조군을 구성할 수 없다"
    hurt = _copy()
    st = single_target
    hurt[st["slug"]][st["i"]]["yearLabel"] = f"BC {abs(st['sd']) + 7}경"
    errs = _errors(hurt)
    assert errs, "yearLabel 드리프트 주입에도 검사가 통과했다"
    assert any("다른 이야기를 한다" in e for e in errs), "라벨 드리프트를 라벨 축으로 지목하지 못했다"
    n += 1

    # ⑥ 범위 라벨 이탈 — startDate가 라벨 범위 밖으로 나간 경우
    hurt = _copy()
    hurt[st["slug"]][st["i"]]["yearLabel"] = f"BC {abs(st['sd']) + 30}–{abs(st['sd']) + 20}경"
    assert _errors(hurt), "범위 라벨 이탈 주입에도 검사가 통과했다"
    n += 1

    # ⑦ 라벨 축 비공허 짝 — 단일연도 라벨을 전부 시대근사로 바꾸면 통과가 아니라 실패여야 한다
    hurt = _copy()
    for slug in hurt:
        for ev in hurt[slug]:
            ev["yearLabel"] = "홍수 이전"
    assert _errors(hurt), "단일연도 라벨 0건에도 검사가 통과했다(라벨 축 공허 통과)"
    n += 1

    # ⑧ 비공허 짝 — 대상이 0건이면 통과가 아니라 실패여야 한다
    assert _errors({}), "사건 0건에도 검사가 통과했다(공허 통과)"
    n += 1

    print(f"대조군: 고의 드리프트 {n}종(파일 내 역전·교차파일 역전·startDate 형식·sortKey 형식·"
          f"라벨 드리프트·범위 라벨 이탈·라벨 0건·사건 0건) 전부 FAIL 확인")
    print("PASS")


def main():
    if "--selftest" in sys.argv:
        _selftest()
        return
    by_file = _load_by_file()
    errs = _errors(by_file)
    assert not errs, "통합 시간축 sortKey↔startDate 역전:\n  " + "\n  ".join(errs)
    n_ev, n_files, ties = _counts(by_file)
    flat = [{"id": ev["id"], "file": slug, "sd": int(ev["startDate"]), "sk": ev["sortKey"],
             "yearLabel": ev.get("yearLabel")} for slug, evs in by_file.items() for ev in evs]
    _, single, ranged, skipped = _label_errors(flat)
    print(f"검사: 인물 파일 {n_files}개의 저작 사건 {n_ev}건을 sortKey로 전역 정렬 — "
          f"인접쌍 startDate 역전 0곳 (sortKey 동값으로 판정 제외한 쌍 {ties}개), "
          f"yearLabel 단일연도 {single}건 == startDate · 범위 {ranged}건 포함 · "
          f"시대근사·비수치 {skipped}건 형태로 제외")
    print("PASS")


if __name__ == "__main__":
    main()
