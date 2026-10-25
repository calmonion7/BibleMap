#!/usr/bin/env python3
"""task 421 — 곁 장면 합성 그림의 기계 판정(단계 ③): 큰 장면 문항은 합성 그림(구름 포함)에, 곁 장면 문항은 곁 장면 원본에 묻는다.

  python3 batch/inset_judge.py judge    # 시드 × (큰 장면 M · 곁 장면 I) × reps — claude -p Sonnet · 머리말 v2 · 답 없는 문항만(문항을 바꾸면 그것만)
  python3 batch/inset_judge.py report   # 장마다 다수결 · 문항별 맞음 수 · `통과: N/8` 줄(「record」 기록 문항은 셈에서 뺌 — judge_items.gating)
  python3 batch/inset_judge.py check    # 답 빠짐 0 · 노트 `통과:` 줄 = 다시 셈 → ok
  python3 batch/inset_judge.py page <out.html>   # 사람 판정 화면(단계 ④) — 8장 전부(통과 + 기계 불통과 표본) · 12:24-25 원문 · 답 복사
  python3 batch/inset_judge.py record '<판정 task 421 + JSON 한 줄>'   # 사람 답 → 노트 「- 사람 답(8시드)」 줄

문항·시드는 notes/BIRTH-INSET.md 「```json fixed 421」 절. 그림은 batch/inset_try.py(gen·comp)가 만든 것.
판정 부품은 gibeah_redraw와 같다(judge_items.prepare/prompt/call/parse)."""
import json, os, re, sys, threading
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "batch"))
import derive_scene as D
import judge_items as J

NOTES = os.path.join(HERE, "notes", "BIRTH-INSET.md")
with open(NOTES, encoding="utf-8") as _fh:
    FX = json.loads(re.search(r"```json fixed 421\n(.*?)\n```", _fh.read(), re.S).group(1))
MAIN = FX["main"]
SUB = D.load(MAIN)["inset"]["spec"]
METRICS = os.path.join(HERE, "samples", FX["dir"], "metrics.json")
QS = {"M": FX["main_qs"], "I": FX["inset_qs"]}
LOCK = threading.Lock()


def img(kind, s):
    """큰 장면 문항 = 합성 그림(구름 자리·다른 때까지 봄) · 곁 장면 문항 = 곁 장면 원본(줄이기 전 화소)."""
    if kind == "M":
        return os.path.join(HERE, "samples", FX["dir"], f"comp-s{s}.png")
    return os.path.expanduser(f"~/.local/biblemap-imggen/{FX['dir']}/{SUB}-s{s}.png")


def load():
    return json.load(open(METRICS, encoding="utf-8")) if os.path.exists(METRICS) else {"answers": {}}


def save(m):
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    with open(METRICS, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=1)


def missing(m, s, kind, rep):
    """그 회차에 답이 없는 문항 — 문항을 바꾸거나 더하면(task 422) 그 문항만 다시 묻는다."""
    got = (((m["answers"].get(f"s{s}") or {}).get(kind) or {}).get(str(rep)) or {}).get("answers") or {}
    return [q["id"] for q in QS[kind] if q["id"] not in got]


def ask(m, s, kind, rep, qids):
    sid = MAIN if kind == "M" else SUB
    spec = D.load(sid)
    it = {"key": f"{kind}:{s}", "task": "inset-421", "scene": sid, "title": spec["title"], "range": spec["verses"]["range"],
          "seed": s, "src": img(kind, s), "qs": [dict(q) for q in QS[kind]], "qids": qids}
    d, files = J.prepare(it, "inset-421")
    text = J.prompt(it, files, J.HEADERS["v2"])
    got, tries = None, []
    for _ in range(2):
        o = J.call(text, d, "sonnet")
        tries.append(J.use(o) | {"error": bool(o.get("is_error"))})
        got = None if o.get("is_error") else J.parse(o.get("result"), it["qids"])
        if got:
            break
    with LOCK:
        old = m["answers"].setdefault(f"s{s}", {}).setdefault(kind, {}).get(str(rep)) or {}
        if not got:
            old.setdefault("answers", None)
        else:
            old["answers"] = (old.get("answers") or {}) | got["answers"]
            old["reasons"] = (old.get("reasons") or {}) | got["reasons"]
        old["tries"] = old.get("tries", []) + tries
        m["answers"][f"s{s}"][kind][str(rep)] = old
        save(m)


def judge(workers=8):
    m = load()
    todo = [(s, k, r, missing(m, s, k, r)) for s in FX["seeds"] for k in QS for r in range(1, FX["reps"] + 1)]
    todo = [t for t in todo if t[3]]
    print(f"[InsetJudge] 판정 {len(todo)}건 · 문항 {sum(len(t[3]) for t in todo)}", flush=True)
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda job: ask(m, *job), todo))


