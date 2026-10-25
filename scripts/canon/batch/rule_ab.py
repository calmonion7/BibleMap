#!/usr/bin/env python3
"""task 423 — 규칙 후보를 다른 장면에서 같은 시드·한 낱말만 바꾼 두 장(A = 지금 파생 · B = 규칙 적용)으로 확인한다.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV batch/rule_ab.py gen       # 사례마다 A·B 한 장씩(가이드 사례는 명세 guide에서 다시 그린 가이드 · 스텝별)
  python3 batch/rule_ab.py judge   # 4장 한 묶음 × 장면 전 문항 × reps — claude -p Sonnet · 머리말 v2 · 답 없는 회차만
  python3 batch/rule_ab.py report  # 장마다 문항 다수결 · 축 문항 · 거르기 문항 맞음 수 · `재현:` 줄
  python3 batch/rule_ab.py --fixed 432 seeds|gen|judge|report   # task 432 — 시드 여럿(8시드 대조군) · `통과:`·`채택:` 줄

사례·문항·시드는 notes/ 안 「```json fixed N」 절(기본 423 = notes/RULE-AB.md). `seeds`가 있으면 시드마다 그림·판정. 판정 부품은 inset_judge와 같다(judge_items.prepare/prompt/call/parse)."""
import json, os, re, subprocess, sys, threading
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "batch"))
import derive_scene as D
import judge_items as J

W, H = 1216, 640
LOCK = threading.Lock()


def fixed(n):
    """notes/*.md 안 「```json fixed N」 절 → 고정 값(시드 목록 `seeds`, 없으면 `[seed]`)."""
    for name in sorted(os.listdir(os.path.join(HERE, "notes"))):
        if name.endswith(".md"):
            with open(os.path.join(HERE, "notes", name), encoding="utf-8") as fh:
                hit = re.search(rf"```json fixed {n}\n(.*?)\n```", fh.read(), re.S)
            if hit:
                fx = json.loads(hit.group(1))
                fx["seeds"] = fx.get("seeds") or [fx["seed"]]
                return fx
    sys.exit(f"[RuleAB] 고정 절 {n} 없음")


def use(n):
    global FX, SAMPLES, METRICS
    FX = fixed(n)
    SAMPLES = os.path.join(HERE, "samples", FX["dir"])
    METRICS = os.path.join(SAMPLES, "metrics.json")


def img(case, ab, seed):
    return os.path.join(SAMPLES, f"{case['id']}-{ab}-s{seed}.png")


def key(case, ab, seed):
    """판정 키 — 시드 하나인 고정 절(423)은 옛 키 그대로."""
    return f"{case['id']}-{ab}" if "seed" in FX and len(FX["seeds"]) == 1 else f"{case['id']}-{ab}-s{seed}"


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
        for seed in FX["seeds"]:
            for ab, p in (("A", pa), ("B", pb)):
                if not os.path.exists(img(case, ab, seed)):
                    by_mode["gencn" if cn else "gen"].append({"prompt": p, "seed": seed, "w": W, "h": H, "out": img(case, ab, seed), **cn})
    for mode, jobs in by_mode.items():
        if jobs:
            print(f"[RuleAB] {mode} {len(jobs)}장 {run_scene.gen_zimage(jobs, out, mode)}", flush=True)


def load():
    return json.load(open(METRICS, encoding="utf-8")) if os.path.exists(METRICS) else {"answers": {}}


def save(m):
    with open(METRICS, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=1)


def ask(m, case, ab, seed, rep):
    spec = D.load(case["scene"])
    it = {"task": f"rule-ab-{ab}", "scene": spec["id"], "title": spec["title"], "range": spec["verses"]["range"],
          "seed": seed, "src": img(case, ab, seed), "qs": case["qs"], "qids": [q["id"] for q in case["qs"]]}
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
        m["answers"].setdefault(key(case, ab, seed), {})[str(rep)] = {**(got or {"answers": None}), "tries": tries}
        save(m)


