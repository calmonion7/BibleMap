#!/usr/bin/env python3
"""판정 학습 — 사람 라벨이 쌓일수록 판정자가 사람 기준을 배우고, 믿을 만해진 문항 종류는 사람에게서 덜어 낸다.

  python3 batch/judge_learn.py rules <과제>      # 그 과제 앞까지 배운 규칙집 보기
  python3 batch/judge_learn.py curve             # 시간 순서 평가: 과제마다 J1 기본 vs 규칙집(그 과제 앞까지만 배움)
  python3 batch/judge_learn.py trust             # 문항 종류별 믿음 관문(Wilson 95% 하한) — 사람에게서 덜어 낼 종류

원장 = 사람이 판정한 과제의 라벨(TASK_ORDER 순서, judge_items.TASKS의 페이지·metrics) + 그 과제에 대한 J1 답.
규칙집은 **그 과제보다 앞선 과제**의 사람 메모와 「기계·사람이 2장 이상 엇갈린 칸」으로만 만든다(처음 보는 라벨로 재기 —
notes/JUDGE-ITEMS.md 「판정 학습」 고정 절). 새 과제는 TASKS·TASK_ORDER·J1_RUNS에 한 줄씩 더하면 원장에 들어온다."""
import json, math, os, sys
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
    elif cmd == "trust":
        for c, x in trust().items():
            print(f"{c:10s} 잡기 {x['catch']:>7s} 통과 {x['pass']:>7s} 하한 {x['lb']} {'믿음 — 사람에게서 덜어 냄' if x['trusted'] else '사람 확인'}")


if __name__ == "__main__":
    main()
