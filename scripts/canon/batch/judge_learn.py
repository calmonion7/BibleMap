#!/usr/bin/env python3
"""판정 학습 — 사람 라벨이 쌓일수록 판정자가 사람 기준을 배우고, 믿을 만해진 문항 종류는 사람에게서 덜어 낸다.

  python3 batch/judge_learn.py rules <과제>      # 그 과제 앞까지 배운 규칙집 보기
  python3 batch/judge_learn.py curve             # 시간 순서 평가: 과제마다 J1 기본 vs 규칙집(그 과제 앞까지만 배움)
  python3 batch/judge_learn.py trust             # 문항 종류별 믿음 관문(Wilson 95% 하한) — 사람에게서 덜어 낼 종류
  python3 batch/judge_learn.py cand <과제> [--count]   # 후보 화면 규칙(장면마다 후보·되돌림·표본) — --count는 만든 화면 수
  python3 batch/judge_learn.py candjudge <과제>        # 사람 답 기록 뒤: 후보 화면 `판정:` 줄(세 규칙)

원장 = 사람이 판정한 과제의 라벨(TASK_ORDER 순서, judge_items.TASKS의 페이지·metrics) + 그 과제에 대한 J1 답.
규칙집은 **그 과제보다 앞선 과제**의 사람 메모와 「기계·사람이 2장 이상 엇갈린 칸」으로만 만든다(처음 보는 라벨로 재기 —
notes/JUDGE-ITEMS.md 「판정 학습」 고정 절). 새 과제는 TASKS·TASK_ORDER·J1_RUNS에 한 줄씩 더하면 원장에 들어온다."""
import json, math, os, sys, zlib
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import judge_items as J

TASK_ORDER = tuple(sorted(J.TASKS))   # 사람이 판정한 과제가 judge_items.TASKS에 등록되면 원장에 들어온다
# 과제 → (묶음, J1 전 문항 run, J1 지물 run) — 학습 전 기준 판정자의 답
J1_RUNS = {368: ("dev", "r2", "p2-sonnet"), 369: ("dev", "r2", "p2-sonnet"),
           370: ("holdout", "sonnet", "p2-sonnet"), 372: ("holdout", "sonnet", "p2-sonnet")}
# 과제 → (묶음, 학습판 전 문항 run, 학습판 지물 run) — 규칙집(그 과제 앞까지)을 붙인 J1 = L1
L1_RUNS = {369: ("dev", "L1", "L1-prop"), 370: ("holdout", "L1", "L1-prop"), 372: ("holdout", "L1", "L1-prop")}
MIN_DISAGREE = 2      # 기계·사람이 이만큼 이상 엇갈린 칸만 규칙으로
OTHER_SCENE_CAP = 3   # 다른 장면에서 가져오는 같은 종류 규칙 수
TRUST_LB = 0.8        # 믿음 관문: 잡기·통과의 Wilson 95% 하한이 둘 다 이 값 이상
TRUST_MIN_WRONG = 20  # 그리고 사람 「틀림」 라벨이 이만큼 이상


def memos(task):
    d = J.TASKS[task][0]
    m = json.load(open(os.path.join(J.HERE, "samples", d, "metrics.json")))
    return {(sid, q): v["memo"] for sid, sc in m["scenes"].items() for q, v in sc.get("items", {}).items() if v.get("memo")}


def runs_of(m, task):
    """과제의 J1 답이 있는 곳 — 새 과제는 함께 판정 화면 전에 `judge_items.py predict`가 m["t<과제>"]에 쓴다."""
    return J1_RUNS.get(task) or (f"t{task}", "J1", "J1-prop")


def j1_answer(m, task, key, qid, runs=None):
    s, base, prop = (runs or {}).get(task) or runs_of(m, task)
    rec = m[s][prop if J.cls(qid) == "prop" else base]["answers"].get(key) or {}
    return (rec.get("answers") or {}).get(qid), (rec.get("reasons") or {}).get(qid, "")


