#!/usr/bin/env python3
"""task#389 — 화풍 판정자 점검(GPU 0): 388 격자 s11 「화풍 틀림」이 CN 탓인지 판정자·시드 탓인지 가린다.

  python3 batch/style_judge.py judge     # 30장 × 3회 S 문항(claude -p Sonnet · 머리말 v2) — 이미 답한 회차는 건너뜀
  python3 batch/style_judge.py report    # 장마다 다수결·묶음 합계·결론
  python3 batch/style_judge.py check     # 개수·빈 답·노트 `점검:` 줄 = 다시 셈한 결론 → ok

묶음·결론 규칙은 notes/STYLE-JUDGE.md 고정 절. S 문항은 notes/JORDAN-GUIDE.md 고정 절 `style` 그대로(문구 복제 없음).
답은 samples/style-judge/metrics.json에 회차마다 바로."""
import json, os, re, sys, threading
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "batch"))
import derive_scene as D
import judge_items as J

NOTE_MD = os.path.join(HERE, "notes", "STYLE-JUDGE.md")
GUIDE = os.path.join(HERE, "notes", "JORDAN-GUIDE.md")
METRICS = os.path.join(HERE, "samples", "style-judge", "metrics.json")
IMG = os.path.expanduser("~/.local/biblemap-imggen")
SID = "authored-david-returns-jerusalem"
LOCK = threading.Lock()


def fixed(path):
    return json.loads(re.search(r"```json fixed\n(.*?)\n```", open(path, encoding="utf-8").read(), re.S).group(1))


FX = fixed(NOTE_MD)
QS = fixed(GUIDE)["scenes"][SID]["style"]


def images():
    """(묶음, 과제 꼬리표, 장면, 시드, 그림 경로) — A 387 r1 · B 사람 승인 최종 · C 388 격자."""
    out = [("A", "387r1", SID, s, f"{IMG}/jordan-scene/r1/{SID}/s{s}.png") for s in FX["A_seeds"]]
    for sid in FX["B_scenes"]:
        f = D.load(sid)["approved"]["final"]
        out.append(("B", "approved", sid, f["seed"], f["image"] if os.path.isabs(f["image"]) else os.path.join(HERE, f["image"])))
    for g in FX["C_grid"]:
        out += [("C", g, SID, s, f"{IMG}/jordan-guide/{g}/{SID}/s{s}.png") for s in (11, 42)]
    return out


def load():
    return json.load(open(METRICS, encoding="utf-8")) if os.path.exists(METRICS) else {"answers": {}}


def save(m):
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    with open(METRICS, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=1)


def ask(m, grp, tag, sid, seed, src, rep):
    spec = D.load(sid)
    it = {"key": f"{tag}:{sid}:{seed}", "task": tag, "scene": sid, "title": spec["title"], "range": spec["verses"]["range"],
          "seed": seed, "src": src, "qs": [dict(q) for q in QS], "qids": [q["id"] for q in QS]}
    d, files = J.prepare(it, "style-judge")
    text = J.prompt(it, files, J.HEADERS["v2"])
    got, tries = None, []
    for _ in range(2):   # JSON이 깨지면 한 번만 다시(plain_words.ask와 같음)
        o = J.call(text, d, "sonnet")
        tries.append(J.use(o) | {"error": bool(o.get("is_error"))})
        got = None if o.get("is_error") else J.parse(o.get("result"), it["qids"])
        if got:
            break
    with LOCK:
        m["answers"].setdefault(it["key"], {"group": grp, "src": src, "reps": {}})["reps"][str(rep)] = {"tries": tries, **(got or {"answers": None})}
        save(m)
    if not got:
        print(f"[StyleJudge] {it['key']} 회차 {rep} 답 없음", flush=True)


def judge(workers=8):
    m = load()
    todo = [(g, t, sid, s, src, r) for g, t, sid, s, src in images() for r in range(1, FX["reps"] + 1)
            if not ((m["answers"].get(f"{t}:{sid}:{s}") or {}).get("reps", {}).get(str(r)) or {}).get("answers")]
    print(f"[StyleJudge] 판정 {len(todo)}건", flush=True)
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda job: ask(m, *job), todo))


def votes(m, key, qid="s.style"):
    return [(r.get("answers") or {}).get(qid) for _, r in sorted((m["answers"].get(key) or {}).get("reps", {}).items())]


def majority(v):
    return "틀림" if v.count("틀림") * 2 > len(v) else "맞음"


def conclude(m):
    rows = [(g, f"{t}:{sid}:{s}") for g, t, sid, s, _ in images()]
    b_wrong = sum(1 for g, k in rows if g == "B" and majority(votes(m, k)) == "틀림")
    agree = sum(1 for _, k in rows if len(set(votes(m, k))) == 1) / len(rows)
    if b_wrong >= FX["unstable_b_wrong"] or agree < FX["unstable_agree"]:
        c = "판정자 불안정"
    elif majority(votes(m, f"387r1:{SID}:11")) == "틀림":
        c = "CN 무관"
    else:
        c = "CN 탓"
    return c, {"b_wrong": b_wrong, "agree": round(agree, 3)}


def report():
    m = load()
    for g, t, sid, s, _ in images():
        k = f"{t}:{sid}:{s}"
        v, b = votes(m, k), votes(m, k, "s.no-blob")
        print(f"{g} {t:9} {sid[9:34]:25} s{s:<4} 화풍 {''.join(x[0] if x else '-' for x in v)} → {majority(v)} · 복제없음 {''.join(x[0] if x else '-' for x in b)}")
    for g in "ABC":
        ks = [f"{t}:{sid}:{s}" for gg, t, sid, s, _ in images() if gg == g]
        print(f"[{g}] 화풍 다수결 맞음 {sum(majority(votes(m, k)) == '맞음' for k in ks)}/{len(ks)}")
    # 측정만: 다수결로 다시 센 388 격자 통과(두 시드 모두 화풍·복제없음 다수결 맞음) — 388 판정은 바꾸지 않는다
    ok = [g for g in FX["C_grid"] if all(majority(votes(m, f"{g}:{SID}:{s}", q)) == "맞음" for s in (11, 42) for q in ("s.style", "s.no-blob"))]
    print(f"[측정] 다수결 격자 통과 설정: {ok or '없음'}")
    c, why = conclude(m)
    print(f"결론: {c} {why}")


def check():
    m, err = load(), []
    imgs = images()
    for g, n in (("A", 8), ("B", 10), ("C", 12)):
        if sum(1 for x in imgs if x[0] == g) != n:
            err.append(f"{g} 장 수 {n} 아님")
    for g, t, sid, s, _ in imgs:
        v = votes(m, f"{t}:{sid}:{s}") + votes(m, f"{t}:{sid}:{s}", "s.no-blob")
        if len(v) != 2 * FX["reps"] or None in v:
            err.append(f"{t}:{sid}:{s} 답 {len(v)}/{2 * FX['reps']} 또는 빈 답")
    line = re.findall(r"^점검: (.+)$", open(NOTE_MD, encoding="utf-8").read(), re.M)
    if not err and line != [conclude(m)[0]]:
        err.append(f"노트 점검 줄 {line} ≠ 다시 셈 {conclude(m)[0]}")
    print("ok" if not err else "\n".join(err))
    return not err


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "judge":
        judge()
    elif cmd == "report":
        report()
    elif cmd == "check":
        sys.exit(0 if check() else 1)
    else:
        sys.exit(__doc__)
