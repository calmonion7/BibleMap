"""theographic 원본 이벤트의 연대 이상을 검출한다 (task#158 S1).

검출 항목:
  a) 같은 인물의 출생<활동<사망 서사 역전 — "Birth/Death/Lifetime of X" 이벤트와
     그 인물의 HAS_PARTICIPANT 이벤트 연도 비교
  b) 사사 승계 순서(삿 10-12장 본문 순서) 역전
  c) 대표 앵커(출애굽/아브라함 소명/가뭄 선포) 대비 역전
  d) 교정 창(연도 -2200~-600) 안의 rec 접두 이벤트 전수 목록화
  e) 전치 오타 후보 — 같은 PART_OF 형제 그룹 내 ±150년 이상 고립 이탈
  + Person 스캔: birthYear/deathYear 보유 인물 중 사망<출생 또는 수명>1000년

화이트리스트(위반 아님): 신학적 참여(예수↔Creation of all things, 모세·엘리야↔변화산),
사망 이벤트 ±2년 포함셈, authored 이벤트 자체(교정 대상 아님, 비교 기준으로만 사용).

위반이 있으면 목록을 출력하고 종료 코드 1. --json PATH로 구조화 리포트도 저장한다.
"""
import argparse
import json
import os
import re
import sys

from neo4j import GraphDatabase

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
if not NEO4J_PASSWORD:
    raise RuntimeError("NEO4J_PASSWORD 환경변수가 설정되지 않았습니다")

# 교정 창 — 아브라함 출생 ~ 왕들 시대 (plan.md 충돌 구간)
CORRECTION_WINDOW = (-2200, -600)

DEATH_TOLERANCE_YEARS = 2
ISOLATED_OUTLIER_THRESHOLD_YEARS = 150

# (제목, "after"|"before", 앵커연도, 앵커설명) — ADR-0014 정본 연대계 대표 앵커
ANCHORS = [
    ("Death of Moses", "after", -1446, "출애굽(Exodus)"),
    ("Birth of Abraham", "before", -2091, "아브라함 소명(Call of Abraham in Ur)"),
    ("Elijah Translated", "after", -870, "가뭄 선포(Elijah declares the drought)"),
]

# 삿 10-12장 사사 승계 순서(본문 순서)
JUDGES_ORDER = [
    "Judgeship of Tola",
    "Judgeship of Jair",
    "Deliverance by Jephthah",
    "Judgeship of Ibzan",
    "Judgeship of Elon",
    "Judgeship of Abdon",
]

# 신학적 참여 화이트리스트 — (Person.name, Event.title) 쌍은 출생/사망 창 밖이어도 위반 아님
THEOLOGICAL_WHITELIST = {
    ("Jesus Christ", "Creation of all things"),
    # 변화산: dedupe(task#168)로 theographic 원본(오타 'The Transfiguation')이
    # authored-jesus-transfiguration('The Transfiguration')에 병합됨 — 병합 후 제목 기준
    ("Moses", "The Transfiguration"),
    ("Elijah", "The Transfiguration"),
}

BIO_EVENT_RE = re.compile(r"^(Birth|Death|Lifetime) of (.+)$")


def _year(s):
    """startDate 문자열(연도만/연-월/연-월-일, BC 음수 접두)에서 연도만 정수로 파싱한다.
    (nodes.py `_year`와 동일 규칙: 부호 분리 후 첫 파트 정수화)"""
    if not s:
        return None
    neg = s.startswith("-")
    body = s[1:] if neg else s
    try:
        y = int(body.split("-")[0])
    except ValueError:
        return None
    return -y if neg else y


def fetch_data(session):
    events = session.run(
        """
        MATCH (e:Event)
        RETURN e.theographic_id AS id, e.title AS title, e.startDate AS startDate,
               e.sortKey AS sortKey, e.nameKo AS nameKo, e.authored AS authored
        """
    ).data()
    persons = session.run(
        """
        MATCH (p:Person)
        RETURN p.theographic_id AS id, p.name AS name, p.nameKo AS nameKo,
               p.birthYear AS birthYear, p.deathYear AS deathYear
        """
    ).data()
    participation = session.run(
        """
        MATCH (ev:Event)-[:HAS_PARTICIPANT]->(p:Person)
        RETURN ev.theographic_id AS eventId, p.theographic_id AS personId
        """
    ).data()
    part_of = session.run(
        """
        MATCH (e:Event)-[:PART_OF]->(parent:Event)
        WHERE e.theographic_id STARTS WITH 'rec'
        RETURN parent.theographic_id AS parentId, parent.title AS parentTitle,
               e.theographic_id AS childId
        """
    ).data()
    return events, persons, participation, part_of