def cells(task, m):
    """→ {(장면, 문항): 칸} — 과제 한 칸(장면 × 문항)의 사람 틀림 수·기계 엇갈림·사람 메모·기대 문장."""
    out, mm = {}, memos(task)
    for it in J.items(None, tasks=[task]):
        for qid, lab in it["labels"].items():
            c = out.setdefault((it["scene"], qid), {"task": task, "title": it["title"], "scene": it["scene"], "qid": qid,
                                                    "what": next(q["what"] for q in it["qs"] if q["id"] == qid), "n": 0, "wrong": 0,
                                                    "miss": [], "false": [], "memo": mm.get((it["scene"], qid), "")})
            pred, why = j1_answer(m, task, it["key"], qid)
            c["n"] += 1
            c["wrong"] += lab == "틀림"
            if pred and pred != lab:
                (c["miss"] if lab == "틀림" else c["false"]).append(why)
    return out


def rule_text(c):
    s = f"- [{c['title']} · {c['qid']}] 기대 「{c['what']}」 — 사람은 {c['n']}장 중 {c['wrong']}장을 틀림으로 봄"
    if c["memo"]:
        s += f" · 사람 메모 「{c['memo']}」"
    if len(c["miss"]) >= MIN_DISAGREE:
        s += f" · 기계는 그중 {len(c['miss'])}장을 맞음으로 놓침(기계 이유 예: 「{c['miss'][0][:80]}」) → 이런 그림은 틀림"
    if len(c["false"]) >= MIN_DISAGREE:
        s += f" · 기계는 사람이 맞다고 본 {len(c['false'])}장을 틀림으로 봄(기계 이유 예: 「{c['false'][0][:80]}」) → 이 정도는 맞음"
    return s


def rulebook(task, m=None):
    """→ [칸] — task보다 앞선 과제에서 배운 것: 사람 메모가 있거나 기계·사람이 MIN_DISAGREE 이상 엇갈린 칸."""
    m = m or J.load()
    prior = TASK_ORDER[:TASK_ORDER.index(task)]
    return [c for t in prior for c in cells(t, m).values()
            if c["memo"] or len(c["miss"]) >= MIN_DISAGREE or len(c["false"]) >= MIN_DISAGREE]


def rules_for(it, classes, book, other=OTHER_SCENE_CAP):
    """그림 한 장에 붙일 규칙: 같은 장면은 그 문항 종류 전부, 다른 장면은 같은 종류에서 OTHER_SCENE_CAP개."""
    same = [c for c in book if c["scene"] == it["scene"] and J.cls(c["qid"]) in classes]
    others = defaultdict(list)
    for c in book:
        if c["scene"] != it["scene"] and J.cls(c["qid"]) in classes:
            others[J.cls(c["qid"])].append(c)
    picked = same + [c for k in sorted(others) for c in sorted(others[k], key=lambda c: -(len(c["miss"]) + len(c["false"]) + bool(c["memo"])))[:other]]
    if not picked:
        return ""
    return ("\n\n이전 사람 판정에서 배운 기준(같은 장면이면 그대로, 다른 장면이면 같은 종류 문항의 눈높이로 참고):\n"
            + "\n".join(rule_text(c) for c in picked))


def wilson_lb(k, n, z=1.96):
    if not n:
        return 0.0
    p = k / n
    return (p + z * z / (2 * n) - z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n)


def trust(m=None, learned=None):
    """→ {종류: {catch, pass, lb, trusted}} — 원장 전체(과제마다 그 시점 판정자의 답 = learned가 있으면 학습판)."""
    m = m or J.load()
    acc = defaultdict(lambda: {"틀림": [0, 0], "맞음": [0, 0]})
    for task in TASK_ORDER:
        for it in J.items(None, tasks=[task]):
            for qid, lab in it["labels"].items():
                if qid in it["premarked"]:   # 기계 표시를 보고 고친 칸 — 닻 효과로 평가에서 뺀다(블라인드 칸만 잰다)
                    continue
                pred = (learned or {}).get((it["key"], qid)) or j1_answer(m, task, it["key"], qid)[0]
                a = acc[J.cls(qid)][lab]
                a[0] += pred == lab
                a[1] += 1
    out = {}
    for c in J.CLASSES:
        if c not in acc:
            continue
        w, r = acc[c]["틀림"], acc[c]["맞음"]
        lb = (wilson_lb(*w), wilson_lb(*r))
        out[c] = {"catch": f"{w[0]}/{w[1]}", "pass": f"{r[0]}/{r[1]}", "lb": [round(x, 3) for x in lb],
                  "trusted": w[1] >= TRUST_MIN_WRONG and min(lb) >= TRUST_LB}
    return out