def votes(m, s, kind, qid):
    return [(r.get("answers") or {}).get(qid) for _, r in sorted((m["answers"].get(f"s{s}") or {}).get(kind, {}).items())]


def maj(v):
    return "맞음" if v.count("맞음") * 2 > len(v) else "틀림"


def fails(m, s):
    return [f"{k}/{q['id']}" for k in QS for q in J.gating(QS[k]) if maj(votes(m, s, k, q["id"])) == "틀림"]


def conclude(m):
    ok = [s for s in FX["seeds"] if not fails(m, s)]
    return f"{len(ok)}/{len(FX['seeds'])}" + (f" ({', '.join(f's{s}' for s in ok)})" if ok else "")


def report():
    m = load()
    for k, name in (("M", "큰 장면"), ("I", "곁 장면")):
        print(f"{name}: " + " · ".join(f"{q['q']}{'(기록)' if q.get('record') else ''} {sum(maj(votes(m, s, k, q['id'])) == '맞음' for s in FX['seeds'])}" for q in QS[k]))
    for s in FX["seeds"]:
        print(f"s{s}: 틀림 {len(fails(m, s))} {' '.join(fails(m, s))}")
    print(f"통과: {conclude(m)}")


def check():
    m, err = load(), []
    for s in FX["seeds"]:
        for k in QS:
            if not os.path.exists(img(k, s)):
                err.append(f"그림 없음 {k} s{s}")
            for q in QS[k]:
                v = votes(m, s, k, q["id"])
                if len(v) != FX["reps"] or None in v:
                    err.append(f"s{s} {k}/{q['id']} 답 {v}")
    line = re.findall(r"^통과: (.+)$", open(NOTES, encoding="utf-8").read(), re.M)
    if not err and line != [conclude(m)]:
        err.append(f"노트 통과 줄 {line} ≠ 다시 셈 {conclude(m)}")
    print("ok" if not err else "\n".join(err[:20]))
    return not err


def page(out):
    """폰용 한 질문 화면 — 그림은 자리표 @@IMG@@ 없이 JSON 덩어리로 맨 끝에 넣는다(417 판 1: 원문 자리표 치환이 그림 base64까지 바꿈)."""
    import base64, io
    from PIL import Image
    m = load()
    verses = json.load(open(os.path.join(HERE, "..", "..", "data", "bible", "verses.json"), encoding="utf-8"))
    rows = []
    for v in (24, 25):
        txt = verses[f"10012{v:03d}"]["textKo"].strip()
        rows.append(f'<p><span class="ref">12:{v}</span>{"<b>" + txt + "</b>" if f"12:{v}" in FX["bold"] else txt}</p>')
    qname = {f"{k}/{q['id']}": q["q"] for k in QS for q in QS[k]}
    cards = [{"seed": s, "pass": not fails(m, s), "fails": [("곁 " if f.startswith("I/") else "") + qname[f] for f in fails(m, s)]} for s in FX["seeds"]]
    cards.sort(key=lambda c: (not c["pass"], len(c["fails"]), FX["seeds"].index(c["seed"])))

    def uri(path, w):
        im = Image.open(path).convert("RGB")
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=88)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    imgs = {f"comp-{s}": uri(img("M", s), 1216) for s in FX["seeds"]} | {f"inset-{s}": uri(img("I", s), 896) for s in FX["seeds"]}
    tpl = open(os.path.join(HERE, "batch", "inset_judge_page.html"), encoding="utf-8").read()
    html = tpl.replace("@@VERSES@@", "".join(rows)).replace("/*CARDS*/[]", json.dumps(cards, ensure_ascii=False))
    html = html.replace("/*IMGS*/{}", json.dumps(imgs))   # 그림은 마지막에
    open(out, "w", encoding="utf-8").write(html)
    print(f"[InsetJudge] 화면 {out} {len(html) / 1e6:.2f}MB · 통과 {sum(c['pass'] for c in cards)}/{len(cards)}")


def record(text):
    v = json.loads(text.split("\n", 1)[1].strip().splitlines()[0])
    m = load()
    m["verdict"] = v
    save(m)
    line = f"- 사람 답(8시드): {v['pick']}" + (f" · 메모 「{v['memo']}」" if v.get("memo") else "")
    with open(NOTES, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(f"[InsetJudge] {line}")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] in ("page", "record"):
        {"page": page, "record": record}[sys.argv[1]](sys.argv[2])
        sys.exit(0)
    fn = {"judge": judge, "report": report, "check": check}.get(sys.argv[1] if len(sys.argv) > 1 else "")
    if not fn:
        sys.exit(__doc__)
    r = fn()
    if fn is check:
        sys.exit(0 if r else 1)