def check_person_bio_reversal(events, persons, participation):
    """(a) 같은 인물의 출생<활동<사망 서사 역전."""
    violations = []
    events_by_id = {e["id"]: e for e in events}
    persons_by_id = {p["id"]: p for p in persons}

    # 인물명 후보 -> {"Birth"/"Death"/"Lifetime": [(year, event)]}
    bio_by_name = {}
    for e in events:
        m = BIO_EVENT_RE.match(e["title"] or "")
        if not m:
            continue
        kind, name_part = m.group(1), m.group(2).split(",")[0].strip()
        year = _year(e["startDate"])
        if year is None:
            continue
        bio_by_name.setdefault(name_part, {}).setdefault(kind, []).append((year, e))

    # Person 매칭 인덱스: 이름 그대로 / 괄호주석 제거 기본명
    exact_name_to_persons, base_name_to_persons = {}, {}
    for p in persons:
        exact_name_to_persons.setdefault(p["name"], []).append(p)
        base = p["name"].split(" (")[0].strip() if p["name"] else None
        if base:
            base_name_to_persons.setdefault(base, []).append(p)

    def match_person(name_part):
        cands = exact_name_to_persons.get(name_part, [])
        if len(cands) == 1:
            return cands[0]
        cands2 = base_name_to_persons.get(name_part, [])
        if len(cands2) == 1:
            return cands2[0]
        uniq_ids = {c["id"] for c in cands + cands2}
        if len(uniq_ids) == 1:
            return (cands or cands2)[0]
        return None  # 모호하거나 매칭 안 됨 — 스킵

    # personId -> [(eventId, ...)]
    events_by_person = {}
    for row in participation:
        events_by_person.setdefault(row["personId"], []).append(row["eventId"])

    skipped_names = []
    for name_part, kinds in bio_by_name.items():
        person = match_person(name_part)
        if person is None:
            skipped_names.append(name_part)
            continue

        birth_years = [y for y, _ in kinds.get("Birth", [])]
        death_years = [y for y, _ in kinds.get("Death", [])]
        lifetime_years = [y for y, _ in kinds.get("Lifetime", [])]
        birth_year = min(birth_years) if birth_years else (min(lifetime_years) if lifetime_years else None)
        death_year = max(death_years) if death_years else None
        if birth_year is None and death_year is None:
            continue

        before_birth, after_death = [], []
        for ev_id in events_by_person.get(person["id"], []):
            ev = events_by_id.get(ev_id)
            if ev is None:
                continue
            if (person["name"], ev["title"]) in THEOLOGICAL_WHITELIST:
                continue
            y = _year(ev["startDate"])
            if y is None:
                continue
            if birth_year is not None and y < birth_year:
                before_birth.append((y, ev))
            if death_year is not None and y > death_year + DEATH_TOLERANCE_YEARS:
                after_death.append((y, ev))

        if before_birth:
            before_birth.sort(key=lambda t: t[0])
            worst_y, worst_ev = before_birth[0]
            violations.append({
                "person": name_part,
                "personId": person["id"],
                "personNameKo": person.get("nameKo"),
                "kind": "출생 이전 참여",
                "boundYear": birth_year,
                "count": len(before_birth),
                "worstEvent": {"id": worst_ev["id"], "title": worst_ev["title"], "startDate": worst_ev["startDate"], "year": worst_y},
                "detail": f"'{name_part}' 참여 이벤트 {len(before_birth)}건이 출생({birth_year})보다 앞섬 — 최악 사례 '{worst_ev['title']}'({worst_y})",
            })
        if after_death:
            after_death.sort(key=lambda t: -t[0])
            worst_y, worst_ev = after_death[0]
            violations.append({
                "person": name_part,
                "personId": person["id"],
                "personNameKo": person.get("nameKo"),
                "kind": "사망 이후 참여",
                "boundYear": death_year,
                "count": len(after_death),
                "worstEvent": {"id": worst_ev["id"], "title": worst_ev["title"], "startDate": worst_ev["startDate"], "year": worst_y},
                "detail": f"'{name_part}' 참여 이벤트 {len(after_death)}건이 사망({death_year}, ±{DEATH_TOLERANCE_YEARS}년 허용)보다 뒤임 — 최악 사례 '{worst_ev['title']}'({worst_y})",
            })

    return violations, skipped_names