def curve(m=None):
    """→ [(과제, 판정자, 잡기 k/n, 통과 k/n, 종류별)] — 과제마다 J1 기본 vs L1(그 과제 앞까지 배운 규칙집)."""
    m = m or J.load()
    rows, tot = [], {"J1": [[0, 0], [0, 0]], "L1": [[0, 0], [0, 0]]}
    for task in TASK_ORDER:
        if task not in L1_RUNS:
            continue
        for name, runs in (("J1", J1_RUNS), ("L1", L1_RUNS)):
            hit = {"틀림": [0, 0], "맞음": [0, 0]}
            by = defaultdict(lambda: {"틀림": [0, 0], "맞음": [0, 0]})
            for it in J.items(None, tasks=[task]):
                for qid, lab in it["labels"].items():
                    if qid in it["premarked"]:
                        continue
                    pred = j1_answer(m, task, it["key"], qid, runs)[0]
                    for h in (hit[lab], by[J.cls(qid)][lab]):
                        h[0] += pred == lab
                        h[1] += 1
            rows.append((task, name, hit["틀림"], hit["맞음"], {c: (v["틀림"], v["맞음"]) for c, v in by.items()}))
            for i, lab in enumerate(("틀림", "맞음")):
                tot[name][i][0] += hit[lab][0]
                tot[name][i][1] += hit[lab][1]
    return rows, tot


def machine_marks(task, m=None):
    """→ ({장면: {문항: [기계가 틀렸다고 본 시드]}}, {장면: 되돌림 후보?}) — 함께 판정 화면에 미리 표시할 J1 답.
    되돌림 후보 = 장면 뜻(moment)을 기계가 시드 전부 틀렸다고 봄(notes 「판정 학습」 — 368~372에서 「없음」 5개 중 3 · 잘못 0/8, 다음 묶음에서 확인)."""
    m = m or J.load()
    marks, seeds = defaultdict(lambda: defaultdict(list)), defaultdict(set)
    for it in J.items(None, tasks=[task]):
        seeds[it["scene"]].add(it["seed"])
        for qid in it["qids"]:
            if j1_answer(m, task, it["key"], qid)[0] == "틀림":
                marks[it["scene"]][qid].append(it["seed"])
    reject = {sid: len(marks[sid].get("moment", [])) == len(seeds[sid]) for sid in seeds}
    return {sid: dict(q) for sid, q in marks.items()}, reject


def sample_order(sid, seeds):
    """블라인드 표본 순서 — 장면 id와 시드로만 정해진다(J1 답과 무관, 재현됨)."""
    return sorted(seeds, key=lambda s: zlib.crc32(f"{sid}:{s}".encode()))


