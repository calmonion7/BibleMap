#!/usr/bin/env python3
"""task 423 — 규칙 후보를 다른 장면에서 같은 시드·한 낱말만 바꾼 두 장(A = 지금 파생 · B = 규칙 적용)으로 확인한다.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV batch/rule_ab.py gen       # 사례마다 A·B 한 장씩(가이드 사례는 명세 guide에서 다시 그린 가이드 · 스텝별)
  python3 batch/rule_ab.py judge   # 4장 한 묶음 × 장면 전 문항 × reps — claude -p Sonnet · 머리말 v2 · 답 없는 회차만
  python3 batch/rule_ab.py report  # 장마다 문항 다수결 · 축 문항 · 거르기 문항 맞음 수 · `재현:` 줄

사례·문항·시드는 notes/RULE-AB.md 「```json fixed 423」 절. 판정 부품은 inset_judge와 같다(judge_items.prepare/prompt/call/parse)."""
import json, os, re, subprocess, sys, threading
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "batch"))
import derive_scene as D
import judge_items as J

NOTES = os.path.join(HERE, "notes", "RULE-AB.md")
with open(NOTES, encoding="utf-8") as _fh:
    FX = json.loads(re.search(r"```json fixed 423\n(.*?)\n```", _fh.read(), re.S).group(1))
SAMPLES = os.path.join(HERE, "samples", FX["dir"])
METRICS = os.path.join(SAMPLES, "metrics.json")
W, H = 1216, 640
LOCK = threading.Lock()


def img(case, ab):
    return os.path.join(SAMPLES, f"{case['id']}-{ab}-s{FX['seed']}.png")


def prompts(case):
    """→ (A, B). A = route_prompt(+ a_from 바꿈 — 카드 자리표는 장면 카드로 채움) · B = A에서 b_from 한 군데만 바꿈."""
    spec = D.load(case["scene"])
    a = D.route_prompt(spec)
    if case["a_from"]:
        old, new = case["a_from"]
        assert a.count(old) == 1, (case["id"], old)
        a = a.replace(old, D._fill(new, D._scene_cards(spec)))
    old, new = case["b_from"]
    assert a.count(old) == 1, (case["id"], old)
    return a, a.replace(old, new)


def gen():
    import make_guide
    import run_scene
    busy = subprocess.run(["pgrep", "-fl", "mflux|run_scene.py --worker|gen_video_pilot|mlx_video"], capture_output=True, text=True).stdout.strip()
    if busy:
        sys.exit(f"[RuleAB] 다른 생성 프로세스가 돈다 — 겹치지 않게 멈춤:\n{busy}")
    os.makedirs(SAMPLES, exist_ok=True)
    out = os.path.expanduser(f"~/.local/biblemap-imggen/{FX['dir']}")
    os.makedirs(out, exist_ok=True)
    by_mode = {"gen": [], "gencn": []}
    for case in FX["cases"]:
        pa, pb = prompts(case)
        cn = {}
        if case["guide"]:   # 그 장면의 생성 조건 그대로 — 스텝별(앞 2스텝 뼈대 → 뒤 2스텝 깊이, inset_try와 같은 값)
            spec = D.load(case["scene"])
            gs = [os.path.join(SAMPLES, f"guide-{case['id']}-{k}.png") for k in (1, 2)]
            for k, g in zip((1, 2), gs):
                make_guide.make(spec, k).save(g, format="PNG")
            cn = {"control": gs[0], "control2": gs[1], "scale": 1.0, "cn_steps": 2, "cn_steps2": 2}
        for ab, p in (("A", pa), ("B", pb)):
            if not os.path.exists(img(case, ab)):
                by_mode["gencn" if cn else "gen"].append({"prompt": p, "seed": FX["seed"], "w": W, "h": H, "out": img(case, ab), **cn})
    for mode, jobs in by_mode.items():
        if jobs:
            print(f"[RuleAB] {mode} {len(jobs)}장 {run_scene.gen_zimage(jobs, out, mode)}", flush=True)


def load():
    return json.load(open(METRICS, encoding="utf-8")) if os.path.exists(METRICS) else {"answers": {}}


def save(m):
    with open(METRICS, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=1)


def ask(m, case, ab, rep):
    spec = D.load(case["scene"])
    it = {"task": f"rule-ab-{ab}", "scene": spec["id"], "title": spec["title"], "range": spec["verses"]["range"],
          "seed": FX["seed"], "src": img(case, ab), "qs": case["qs"], "qids": [q["id"] for q in case["qs"]]}
    d, files = J.prepare(it, FX["dir"])
    text = J.prompt(it, files, J.HEADERS["v2"])
    got, tries = None, []
    for _ in range(2):
        o = J.call(text, d, "sonnet")
        tries.append(J.use(o) | {"error": bool(o.get("is_error"))})
        got = None if o.get("is_error") else J.parse(o.get("result"), it["qids"])
        if got:
            break
    with LOCK:
        m["answers"].setdefault(f"{case['id']}-{ab}", {})[str(rep)] = {**(got or {"answers": None}), "tries": tries}
        save(m)


def judge(workers=8):
    gone = [os.path.basename(img(c, ab)) for c in FX["cases"] for ab in "AB" if not os.path.exists(img(c, ab))]
    if gone:   # task 424 회고: 그림이 빠진 채 판정하지 않음
        sys.exit(f"[RuleAB] 그림 없음 — 판정하지 않음: {', '.join(gone)}")
    m = load()
    todo = [(c, ab, r) for c in FX["cases"] for ab in "AB" for r in range(1, FX["reps"] + 1)
            if not ((m["answers"].get(f"{c['id']}-{ab}") or {}).get(str(r)) or {}).get("answers")]
    print(f"[RuleAB] 판정 {len(todo)}건", flush=True)
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda job: ask(m, *job), todo))


def votes(m, case, ab, qid):
    reps = (m["answers"].get(f"{case['id']}-{ab}") or {}).values()
    return sum(r["answers"][qid] == "맞음" for r in reps if r.get("answers")), sum(1 for r in reps if r.get("answers"))


def report():
    m = load()
    for case in FX["cases"]:
        gated = [q["id"] for q in J.gating(case["qs"])]
        ok = {}
        print(f"## {case['id']} — {case['scene']} s{FX['seed']}")
        for q in case["qs"]:
            row = [votes(m, case, ab, q["id"]) for ab in "AB"]
            tag = "축" if q["id"] in case["axis"] else "기록" if q.get("record") else ""
            print(f"- {q['id']} {q['q']}{f' ({tag})' if tag else ''}: A {row[0][0]}/{row[0][1]} · B {row[1][0]}/{row[1][1]}")
        for ab in "AB":
            ok[ab] = {q: 2 * votes(m, case, ab, q)[0] > votes(m, case, ab, q)[1] for q in [x["id"] for x in case["qs"]]}
        lost = [q for q in gated if q not in case["axis"] and ok["A"][q] and not ok["B"][q]]
        a_bad = any(not ok["A"][q] for q in case["axis"])
        b_good = all(ok["B"][q] for q in case["axis"])
        print(f"- 거르기 맞음: A {sum(ok['A'][q] for q in gated)}/{len(gated)} · B {sum(ok['B'][q] for q in gated)}/{len(gated)} · B가 잃은 문항 {lost or '없음'}")
        print(f"재현: {case['id']} {'예' if a_bad and b_good and len(lost) <= 2 else '아니오'}\n")


if __name__ == "__main__":
    {"gen": gen, "judge": judge, "report": report}[sys.argv[1]]()
