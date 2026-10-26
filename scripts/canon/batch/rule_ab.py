#!/usr/bin/env python3
"""task 423 — 규칙 후보를 다른 장면에서 같은 시드·한 낱말만 바꾼 두 장(A = 지금 파생 · B = 규칙 적용)으로 확인한다.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV batch/rule_ab.py gen       # 사례마다 A·B 한 장씩(가이드 사례는 명세 guide에서 다시 그린 가이드 · 스텝별)
  python3 batch/rule_ab.py judge   # 4장 한 묶음 × 장면 전 문항 × reps — claude -p Sonnet · 머리말 v2 · 답 없는 회차만
  python3 batch/rule_ab.py report  # 장마다 문항 다수결 · 축 문항 · 거르기 문항 맞음 수 · `재현:` 줄
  python3 batch/rule_ab.py --fixed 432 seeds|gen|judge|report   # task 432 — 시드 여럿(8시드 대조군) · `통과:`·`채택:` 줄
  python3 batch/rule_ab.py --fixed 432 page <out.html>      # task 433 — 단계 ④ 사람 판정 화면(채택된 쪽 8장 전부 · 원문 · 답 복사)
  python3 batch/rule_ab.py --fixed 432 record '<판정 task 432 + JSON 한 줄>'   # 사람 답 → pick-verdict.txt · 노트 줄 · 고른 장 approve

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
                fx["_notes"] = os.path.join(HERE, "notes", name)
                return fx
    sys.exit(f"[RuleAB] 고정 절 {n} 없음")


def use(n):
    global FX, FX_N, NOTES, SAMPLES, METRICS
    FX, FX_N = fixed(n), n
    NOTES = FX.pop("_notes")
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


def side(m, case):
    """사람에게 보일 쪽 — 채택 규칙이 있으면 채택된 쪽, 없으면 B."""
    if not FX.get("adopt"):
        return "B"
    return "B" if adopt(majority(m, case), [q["id"] for q in J.gating(case["qs"])], FX["adopt"])[0] else "A"


def page(out):
    """task 433 — 단계 ④ 사람 판정 화면: 고른 쪽 8장 전부(기계 통과 + 불통과, 틀린 문항 순) · 장면 구절 원문(순간 절 굵게) · 확대 · 답 복사.
    틀은 inset_judge와 같다(inset_judge_page.html). 카드 메모 = 그 쪽에서 가장 많이 떨어진 거르기 문항의 표 수와 틀림 이유 하나."""
    import base64, io
    import inset_judge as IJ
    from PIL import Image
    m, case = load(), FX["cases"][0]
    ab, spec = side(m, case), D.load(case["scene"])
    gated = J.gating(case["qs"])
    ok = majority(m, case)[ab]
    weak = min(gated, key=lambda q: sum(ok[s][q["id"]] for s in FX["seeds"]))
    book = {"왕상": 11}[spec["verses"]["range"].split()[0]]
    verses = json.load(open(os.path.join(HERE, "..", "..", "data", "bible", "verses.json"), encoding="utf-8"))
    rows = []
    for cv in spec["verses"]["quotes"]:
        c, v = map(int, cv.split(":"))
        txt = verses[f"{book:02d}{c:03d}{v:03d}"]["textKo"].strip()
        rows.append(f'<p><span class="ref">{cv}</span>{"<b>" + txt + "</b>" if cv == spec["moment"]["verse"] else txt}</p>')
    cards = []
    for s in FX["seeds"]:
        reps = [r for r in (m["answers"].get(key(case, ab, s)) or {}).values() if r.get("answers")]
        yes = sum(r["answers"][weak["id"]] == "맞음" for r in reps)
        why = next((r["reasons"][weak["id"]] for r in reps if r["answers"][weak["id"]] == "틀림" and (r.get("reasons") or {}).get(weak["id"])), "")
        fails = [q["q"] for q in gated if not ok[s][q["id"]]]
        cards.append({"seed": s, "pass": not fails, "fails": fails,
                      "note": f"{weak['q']} 맞음 {yes}/{len(reps)}표" + (f" — 틀림 이유: {why}" if why else "")})
    cards.sort(key=lambda c: (not c["pass"], len(c["fails"]), FX["seeds"].index(c["seed"])))

    def uri(path):
        buf = io.BytesIO()
        Image.open(path).convert("RGB").save(buf, "JPEG", quality=88)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    imgs = {f"comp-{s}": uri(img(case, ab, s)) for s in FX["seeds"]}
    tpl = open(os.path.join(HERE, "batch", "inset_judge_page.html"), encoding="utf-8").read()
    html = IJ.fill(tpl, TITLE="두 여인 재판 그림 고르기", H1="두 여인의 재판 — 쓸 그림 고르기", RANGE=spec["verses"]["range"], TASK=str(FX_N),
                   LEDE=f"3:26 — 참 어머니가 앉은 솔로몬 왕 앞에서 아들을 위해 애원하고, 다른 여인은 아기를 안고 섰으며, 왕 앞 바닥에는 3:24에 가져온 칼이 있는 때입니다. 시드 8장을 모두 보여 드립니다. 기계 판정을 통과한 장과 통과하지 못한 장을 함께 놓았고, 카드마다 가장 많이 떨어진 문항({weak['q']})의 기계 표와 틀림 이유를 적었습니다.",
                   HINT="그림을 누르면 원래 화소로 1~3배 확대해 볼 수 있습니다. 기계 표는 너그러울 수 있습니다(s42 칼 자리) — 눈으로 갈라 주세요.",
                   MEMO_EG="예: 칼이 왕 앞이 아니라 여인 발치")
    html = html.replace("@@VERSES@@", "".join(rows)).replace("/*CARDS*/[]", json.dumps(cards, ensure_ascii=False))
    html = html.replace("/*IMGS*/{}", json.dumps(imgs))   # 그림은 마지막에(417 판 1)
    open(out, "w", encoding="utf-8").write(html)
    print(f"[RuleAB] 화면 {out} {len(html) / 1e6:.2f}MB · {case['id']}-{ab} 통과 {sum(c['pass'] for c in cards)}/{len(cards)}")


def record(text):
    """사람 답(「판정 task N」 + JSON 한 줄) → 원문 pick-verdict.txt · metrics verdict · 노트 「- 사람 답(8시드)」 줄. 고른 장이 있으면 approve(night-pick, by user)."""
    import approve
    v = json.loads(text.split("\n", 1)[1].strip().splitlines()[0])
    m, case = load(), FX["cases"][0]
    ab = side(m, case)
    with open(os.path.join(SAMPLES, "pick-verdict.txt"), "w", encoding="utf-8") as fh:
        fh.write(text.strip() + "\n")
    m["verdict"] = v
    save(m)
    line = f"- 사람 답(8시드): {v['pick']}" + (f" · 메모 「{v['memo']}」" if v.get("memo") else "")
    with open(NOTES, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(f"[RuleAB] {line}")
    if v["pick"] != "none":
        seed = int(v["pick"].lstrip("s"))
        image = os.path.relpath(img(case, ab, seed), HERE)
        approve.save_spec(approve.night_pick(approve.load_spec(case["scene"]), seed, "base", image, "user"))
        print(f"[RuleAB] 장면 완료 기록 {case['scene']} ← {image}")

if __name__ == "__main__":
    args = sys.argv[1:]
    use(int(args.pop(args.index("--fixed") + 1)) if "--fixed" in args else 423)
    args = [a for a in args if a != "--fixed"]
    if args[0] in ("page", "record"):   # task 433 — 단계 ④ 사람 판정
        {"page": page, "record": record}[args[0]](args[1])
        sys.exit(0)
    {"gen": gen, "judge": judge, "report": report, "seeds": seeds}[args[0]]()
