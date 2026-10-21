#!/usr/bin/env python3
"""상식 규칙집(notes/PLAUSIBILITY.md) — 그림이 물리·몸·사물 상식에 맞는가를 규칙 하나씩 묻는다.

  python3 batch/plausibility.py validate   # 사람 라벨 묶음(지적 그림 · 결함 없는 그림) × 걸린 규칙 × 3회 — claude -p Sonnet · 머리말 pl1
  python3 batch/plausibility.py report     # 규칙마다 잡음 · 헛경보 · 채택 여부
  python3 batch/plausibility.py check      # 답 빠짐 0 · 노트 `채택:` 줄 = 다시 셈 → ok

다른 판정 묶음은 `questions(spec, adopted_only=True)`로 채택된 규칙만 문항으로 쓴다. 답은 samples/plausibility/metrics.json."""
import hashlib, json, os, re, sys, threading
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "batch"))
import derive_scene as D
import judge_items as J

NOTES = os.path.join(HERE, "notes", "PLAUSIBILITY.md")
METRICS = os.path.join(HERE, "samples", "plausibility", "metrics.json")
IMG = os.path.expanduser("~/.local/biblemap-imggen")
FX = json.loads(re.search(r"```json fixed\n(.*?)\n```", open(NOTES, encoding="utf-8").read(), re.S).group(1))
RULES = {r["id"]: r for r in FX["rules"]}
LOCK = threading.Lock()
# O1(「모호하면 이상함」)이 이상 없음 통과 11/33으로 너무 많이 잡았다 → 반대로 결함이 분명할 때만 틀림
HEADER = """너는 그림의 물리·몸·사물 상식을 검수하는 미술 감독이다. Read 도구로 아래 그림 파일을 연 뒤, 문항마다 그 상식이 이 그림에서 깨졌는지 판정하라.
- 문항이 말하는 결함이 그림에 **분명히 보이면** 「틀림」, 결함이 보이지 않으면 「맞음」.
- 작고 멀어 흐릿한 것, 가려져 확인할 수 없는 것은 결함이 아니다 — 「맞음」.
- 장면의 뜻·인물 신원·화풍은 묻지 않는다. 문항의 상식 하나만 본다.
- 출력은 JSON 하나만: {"answers": {"<문항 id>": "맞음" 또는 "틀림", ...}, "reasons": {"<문항 id>": "본 것 — 짧게", ...}}"""


def scene_text(sid):
    return D.route_prompt(D.load(sid)).lower()


def questions(spec_or_sid, adopted_only=False):
    """장면 명세 낱말이 고르는 규칙 → 문항 목록(id·q·what). adopted_only면 노트 「채택:」 줄의 규칙만."""
    text = scene_text(spec_or_sid) if isinstance(spec_or_sid, str) else D.route_prompt(spec_or_sid).lower()
    keep = adopted() if adopted_only else None
    out = []
    for r in FX["rules"]:
        hit = r.get("always") or any(re.search(rf"\b{t}\b", text) for t in r.get("triggers", []))
        if hit and (keep is None or r["id"] in keep):
            out.append({"id": r["id"], "q": r["q"], "what": r["what"]})
    return out


def adopted():
    line = re.findall(r"^채택: (.*)$", open(NOTES, encoding="utf-8").read(), re.M)
    return [x.strip() for x in line[0].split("·") if x.strip() and x.strip() != "없음"] if line else []


def items():
    """검증 묶음 → [{key, image, scene, labels: {규칙: 맞음|틀림}}]. 걸린 규칙 전부를 묻고, 라벨 있는 규칙만 센다."""
    V, out = FX["validate"], []
    E = V["engedi_hand"]
    scr = json.load(open(os.path.join(HERE, E["metrics"]), encoding="utf-8"))["screens"][E["screen"]]
    group = [r["id"] for r in FX["rules"] if r.get("group") == E["group"]]
    for x in scr:
        p = E["paths"][x["kind"]]
        img = os.path.join(HERE, p[1:]) if p.startswith("@") else os.path.join(IMG, p.format(seed=x["seed"]))
        lab = "틀림" if x["n"] in E["pressed"] else "맞음"
        out.append({"key": f"engedi:{x['kind']}:{x['seed']}", "image": img, "scene": E["scene"], "group_label": lab,
                    "labels": {} if lab == "틀림" else {g: "맞음" for g in group}, "source": f"사람 365 G-hand {lab}"})
    for f in V["flagged"]:
        out.append({"key": f"flag:{f['image']}", "image": os.path.join(IMG, f["image"]), "scene": f["scene"],
                    "labels": {r: "틀림" for r in f["rules"]}, "source": f["source"]})
    finals = [(sid, D.load(sid)["approved"]["final"]["image"]) for sid in sorted(x[:-5] for x in os.listdir(os.path.join(HERE, "scenes")))
              if "image" in (D.load(sid).get("approved") or {}).get("final", {})]
    finals.append(("authored-david-en-gedi-saul", "samples/engedi-final/approved-engedi-c.png"))
    for sid, p in finals:
        img = p if os.path.isabs(p) else os.path.join(HERE, p)
        out.append({"key": f"approved:{sid}", "image": img, "scene": sid, "labels": {q["id"]: "맞음" for q in questions(sid)},
                    "source": "사람 승인 최종"})
    return out