def check_judges_succession(events):
    """(b) 사사 승계 순서(삿 10-12장) 역전."""
    by_title = {e["title"]: e for e in events}
    violations = []
    resolved = []
    for title in JUDGES_ORDER:
        ev = by_title.get(title)
        if ev is None:
            continue
        y = _year(ev["startDate"])
        resolved.append((title, ev, y))

    for i in range(len(resolved)):
        for j in range(i + 1, len(resolved)):
            title_i, ev_i, y_i = resolved[i]
            title_j, ev_j, y_j = resolved[j]
            if y_i is None or y_j is None:
                continue
            if y_i > y_j:
                violations.append({
                    "kind": "사사 승계 순서 역전",
                    "before": {"title": title_i, "id": ev_i["id"], "startDate": ev_i["startDate"], "year": y_i},
                    "after": {"title": title_j, "id": ev_j["id"], "startDate": ev_j["startDate"], "year": y_j},
                    "detail": f"'{title_i}'({y_i})가 본문상 '{title_j}'({y_j})보다 앞서야 하는데 연도가 뒤임",
                })
    return violations


def check_anchors(events):
    """(c) 대표 앵커 역전."""
    by_title = {e["title"]: e for e in events}
    violations = []
    for title, cmp_kind, anchor_year, anchor_label in ANCHORS:
        ev = by_title.get(title)
        if ev is None:
            continue
        y = _year(ev["startDate"])
        if y is None:
            continue
        if cmp_kind == "after" and y <= anchor_year:
            violations.append({
                "kind": "앵커 역전",
                "event": {"title": title, "id": ev["id"], "startDate": ev["startDate"], "year": y},
                "anchor": {"label": anchor_label, "year": anchor_year, "must": "after"},
                "detail": f"'{title}'({y})는 {anchor_label}({anchor_year})보다 뒤여야 하는데 그렇지 않음",
            })
        elif cmp_kind == "before" and y >= anchor_year:
            violations.append({
                "kind": "앵커 역전",
                "event": {"title": title, "id": ev["id"], "startDate": ev["startDate"], "year": y},
                "anchor": {"label": anchor_label, "year": anchor_year, "must": "before"},
                "detail": f"'{title}'({y})는 {anchor_label}({anchor_year})보다 앞서야 하는데 그렇지 않음",
            })
    return violations


def check_isolated_outliers(events, part_of):
    """(e) 전치 오타 후보 — 같은 PART_OF 형제 그룹 안에서 앞뒤 형제 모두와 ±150년 이상 떨어진
    고립 이벤트. 왕조처럼 형제군이 자연히 수백 년에 걸치더라도 인접 형제 간 간격은 좁으므로,
    (그룹 전체 대비가 아니라) 정렬된 형제열에서 바로 앞/뒤 이웃과의 간격만 본다.
    양끝(첫/마지막) 항목은 시대 경계상 간격이 벌어지는 게 정상이라 검사에서 제외한다."""
    events_by_id = {e["id"]: e for e in events}
    groups = {}
    for row in part_of:
        groups.setdefault(row["parentId"], {"title": row["parentTitle"], "children": []})["children"].append(row["childId"])

    violations = []
    for parent_id, g in groups.items():
        years = []
        for cid in g["children"]:
            ev = events_by_id.get(cid)
            if ev is None:
                continue
            y = _year(ev["startDate"])
            if y is not None:
                years.append((y, ev))
        if len(years) < 3:
            continue
        years.sort(key=lambda t: t[0])
        for i in range(1, len(years) - 1):
            y, ev = years[i]
            gap_prev = y - years[i - 1][0]
            gap_next = years[i + 1][0] - y
            if gap_prev >= ISOLATED_OUTLIER_THRESHOLD_YEARS and gap_next >= ISOLATED_OUTLIER_THRESHOLD_YEARS:
                violations.append({
                    "kind": "전치 오타 후보(형제군 고립 이탈)",
                    "event": {"title": ev["title"], "id": ev["id"], "startDate": ev["startDate"], "year": y},
                    "group": g["title"],
                    "neighborGapPrevYears": gap_prev,
                    "neighborGapNextYears": gap_next,
                    "detail": f"'{ev['title']}'({y})가 형제군 '{g['title']}'에서 앞({years[i-1][1]['title']}, {years[i-1][0]})·뒤({years[i+1][1]['title']}, {years[i+1][0]}) 이웃과 모두 {ISOLATED_OUTLIER_THRESHOLD_YEARS}년 이상 이탈",
                })
    return violations