def pick_candidates(answers, oddity=None):
    """후보 화면 규칙(notes/VERSE-REGEN.md 고정 절). answers = {장면: {시드: {문항: "맞음"|"틀림"|None}}} (시드는 시드 목록 순서)
    → {장면: {cand, sample, reject, wrong}} — 답 없음(None)은 틀림으로 센다.
    후보 = 장면 뜻(moment) 맞음인 시드 중 틀림 칸이 가장 적은 시드(동률이면 앞쪽) · 되돌림 = moment가 시드 전부 틀림 · 표본 = 표본 순서에서 후보 아닌 첫 시드.
    oddity = {장면: {시드: "맞음"|"틀림"|None}}(이상한 점 판정자, 「틀림」 = 있음 · 답 없음은 있음으로) — 주면 후보는 「장면 뜻 맞음 그리고
    이상한 점 없음」 시드에서만 고르고, 되돌림 사유(reason: 장면 뜻 | 이상한 점)를 붙인다(task 378 S6). 안 주면 376 규칙 그대로."""
    out = {}
    for sid, by in answers.items():
        wrong = {s: sum(a != "맞음" for a in qa.values()) for s, qa in by.items()}
        ok = [s for s, qa in by.items() if qa.get("moment") == "맞음"]
        pool = ok if oddity is None else [s for s in ok if (oddity.get(sid) or {}).get(s) == "맞음"]
        cand = min(pool, key=lambda s: wrong[s]) if pool else None   # min은 동률에서 앞쪽 시드
        sample = None if cand is None else next(s for s in sample_order(sid, list(by)) if s != cand)
        out[sid] = {"cand": cand, "sample": sample, "reject": cand is None, "wrong": wrong}
        if oddity is not None:
            out[sid]["reason"] = None if cand is not None else ("장면 뜻" if not ok else "이상한 점")
    return out


SPEC_JUDGE = os.path.join(J.HERE, "samples", "spec-judge", "metrics.json")


def oddity_on():
    """후보 규칙 결합 기본값 — task 378 `판정(이상한 점):`이 「채택」이면 켬(samples/spec-judge/metrics.json 요약)."""
    try:
        return json.load(open(SPEC_JUDGE))["summary"]["oddity"]["verdict"] == "채택"
    except (OSError, KeyError, json.JSONDecodeError):
        return False


def oddity_answers(task, m=None):
    """과제의 이상한 점 답(t<과제>/O1) → {장면: {시드: "맞음"|"틀림"|None}}."""
    m = m or J.load()
    got = m.get(f"t{task}", {}).get("O1", {}).get("answers", {})
    out = defaultdict(dict)
    for it in J.items(None, tasks=[task]):
        out[it["scene"]][it["seed"]] = ((got.get(it["key"]) or {}).get("answers") or {}).get("oddity")
    return dict(out)


def screens(scenes):
    """후보 화면 수 — 되돌림 장면은 한 화면, 나머지는 후보·표본 두 화면."""
    return sum(1 if s["reject"] else 2 for s in scenes)


CAND_SWITCH_MAX = 0.25   # 사람이 기계 후보를 바꾼 장면 ≤ 되돌림 아닌 장면의 1/4
CAND_HIT_MIN = 0.75      # 블라인드 칸 J1 잡기·통과 하한


def cand_rules(scenes, hits):
    """후보 화면 `판정:` 세 규칙(notes/VERSE-REGEN.md 고정 절). scenes = [{reject, machine_cand, cand, revived}] (사람 답 기록 뒤),
    hits = {"틀림": [맞힘, 수], "맞음": [맞힘, 수]} (블라인드 칸 J1) → (판정 줄, 규칙별 [통과?, 설명])."""
    rej = [s for s in scenes if s["reject"]]
    rest = [s for s in scenes if not s["reject"]]
    revived = sum(1 for s in rej if s.get("revived") is not None)
    switched = sum(1 for s in rest if s.get("cand") is not None and s["cand"] != s["machine_cand"])
    catch, pss = (hits[k][0] / hits[k][1] if hits[k][1] else 0.0 for k in ("틀림", "맞음"))
    r = [(revived == 0, f"되돌림 장면에서 살린 수 {revived}" + ("" if rej else " (되돌림 장면 없음 — 해당 없음)")),
         (switched <= CAND_SWITCH_MAX * len(rest), f"기계 후보를 바꾼 장면 {switched} ≤ {CAND_SWITCH_MAX * len(rest):g}"),
         (catch >= CAND_HIT_MIN and pss >= CAND_HIT_MIN,
          f"블라인드 칸 J1 잡기 {hits['틀림'][0]}/{hits['틀림'][1]} {catch:.3f} · 통과 {hits['맞음'][0]}/{hits['맞음'][1]} {pss:.3f} (≥ {CAND_HIT_MIN})")]
    bad = [str(i + 1) for i, (ok, _) in enumerate(r) if not ok]
    return ("판정: 후보 화면 채택" if not bad else f"판정: 보류 (어긴 규칙 {', '.join(bad)})"), r