def load():
    return json.load(open(METRICS, encoding="utf-8")) if os.path.exists(METRICS) else {"answers": {}}


def save(m):
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    with open(METRICS, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=1)


def ask(m, it, rep):
    qs = questions(it["scene"])
    spec = D.load(it["scene"])
    tag = hashlib.sha1(it["key"].encode()).hexdigest()[:10]
    x = {"key": it["key"], "task": tag, "scene": it["scene"], "title": spec["title"], "range": spec["verses"]["range"], "seed": 0,
         "src": it["image"], "qs": qs, "qids": [q["id"] for q in qs]}
    d, files = J.prepare(x, "plausibility")
    text = J.prompt(x, files, HEADER)
    got, tries = None, []
    for _ in range(2):
        o = J.call(text, d, "sonnet")
        tries.append(J.use(o) | {"error": bool(o.get("is_error"))})
        got = None if o.get("is_error") else J.parse(o.get("result"), x["qids"])
        if got:
            break
    with LOCK:
        m["answers"].setdefault(it["key"], {})[str(rep)] = {"tries": tries, **(got or {"answers": None})}
        save(m)


def validate(workers=8):
    m = load()
    todo = [(it, r) for it in items() for r in range(1, FX["reps"] + 1)
            if not ((m["answers"].get(it["key"]) or {}).get(str(r)) or {}).get("answers")]
    for it in items():
        assert os.path.exists(it["image"]), it["image"]
    print(f"[Plausibility] 판정 {len(todo)}건", flush=True)
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda job: ask(m, *job), todo))


def maj(m, key, rid):
    v = [(r.get("answers") or {}).get(rid) for _, r in sorted((m["answers"].get(key) or {}).items())]
    return None if None in v or not v else ("틀림" if v.count("틀림") * 2 > len(v) else "맞음")


def score(m):
    """규칙마다 (잡음, 지적 수, 헛경보, 결함 없음 수) — 엔게디 지적 그림은 묶음(blade) 중 하나라도 틀림이면 잡음."""
    its, s = items(), {r: [0, 0, 0, 0] for r in RULES}
    group = [r["id"] for r in FX["rules"] if r.get("group") == FX["validate"]["engedi_hand"]["group"]]
    for it in its:
        if it.get("group_label") == "틀림":
            asked = [g for g in group if g in {q["id"] for q in questions(it["scene"])}]
            hit = any(maj(m, it["key"], g) == "틀림" for g in asked)
            for g in asked:
                s[g][1] += 1
                s[g][0] += hit
        for rid, lab in it["labels"].items():
            v = maj(m, it["key"], rid)
            if lab == "틀림":
                s[rid][1] += 1
                s[rid][0] += v == "틀림"
            else:
                s[rid][3] += 1
                s[rid][2] += v == "틀림"
    return s


def decide(s):
    A, out = FX["adopt"], {}
    for rid, (c, n, fa, k) in s.items():
        far = fa / k if k else None
        if n:
            out[rid] = "채택" if c / n >= A["catch"] and far is not None and far <= A["false_alarm"] else "미채택"
        else:
            out[rid] = "기록만" if far is not None and far <= A["always_false_alarm"] else "미채택"
    return out


def report():
    m = load()
    s = score(m)
    dec = decide(s)
    for rid, (c, n, fa, k) in s.items():
        print(f"{rid:15} 잡음 {c}/{n}  헛경보 {fa}/{k}  → {dec[rid]}")
    print("채택: " + (" · ".join(r for r, d in dec.items() if d == "채택") or "없음"))


def check():
    m, err = load(), []
    for it in items():
        for r in range(1, FX["reps"] + 1):
            if not ((m["answers"].get(it["key"]) or {}).get(str(r)) or {}).get("answers"):
                err.append(f"답 없음 {it['key']} 회차 {r}")
    dec = decide(score(m))
    want = sorted(r for r, d in dec.items() if d == "채택")
    if not err and sorted(adopted()) != want:
        err.append(f"노트 채택 줄 {adopted()} ≠ 다시 셈 {want}")
    print("ok" if not err else "\n".join(err[:20]))
    return not err


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    fn = {"validate": validate, "report": report, "check": check}.get(cmd)
    if not fn:
        sys.exit(__doc__)
    r = fn()
    if cmd == "check":
        sys.exit(0 if r else 1)