def judge(workers=8):
    gone = [os.path.basename(img(c, ab, s)) for c in FX["cases"] for ab in "AB" for s in FX["seeds"] if not os.path.exists(img(c, ab, s))]
    if gone:   # task 424 회고: 그림이 빠진 채 판정하지 않음
        sys.exit(f"[RuleAB] 그림 없음 — 판정하지 않음: {', '.join(gone)}")
    m = load()
    todo = [(c, ab, s, r) for c in FX["cases"] for ab in "AB" for s in FX["seeds"] for r in range(1, FX["reps"] + 1)
            if not ((m["answers"].get(key(c, ab, s)) or {}).get(str(r)) or {}).get("answers")]
    print(f"[RuleAB] 판정 {len(todo)}건", flush=True)
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda job: ask(m, *job), todo))


def votes(m, case, ab, seed, qid):
    reps = (m["answers"].get(key(case, ab, seed)) or {}).values()
    return sum(r["answers"][qid] == "맞음" for r in reps if r.get("answers")), sum(1 for r in reps if r.get("answers"))


def majority(m, case):
    """→ {ab: {seed: {qid: 다수결 맞음}}}"""
    return {ab: {s: {q["id"]: 2 * votes(m, case, ab, s, q["id"])[0] > votes(m, case, ab, s, q["id"])[1] for q in case["qs"]}
                 for s in FX["seeds"]} for ab in "AB"}


def adopt(ok, gated, rule):
    """task 432 미리 정한 채택 규칙 — 축 문항 다수결 맞음 장 수 합이 B가 A보다 gain 이상 많고, 다른 거르기 문항은 B가 loss장 넘게 안 떨어짐."""
    n = {ab: {q: sum(ok[ab][s][q] for s in ok[ab]) for q in gated} for ab in "AB"}
    sa, sb = (sum(n[ab][q] for q in rule["qs"]) for ab in "AB")
    lost = [q for q in gated if q not in rule["qs"] and n["A"][q] - n["B"][q] > rule["loss"]]
    return sb - sa >= rule["gain"] and not lost, sa, sb, lost


def report():
    m = load()
    for case in FX["cases"]:
        gated = [q["id"] for q in J.gating(case["qs"])]
        ok = majority(m, case)
        k = len(FX["seeds"])
        print(f"## {case['id']} — {case['scene']} s{' s'.join(map(str, FX['seeds']))}")
        for q in case["qs"]:
            tag = "축" if q["id"] in case.get("axis", []) else "기록" if q.get("record") else ""
            row = [(sum(ok[ab][s][q["id"]] for s in FX["seeds"]),) + tuple(map(sum, zip(*[votes(m, case, ab, s, q["id"]) for s in FX["seeds"]]))) for ab in "AB"]
            print(f"- {q['id']} {q['q']}{f' ({tag})' if tag else ''}: " + " · ".join(f"{ab} {r[0]}/{k}장 ({r[1]}/{r[2]}표)" for ab, r in zip("AB", row)))
        for ab in "AB":
            fine = [s for s in FX["seeds"] if all(ok[ab][s][q] for q in gated)]
            print(f"통과: {case['id']}-{ab} {len(fine)}/{k}" + (f" (s{' s'.join(map(str, fine))})" if fine else ""))
        if case.get("axis"):
            s = FX["seeds"][0]
            a, b = ok["A"][s], ok["B"][s]
            lost = [q for q in gated if q not in case["axis"] and a[q] and not b[q]]
            print(f"- 거르기 맞음: A {sum(a[q] for q in gated)}/{len(gated)} · B {sum(b[q] for q in gated)}/{len(gated)} · B가 잃은 문항 {lost or '없음'}")
            print(f"재현: {case['id']} {'예' if any(not a[q] for q in case['axis']) and all(b[q] for q in case['axis']) and len(lost) <= 2 else '아니오'}")
        if FX.get("adopt"):
            yes, sa, sb, lost = adopt(ok, gated, FX["adopt"])
            print(f"채택: {case['id']} {'예' if yes else '아니오'} ({'·'.join(FX['adopt']['qs'])} 맞음 장 A {sa} · B {sb} · 차 {sb - sa:+d}"
                  f" — 기준 +{FX['adopt']['gain']} · {FX['adopt']['loss']}장 넘게 떨어진 문항 {lost or '없음'})")
        print()


def seeds():
    print(" ".join(map(str, FX["seeds"])))

if __name__ == "__main__":
    args = sys.argv[1:]
    use(int(args.pop(args.index("--fixed") + 1)) if "--fixed" in args else 423)
    args = [a for a in args if a != "--fixed"]
    {"gen": gen, "judge": judge, "report": report, "seeds": seeds}[args[0]]()