def cand_judgment(task, m=None):
    """과제의 기록된 사람 답(samples metrics의 cand) + 블라인드 칸 J1 → cand_rules."""
    m = m or J.load()
    met = json.load(open(os.path.join(J.HERE, "samples", J.TASKS[task][0], "metrics.json")))
    scenes = [{"reject": bool(sc["cand"]["machine_cand"] is None), **sc["cand"]} for sc in met["scenes"].values()]
    hits = {"틀림": [0, 0], "맞음": [0, 0]}
    for it in J.items(None, tasks=[task]):
        for qid, lab in it["labels"].items():
            hits[lab][0] += j1_answer(m, task, it["key"], qid)[0] == lab
            hits[lab][1] += 1
    return cand_rules(scenes, hits)


def regen_rules(scenes, fx):
    """두 겹 판정 3/3 `판정:` 세 규칙(notes/SPEC-REGEN.md 고정 절 — task 380). scenes = 사람 답 기록 뒤 metrics의 scenes,
    fx = 고정 절 ```json fixed {recur, rules} → (판정 줄, 규칙별 [통과?, 설명], 재발 항목 id 목록).
    재발 = 되돌림 동의 장면이면 그 장면 항목 전부 · 「없음」이고 메모가 words에 맞음 · 최종 후보 시드에서 qids 중 하나를 틀림으로 표시.
    살림 = 되돌림 장면에서 사람이 시드를 누른 수(376 cand_rules와 같은 정의 — revived가 있으면 셈)."""
    import re
    recur = []
    for it in fx["recur"]:
        sc = scenes[it["scene"]]
        c, memo = sc["cand"], (sc["cand"].get("memo") or "")
        agreed = c.get("answer") == "동의"
        by_memo = c.get("answer") == "없음" and bool(memo) and bool(re.search(it["words"], memo))
        seed = c.get("cand")
        by_mark = seed is not None and any(seed in sc["items"].get(q, {}).get("wrong", []) for q in it["qids"])
        if agreed or by_memo or by_mark:
            recur.append(it["id"])
    usable = sum(1 for sc in scenes.values() if sc["cand"].get("answer") == "쓸 만함")
    revived = sum(1 for sc in scenes.values() if sc["cand"].get("revived") is not None)
    rl = fx["rules"]
    r = [(len(recur) <= rl["recur_max"], f"사람 메모 재발 {len(recur)} ≤ {rl['recur_max']} ({', '.join(recur) or '없음'})"),
         (usable >= rl["usable_min"], f"「쓸 만함」 {usable} ≥ {rl['usable_min']}"),
         (revived <= rl["revive_max"], f"되돌림 살림 {revived} ≤ {rl['revive_max']}")]
    bad = [str(i + 1) for i, (ok, _) in enumerate(r) if not ok]
    return ("판정: 두 겹 판정 채택" if not bad else f"판정: 보류 (어긴 규칙 {', '.join(bad)})"), r, recur


