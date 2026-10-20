#!/usr/bin/env python3
"""task#374 — 구독 `claude -p` 기계 판정자 시험: 사람이 본 장면 요소 문항을 그림마다 한 번에 묻고 사람 라벨과 견준다.

  python3 batch/judge_items.py run --set dev --key r1 --header v1 --model sonnet [--limit 1] [--workers 4]
  python3 batch/judge_items.py run --set holdout --key sonnet --header v2 --model sonnet
  python3 batch/judge_items.py score            # 원 답 → metrics 요약 + notes/JUDGE-ITEMS.md 결과 절
  python3 batch/judge_items.py score --check    # 다시 계산해 metrics·notes와 대조(손 집계 방지) — 다르면 exit 1

규칙은 notes/JUDGE-ITEMS.md 고정 절. 문항은 사람이 본 페이지 HTML의 SCENES JSON에서(.identity·판 묶음 제외),
그림은 368 편집본·나머지 바탕, 인물 문항은 페이지 크롭 상자로 자른 몸 크롭을 함께. 그림·크롭은 레포 밖
~/.local/biblemap-imggen/judge-items/<묶음>/<과제>-<장면>-s<시드>/, 답·사용량은 samples/judge-items/metrics.json에 그림마다 바로."""
import argparse, json, os, re, subprocess, sys, threading
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = os.path.expanduser("~/.local/biblemap-imggen/pages")
WORK = os.path.expanduser("~/.local/biblemap-imggen/judge-items")
METRICS = os.path.join(HERE, "samples", "judge-items", "metrics.json")
NOTES = os.path.join(HERE, "notes", "JUDGE-ITEMS.md")
# 과제 → (samples 폴더, 사람 페이지, 그림 = 편집본?)
TASKS = {368: ("night-pilot", "night-pick.html", True), 369: ("whole-fix", "whole-fix-pick.html", False),
         370: ("whole-wide", "whole-wide-pick.html", False), 372: ("jabesh-crowd", "jabesh-crowd-pick.html", False)}
SETS = {"dev": (368, 369), "holdout": (370, 372)}
CLASSES = ("moment", "background", "crowds", "pose", "prop", "facing", "guard")
PASS_LINE = 0.8
BEGIN, END = "<!-- score:begin -->", "<!-- score:end -->"

HEADERS = {
    "v1": """너는 성경 장면 그림의 검수자다. Read 도구로 아래 그림 파일을 모두 열어 본 뒤, 문항마다 그 항목이 이 그림에서 틀렸는지 판정하라.
- 「기대」가 그림에 분명히 보이면 「맞음」, 빠졌거나 다르게 그려졌거나 알아볼 수 없으면 「틀림」.
- 인물 문항은 그 인물의 몸 크롭 파일을 함께 본다(크롭 가운데 인물이 그 사람이다).
- 방향의 「화면 왼쪽/오른쪽」은 보는 사람 기준이다.
- 가드 문항은 다른 문항에서 묻지 않은 결함(손가락 수 이상, 두 겹·덧붙은 인물, 종이 테두리·액자, 글자)이 하나라도 보이면 「틀림」.
- 출력은 JSON 하나만: {"answers": {"<문항 id>": "맞음" 또는 "틀림", ...}, "reasons": {"<문항 id>": "짧은 이유", ...}}""",
    # r1(잡기 58%·통과 91%) 뒤: 기계가 「대상이 있다」에서 멈추고 수식어·관계·쥔 방식을 안 봄 → 엄격하게
    "v2": """너는 성경 장면 그림을 깐깐하게 검수하는 미술 감독이다. 같은 장면을 여러 장 뽑아 결함 있는 장을 골라내는 중이다. Read 도구로 아래 그림 파일을 모두 열어 본 뒤, 문항마다 그 항목이 이 그림에서 틀렸는지 판정하라.
- 「기대」 문장의 **모든** 낱말이 그림에 맞아야 「맞음」이다. 대상이 있어도 수식어(크기·상태·수·위치), 쥐거나 지닌 방식, 행동, 인물 사이 관계 중 하나라도 어긋나면 「틀림」. 예: 「작은 수금」인데 몸통만 한 하프 → 틀림. 「겉옷자락을 붙잡음」인데 따로 떨어진 천 조각만 쥠 → 틀림. 무리가 「애곡함」·「둘러섬」·「흩어짐」인데 그냥 줄지어 서 있음 → 틀림.
- 장면 뜻(moment)은 인물들의 관계와 동작이 그 순간의 이야기를 말하는지 본다. 누가 누구를 향하는지, 다가가는지 떠나는지가 뜻과 다르면 틀림(예: 무리를 뒤로하고 떠나야 하는데 무리와 마주 봄).
- 지물은 그 시대 사람이 그 장면에서 지닐 모양과 방식인지까지 본다(칼을 차야 할 장면에서 뽑아 들었거나, 현대식 물건이면 틀림).
- 인물 문항은 그 인물의 몸 크롭 파일을 함께 본다(크롭 가운데 인물이 그 사람이다). 방향의 「화면 왼쪽/오른쪽」은 보는 사람 기준이고, 얼굴과 상체가 향한 쪽을 본다.
- 가드 문항은 다른 문항에서 묻지 않은 결함(손가락 수 이상, 두 겹·덧붙은 인물, 종이 테두리·액자, 글자)이 하나라도 보이면 「틀림」.
- 분명히 맞다고 확인되지 않으면 「틀림」으로 답한다.
- 출력은 JSON 하나만: {"answers": {"<문항 id>": "맞음" 또는 "틀림", ...}, "reasons": {"<문항 id>": "짧은 이유", ...}}""",
}