def check_person_scan(persons):
    """Person 스캔: birthYear/deathYear 보유 인물 중 사망<출생 또는 수명>1000년."""
    violations = []
    for p in persons:
        b, d = _year(p.get("birthYear")), _year(p.get("deathYear"))
        if b is None or d is None:
            continue
        lifespan = d - b
        if d < b:
            violations.append({
                "kind": "출생/사망 역전",
                "person": p["name"], "personId": p["id"], "personNameKo": p.get("nameKo"),
                "birthYear": b, "deathYear": d,
                "detail": f"'{p['name']}' 사망({d})이 출생({b})보다 앞섬",
            })
        elif lifespan > 1000:
            violations.append({
                "kind": "수명 이상(>1000년)",
                "person": p["name"], "personId": p["id"], "personNameKo": p.get("nameKo"),
                "birthYear": b, "deathYear": d, "lifespan": lifespan,
                "detail": f"'{p['name']}' 수명 {lifespan}년(출생 {b} ~ 사망 {d}) — 성경 기록상 최장수(므두셀라 969년)보다 김",
            })
    return violations


def collect_rec_events_in_window(events):
    """(d) 교정 창 안의 rec 접두 이벤트 전수 목록화."""
    lo, hi = CORRECTION_WINDOW
    out = []
    for e in events:
        if not e["id"].startswith("rec"):
            continue
        y = _year(e["startDate"])
        if y is None or not (lo <= y <= hi):
            continue
        row = {"id": e["id"], "title": e["title"], "startDate": e["startDate"], "sortKey": e["sortKey"]}
        if e.get("nameKo"):
            row["nameKo"] = e["nameKo"]
        out.append(row)
    out.sort(key=lambda r: r["sortKey"] if r["sortKey"] is not None else 0)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", dest="json_path", default=None, help="구조화 리포트 저장 경로")
    args = parser.parse_args()

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        events, persons, participation, part_of = fetch_data(session)
    driver.close()

    bio_violations, skipped_names = check_person_bio_reversal(events, persons, participation)
    judges_violations = check_judges_succession(events)
    anchor_violations = check_anchors(events)
    outlier_violations = check_isolated_outliers(events, part_of)
    person_scan_violations = check_person_scan(persons)
    rec_events_in_window = collect_rec_events_in_window(events)

    total = len(bio_violations) + len(judges_violations) + len(anchor_violations) + len(outlier_violations) + len(person_scan_violations)

    print(f"[validate_event_chronology] 인물 출생/참여/사망 역전(a): {len(bio_violations)}건")
    for v in bio_violations:
        print(" -", v["detail"])
    print(f"[validate_event_chronology] 사사 승계 순서 역전(b): {len(judges_violations)}건")
    for v in judges_violations:
        print(" -", v["detail"])
    print(f"[validate_event_chronology] 앵커 역전(c): {len(anchor_violations)}건")
    for v in anchor_violations:
        print(" -", v["detail"])
    print(f"[validate_event_chronology] 전치 오타 후보(e): {len(outlier_violations)}건")
    for v in outlier_violations:
        print(" -", v["detail"])
    print(f"[validate_event_chronology] Person 스캔(사망<출생 또는 수명>1000년): {len(person_scan_violations)}건")
    for v in person_scan_violations:
        print(" -", v["detail"])
    print(f"[validate_event_chronology] 교정 창({CORRECTION_WINDOW[0]}~{CORRECTION_WINDOW[1]}) 내 rec 이벤트(d): {len(rec_events_in_window)}건")
    if skipped_names:
        print(f"[validate_event_chronology] 참고: 인물명 매칭 모호/실패로 (a) 검사에서 스킵된 이름 {len(skipped_names)}개: {skipped_names}")

    report = {
        "correctionWindow": list(CORRECTION_WINDOW),
        "violations": {
            "personBioReversal": bio_violations,
            "judgesSuccessionReversal": judges_violations,
            "anchorReversal": anchor_violations,
            "isolatedOutlierCandidate": outlier_violations,
        },
        "personScan": person_scan_violations,
        "recEventsInWindow": rec_events_in_window,
        "skippedNamesInBioCheck": skipped_names,
        "summary": {
            "totalViolations": total,
            "personBioReversalCount": len(bio_violations),
            "judgesSuccessionReversalCount": len(judges_violations),
            "anchorReversalCount": len(anchor_violations),
            "isolatedOutlierCandidateCount": len(outlier_violations),
            "personScanCount": len(person_scan_violations),
            "recEventsInWindowCount": len(rec_events_in_window),
        },
    }

    if args.json_path:
        os.makedirs(os.path.dirname(args.json_path), exist_ok=True)
        with open(args.json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"[validate_event_chronology] 구조화 리포트 저장: {args.json_path}")

    if total > 0:
        print(f"[validate_event_chronology] 위반 {total}건 (Person 스캔 포함)")
        sys.exit(1)
    print("[validate_event_chronology] OK — 위반 0")


if __name__ == "__main__":
    main()