def candidates(task, m=None, oddity=None):
    """과제의 J1 답 → pick_candidates. 지물 문항은 J1-prop, 나머지는 J1(j1_answer).
    oddity = 이상한 점 결합 켬/끔(None이면 oddity_on() — task 378 판정을 따름)."""
    m = m or J.load()
    answers = defaultdict(dict)
    for it in J.items(None, tasks=[task]):
        answers[it["scene"]][it["seed"]] = {q: j1_answer(m, task, it["key"], q)[0] for q in it["qids"]}
    on = oddity_on() if oddity is None else oddity
    return pick_candidates(answers, oddity_answers(task, m) if on else None)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "curve"
    if cmd == "rules":
        task = int(sys.argv[2])
        for c in rulebook(task):
            print(rule_text(c))
    elif cmd == "curve":
        rows, tot = curve()
        f = lambda h: f"{h[0]}/{h[1]} {h[0] / h[1] * 100:.1f}%" if h[1] else "—"
        for task, name, w, r, by in rows:
            print(f"{task} {name}  잡기 {f(w):>14s}  통과 {f(r):>14s}  | " + " · ".join(f"{c} {by[c][0][0]}/{by[c][0][1]}·{by[c][1][0]}/{by[c][1][1]}" for c in J.CLASSES if c in by))
        for name, (w, r) in tot.items():
            print(f"합계 {name}  잡기 {f(w):>14s}  통과 {f(r):>14s}")
    elif cmd == "cojudge":   # 함께 판정 화면: python3 batch/judge_learn.py cojudge <과제> [장면 ...]
        task, sids = int(sys.argv[2]), sys.argv[3:] or None
        sys.path.insert(0, J.HERE)
        import make_night_page as P
        marks, reject = machine_marks(task)
        trusted = [c for c, x in trust().items() if x["trusted"]]
        d, fn, _ = J.TASKS[task]
        P.main(os.path.join(J.HERE, "samples", d, "metrics.json"), sids or [s["id"] for s in J.page_scenes(fn)], task,
               machine=marks, reject=reject, trusted=trusted, dst=fn.replace("-pick.html", "-cojudge.html"))
        print(f"[JudgeLearn] 되돌림 후보 {[s for s, v in reject.items() if v]} · 믿음 종류(자동) {trusted or '없음'}")
    elif cmd == "cand":   # 후보 화면 규칙 보기 · --count = 만든 후보 화면 HTML의 화면 수
        task = int(sys.argv[2])
        if "--count" in sys.argv:
            sys.path.insert(0, J.HERE)
            import make_cand_page as C
            sc = J.page_scenes(C.dst(task))
            print(f"[JudgeLearn] {C.dst(task)} 장면 {len(sc)} · 되돌림 {sum(s['reject'] for s in sc)}")
            print(f"screens {screens(sc)} (≤{2 * len(sc)})")
            return
        on = {"--oddity": True, "--no-oddity": False}.get(next((x for x in sys.argv if x in ("--oddity", "--no-oddity")), ""))
        for sid, c in candidates(task, oddity=on).items():
            why = "장면 뜻 전부 틀림" if c.get("reason", "장면 뜻") == "장면 뜻" else "장면 뜻 맞은 장 모두 이상한 점"
            print(f"{sid}: " + (f"되돌림({why})" if c["reject"] else f"후보 s{c['cand']} · 표본 s{c['sample']}")
                  + " · 틀림 칸 " + " ".join(f"s{s}:{n}" for s, n in c["wrong"].items()))
    elif cmd == "candjudge":
        line, rules = cand_judgment(int(sys.argv[2]))
        for i, (ok, why) in enumerate(rules):
            print(f"규칙 {i + 1} {'통과' if ok else '어김'} — {why}")
        print(line)
    elif cmd == "regenjudge":   # 두 겹 판정 3/3: python3 batch/judge_learn.py regenjudge — notes/SPEC-REGEN.md 고정 절 규칙
        import judge_spec
        fx = judge_spec.fixed(os.path.join(J.HERE, "notes", "SPEC-REGEN.md"))
        met = json.load(open(os.path.join(J.HERE, "samples", "spec-regen", "metrics.json")))
        line, rules, _ = regen_rules(met["scenes"], fx)
        for i, (ok, why) in enumerate(rules):
            print(f"규칙 {i + 1} {'통과' if ok else '어김'} — {why}")
        print(line)
    elif cmd == "trust":
        for c, x in trust().items():
            print(f"{c:10s} 잡기 {x['catch']:>7s} 통과 {x['pass']:>7s} 하한 {x['lb']} {'믿음 — 사람에게서 덜어 냄' if x['trusted'] else '사람 확인'}")


if __name__ == "__main__":
    main()