def page_scenes(fn):
    t = open(os.path.join(PAGES, fn), encoding="utf-8").read()
    i = t.index("const SCENES")
    return json.JSONDecoder().raw_decode(t[t.index("=", i) + 1:].lstrip())[0]


def cls(qid):
    return qid.split(".")[-1] if "." in qid else re.sub(r"\[\d+\]$", "", qid)


def items(set_name):
    """→ 그림 목록 [{key, task, scene, title, range, seed, src, qs, labels}] — 문항·라벨은 사람 페이지·metrics 그대로."""
    out = []
    for task in SETS[set_name]:
        d, fn, edited = TASKS[task]
        m = json.load(open(os.path.join(HERE, "samples", d, "metrics.json")))
        for s in page_scenes(fn):
            sc = m["scenes"][s["id"]]
            qs = [q for q in s["qs"] if not q["id"].endswith(".identity") and q.get("grp") != "plate"]
            by = {x["seed"]: x for x in sc["seeds"]}
            for seed in s["seeds"]:
                x = by[seed]
                labels = {q["id"]: ("틀림" if seed in sc["items"][q["id"]]["wrong"] else "맞음")
                          for q in qs if not sc["items"][q["id"]].get("unsure")}
                out.append({"key": f"{task}:{s['id']}:{seed}", "task": task, "scene": s["id"], "title": s["title"], "range": s["range"],
                            "seed": seed, "src": x["edits"][sc["who"][-1]] if edited else x["base"], "qs": qs, "labels": labels,
                            "unsure": sum(1 for q in qs if sc["items"][q["id"]].get("unsure"))})
    return out


def prepare(it, set_name):
    """그림 폴더에 full.jpg + 인물마다 몸 크롭 <who>.jpg → (폴더, 파일 목록)."""
    d = os.path.join(WORK, set_name, f"{it['task']}-{it['scene']}-s{it['seed']}")
    os.makedirs(d, exist_ok=True)
    im = Image.open(it["src"]).convert("RGB")
    files = {"full": os.path.join(d, "full.jpg")}
    if not os.path.exists(files["full"]):
        im.save(files["full"], quality=92)
    for q in it["qs"]:
        who = q.get("who")
        if not who or who in files:
            continue
        x, y, w, h = q["crop"][str(it["seed"])]
        p = os.path.join(d, f"{who}.jpg")
        if not os.path.exists(p):
            W, H = im.size
            im.crop((round(x * W), round(y * H), round((x + w) * W), round((y + h) * H))).save(p, quality=92)
        files[who] = p
    return d, files


def prompt(it, files, header):
    lines = [header, "", f"장면: {it['title']} ({it['range']})", f"전체 그림: {files['full']}"]
    lines += [f"{q['who']} 몸 크롭: {files[q['who']]}" for q in it["qs"] if q.get("who") and q["id"].endswith(".pose")]
    lines += ["", "문항:"]
    for q in it["qs"]:
        if q["id"] not in it["labels"]:
            continue
        who = f" · 크롭 {q['who']}" if q.get("who") else ""
        verse = f" · 근거 {q['verse']}" if q.get("verse") else ""
        lines.append(f"- {q['id']}{who}: {q['q']} — 기대: {q['what']}{verse}")
    return "\n".join(lines)


def call(text, d, model):
    cmd = ["claude", "-p", text, "--model", model, "--output-format", "json", "--allowedTools", "Read", "--add-dir", d,
           "--no-session-persistence", "--strict-mcp-config", "--disable-slash-commands"]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=d, timeout=600)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"is_error": True, "result": (r.stdout + r.stderr)[-500:]}


