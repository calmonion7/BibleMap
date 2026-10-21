#!/usr/bin/env python3
"""restyle-try — CN이 누른 화풍을 되살리는 안 해 본 두 방법(388 다음 수단 2 · 389 `점검: CN 탓` 뒤).

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV batch/restyle_try.py gen       # ① 두 단계 img2img 6장 · ② CN 앞 1·2스텝 4장 (생성 프로세스 한 번에 하나)
  python3 batch/restyle_try.py judge   # 12장(+ 바탕 388 1.0·4 두 장) × S·E 3회 — claude -p Sonnet · 머리말 v2
  python3 batch/restyle_try.py report  # 장마다 다수결 · 통과 설정
  python3 batch/restyle_try.py check   # 개수·빈 답·노트 `시험:` 줄 = 다시 셈 → ok

규칙은 notes/RESTYLE-TRY.md 고정 절. 문구·가이드·시드는 388 격자 1.0·4 job(_zjobs.json) 그대로, 문항은 JORDAN-GUIDE 고정 절 style·elements.
그림 ~/.local/biblemap-imggen/restyle-try/<갈래>/s<시드>.png · 답 samples/restyle-try/metrics.json."""
import json, os, re, sys, threading
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "batch"))
import derive_scene as D
import judge_items as J

NOTES = os.path.join(HERE, "notes", "RESTYLE-TRY.md")
METRICS = os.path.join(HERE, "samples", "restyle-try", "metrics.json")
IMG = os.path.expanduser("~/.local/biblemap-imggen")
OUT = f"{IMG}/restyle-try"
SID = "authored-david-returns-jerusalem"
BASE = f"{IMG}/jordan-guide/g-1.0-4/{SID}"
LOCK = threading.Lock()


def fixed(path):
    return json.loads(re.search(r"```json fixed\n(.*?)\n```", open(path, encoding="utf-8").read(), re.S).group(1))


FX = fixed(NOTES)
G = fixed(os.path.join(HERE, "notes", "JORDAN-GUIDE.md"))["scenes"][SID]
QS = {"S": G["style"], "E": G["elements"]}


def arms():
    """갈래 이름 → (방법, 값). ① i2i-<강도> · ② cn-<스텝> · 바탕 base(388 1.0·4, 생성 안 함)."""
    return {"base": ("base", None), **{f"i2i-{s}": ("i2i", s) for s in FX["i2i_strengths"]},
            **{f"cn-{k}": ("cn", k) for k in FX["cn_steps"]}}


def img(arm, s):
    return f"{BASE}/s{s}.png" if arm == "base" else f"{OUT}/{arm}/s{s}.png"


def gen():
    sys.path.insert(0, os.path.join(HERE, "batch"))
    import run_scene
    src = {j["seed"]: j for j in json.load(open(f"{BASE}/_zjobs.json"))}
    for mode, kind in (("i2i", "i2i"), ("gencn", "cn")):
        jobs = []
        for arm, (k, v) in arms().items():
            for s in FX["seeds"]:
                if k != kind or os.path.exists(img(arm, s)):
                    continue
                j = {"prompt": src[s]["prompt"], "seed": s, "w": src[s]["w"], "h": src[s]["h"], "out": img(arm, s)}
                j.update({"src": img("base", s), "strength": v} if kind == "i2i" else
                         {"control": src[s]["control"], "scale": FX["cn_scale"], "cn_steps": v})
                os.makedirs(os.path.dirname(j["out"]), exist_ok=True)
                jobs.append(j)
        if jobs:
            d = os.path.join(OUT, f"_{mode}")
            os.makedirs(d, exist_ok=True)
            secs = run_scene.gen_zimage(jobs, d, mode)
            print(f"[RestyleTry] {mode} {len(jobs)}장 {secs}", flush=True)


def load():
    return json.load(open(METRICS, encoding="utf-8")) if os.path.exists(METRICS) else {"answers": {}}


def save(m):
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    with open(METRICS, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=1)


def ask(m, arm, s, kind, rep):
    spec = D.load(SID)
    it = {"key": f"{arm}:{s}", "task": f"rt-{arm}", "scene": SID, "title": spec["title"], "range": spec["verses"]["range"],
          "seed": s, "src": img(arm, s), "qs": [dict(q) for q in QS[kind]], "qids": [q["id"] for q in QS[kind]]}
    d, files = J.prepare(it, "restyle-try")
    text = J.prompt(it, files, J.HEADERS["v2"])
    got, tries = None, []
    for _ in range(2):
        o = J.call(text, d, "sonnet")
        tries.append(J.use(o) | {"error": bool(o.get("is_error"))})
        got = None if o.get("is_error") else J.parse(o.get("result"), it["qids"])
        if got:
            break
    with LOCK:
        m["answers"].setdefault(it["key"], {}).setdefault(kind, {})[str(rep)] = {"tries": tries, **(got or {"answers": None})}
        save(m)


def judge(workers=8):
    m = load()
    todo = [(a, s, k, r) for a in arms() for s in FX["seeds"] for k in QS for r in range(1, FX["reps"] + 1)
            if not ((m["answers"].get(f"{a}:{s}") or {}).get(k, {}).get(str(r)) or {}).get("answers")]
    print(f"[RestyleTry] 판정 {len(todo)}건", flush=True)
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda job: ask(m, *job), todo))


def votes(m, arm, s, qid):
    kind = "S" if qid.startswith("s.") else "E"
    return [(r.get("answers") or {}).get(qid) for _, r in sorted((m["answers"].get(f"{arm}:{s}") or {}).get(kind, {}).items())]


def maj(v):
    return "맞음" if v.count("맞음") * 2 > len(v) else "틀림"


def passed(m):
    return [a for a in arms() if a != "base" and all(maj(votes(m, a, s, q)) == "맞음" for s in FX["seeds"] for q in FX["pass_qs"])]


def conclude(m):
    p = passed(m)
    return f"통과 {', '.join(p)}" if p else "통과 없음"


def report():
    m = load()
    qs = [q["id"] for q in QS["S"] + QS["E"]]
    print("갈래      시드 " + " ".join(q.split(".")[1][:10] for q in qs))
    for a in arms():
        for s in FX["seeds"]:
            print(f"{a:9} s{s:<3} " + " ".join("".join(x[0] if x else "-" for x in votes(m, a, s, q)) for q in qs))
    print(f"시험: {conclude(m)}")


def check():
    m, err = load(), []
    for a in arms():
        for s in FX["seeds"]:
            if not os.path.exists(img(a, s)):
                err.append(f"그림 없음 {a} s{s}")
            for q in QS["S"] + QS["E"]:
                v = votes(m, a, s, q["id"])
                if len(v) != FX["reps"] or None in v:
                    err.append(f"{a} s{s} {q['id']} 답 {v}")
    line = re.findall(r"^시험: (.+)$", open(NOTES, encoding="utf-8").read(), re.M)
    if not err and line != [conclude(m)]:
        err.append(f"노트 시험 줄 {line} ≠ 다시 셈 {conclude(m)}")
    print("ok" if not err else "\n".join(err[:20]))
    return not err


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    fn = {"gen": gen, "judge": judge, "report": report, "check": check}.get(cmd)
    if not fn:
        sys.exit(__doc__)
    r = fn()
    if cmd == "check":
        sys.exit(0 if r else 1)