def parse(txt, want):
    m = re.search(r"\{.*\}", txt or "", re.S)
    try:
        d = json.loads(m.group(0)) if m else None
    except json.JSONDecodeError:
        return None
    a = (d or {}).get("answers")
    if not isinstance(a, dict) or any(a.get(k) not in ("맞음", "틀림") for k in want):
        return None
    return {"answers": {k: a[k] for k in want}, "reasons": d.get("reasons", {})}


def use(o):
    u = o.get("usage") or {}
    return {"seconds": (o.get("duration_ms") or 0) / 1000, "input": u.get("input_tokens", 0), "output": u.get("output_tokens", 0),
            "cache_read": u.get("cache_read_input_tokens", 0), "cache_create": u.get("cache_creation_input_tokens", 0),
            "cost_usd": o.get("total_cost_usd") or 0, "turns": o.get("num_turns") or 0}


def load():
    return json.load(open(METRICS)) if os.path.exists(METRICS) else {}


def save(m):
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    tmp = METRICS + ".tmp"
    json.dump(m, open(tmp, "w"), ensure_ascii=False, indent=1)
    os.replace(tmp, METRICS)


def run(a):
    m, lock = load(), threading.Lock()
    r = m.setdefault(a.set, {}).setdefault(a.key, {"model": a.model, "header": a.header, "answers": {}})
    assert (r["model"], r["header"]) == (a.model, a.header), f"{a.set}/{a.key}는 {r['model']}·{r['header']}로 이미 시작함"
    m.setdefault("headers", {})[a.header] = HEADERS[a.header]
    todo = [it for it in items(a.set) if it["key"] not in r["answers"]][: a.limit or None]
    print(f"[JudgeItems] {a.set}/{a.key} {a.model}·{a.header} — 남은 그림 {len(todo)}", flush=True)

    def one(it):
        d, files = prepare(it, a.set)
        text, tries, got = prompt(it, files, HEADERS[a.header]), [], None
        for _ in range(2):   # JSON이 깨지면 한 번만 다시
            o = call(text, d, a.model)
            tries.append(use(o) | {"error": bool(o.get("is_error"))})
            got = None if o.get("is_error") else parse(o.get("result"), list(it["labels"]))
            if got:
                break
        rec = {"tries": tries, "raw": None if got else str(o.get("result"))[:400], **(got or {"answers": None})}
        with lock:
            r["answers"][it["key"]] = rec
            save(m)
        print(f"[JudgeItems] {it['key']} {'ok' if got else '답 없음'} · 시도 {len(tries)} · {sum(t['seconds'] for t in tries):.0f}초", flush=True)

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(one, todo))


def summarize(set_name, r):
    """원 답 → 요약(잡기·통과·부류별·8/8 칸·쏠림·사용량). 호출한 그림만 세고, 답 없음(실패 호출)은 라벨 반대로 셈."""
    its = [it for it in items(set_name) if it["key"] in r["answers"]]
    hits = {"틀림": [0, 0], "맞음": [0, 0]}
    by = {c: {"틀림": [0, 0], "맞음": [0, 0]} for c in CLASSES}
    machine_wrong, cells = 0, {}
    for it in its:
        ans = r["answers"][it["key"]]["answers"]
        for qid, lab in it["labels"].items():
            pred = ans[qid] if ans else ("맞음" if lab == "틀림" else "틀림")
            ok = pred == lab
            hits[lab][0] += ok
            hits[lab][1] += 1
            by[cls(qid)][lab][0] += ok
            by[cls(qid)][lab][1] += 1
            machine_wrong += pred == "틀림"
            c = cells.setdefault(f"{it['task']}:{it['scene']}:{qid}", [0, 0, 0])   # [사람 틀림, 장 수, 기계도 틀림]
            c[0] += lab == "틀림"
            c[1] += 1
            c[2] += lab == "틀림" and pred == "틀림"
    rec = [r["answers"][it["key"]] for it in its]
    tries = [t for x in rec for t in x["tries"]]
    full = [k for k, c in cells.items() if c[0] == c[1]]
    n = hits["틀림"][1] + hits["맞음"][1]
    return {"n": n, "unsure_skipped": sum(it["unsure"] for it in its), "images": len(its), "calls": len(rec),
            "retries": len(tries) - len(rec), "failed": sum(1 for x in rec if x["answers"] is None),
            "catch": round(hits["틀림"][0] / hits["틀림"][1], 4), "pass": round(hits["맞음"][0] / hits["맞음"][1], 4),
            "machine_wrong_rate": round(machine_wrong / n, 4),
            "by_class": {c: {"catch": f"{v['틀림'][0]}/{v['틀림'][1]}", "pass": f"{v['맞음'][0]}/{v['맞음'][1]}"}
                         for c, v in by.items() if v["틀림"][1] + v["맞음"][1]},
            "full_wrong_cells": {"n": len(full), "caught_all": sum(1 for k in full if cells[k][2] == cells[k][1]),
                                 "missed": [k for k in full if cells[k][2] < cells[k][1]]},
            "usage": {k: round(sum(t[k] for t in tries), 4) for k in ("seconds", "input", "output", "cache_read", "cache_create", "cost_usd")}}


def verdict(m):
    h = m.get("holdout", {})
    ok = lambda k: k in h and h[k]["summary"]["catch"] >= PASS_LINE and h[k]["summary"]["pass"] >= PASS_LINE
    if ok("sonnet"):
        return "합격 (Sonnet)"
    if "opus" in h:
        return "합격 (Opus)" if ok("opus") else "불합격"
    return None


def pct(x):
    return f"{x * 100:.1f}%"


def table(m):
    rows = ["| 묶음/회 | 모델·문구 | 라벨 | 잡기 | 통과 | 기계 틀림 비율 | 8/8 칸 다 잡음 | 호출(재시도·실패) | 초 | 입력·캐시읽기·출력 토큰 | cost_usd(참고) |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    cls_rows = ["| 묶음/회 | " + " | ".join(CLASSES) + " |", "|---|" + "---|" * len(CLASSES)]
    for s in ("dev", "holdout"):
        for k, r in m.get(s, {}).items():
            x, u = r["summary"], r["summary"]["usage"]
            rows.append(f"| {s}/{k} | {r['model']}·{r['header']} | {x['n']} | {pct(x['catch'])} | {pct(x['pass'])} | {pct(x['machine_wrong_rate'])} | "
                        f"{x['full_wrong_cells']['caught_all']}/{x['full_wrong_cells']['n']} | {x['calls']}({x['retries']}·{x['failed']}) | {u['seconds']:.0f} | "
                        f"{u['input']:.0f}·{u['cache_read']:.0f}·{u['output']:.0f} | {u['cost_usd']:.2f} |")
            cls_rows.append(f"| {s}/{k} | " + " | ".join(f"잡기 {x['by_class'][c]['catch']} · 통과 {x['by_class'][c]['pass']}" if c in x["by_class"] else "—"
                                                    for c in CLASSES) + " |")
    v = verdict(m)
    head = [f"판정: {v}" if v else "판정 보류: 검증 묶음 미완(Sonnet 불합격이면 Opus 대기)", ""]
    return "\n".join(head + rows + ["", "문항 부류별(맞힌 수/라벨 수):", ""] + cls_rows)


def score(a):
    m = load()
    fresh = {s: {k: summarize(s, r) for k, r in m.get(s, {}).items()} for s in ("dev", "holdout")}
    if a.check:
        bad = [f"{s}/{k}" for s in fresh for k, x in fresh[s].items() if m[s][k].get("summary") != x]
        cur = {s: {k: {**r, "summary": fresh[s][k]} for k, r in m.get(s, {}).items()} for s in ("dev", "holdout")}
        notes = open(NOTES, encoding="utf-8").read()
        block = notes[notes.index(BEGIN) + len(BEGIN): notes.index(END)].strip() if BEGIN in notes else ""
        if block != table({**m, **cur}):
            bad.append("notes 결과 표")
        print(f"[JudgeItems] score --check {'불일치: ' + ', '.join(bad) if bad else '일치'}", flush=True)
        sys.exit(1 if bad else 0)
    for s in fresh:
        for k, x in fresh[s].items():
            m[s][k]["summary"] = x
    save(m)
    notes = open(NOTES, encoding="utf-8").read()
    block = f"{BEGIN}\n{table(m)}\n{END}"
    notes = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), lambda _: block, notes, flags=re.S) if BEGIN in notes else notes.rstrip() + "\n\n## 결과\n\n" + block + "\n"
    open(NOTES, "w", encoding="utf-8").write(notes)
    print(table(m), flush=True)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--set", choices=SETS, required=True)
    r.add_argument("--key", required=True)
    r.add_argument("--header", choices=HEADERS, required=True)
    r.add_argument("--model", required=True)
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--workers", type=int, default=4)
    s = sub.add_parser("score")
    s.add_argument("--check", action="store_true")
    a = p.parse_args()
    run(a) if a.cmd == "run" else score(a)


if __name__ == "__main__":
    main()
