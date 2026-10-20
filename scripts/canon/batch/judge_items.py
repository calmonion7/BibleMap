#!/usr/bin/env python3
"""task#374 — 구독 `claude -p` 기계 판정자 시험: 사람이 본 장면 요소 문항을 그림마다 한 번에 묻고 사람 라벨과 견준다.

  python3 batch/judge_items.py run --set dev --key r1 --header v1 --model sonnet [--limit 1] [--workers 4]
  python3 batch/judge_items.py run --set holdout --key sonnet --header v2 --model sonnet
  python3 batch/judge_items.py run --set oddity --key O1 --header o1 --model sonnet   # 이상한 점(task 378) 라벨 칸
  python3 batch/judge_items.py score            # 원 답 → metrics 요약 + notes/JUDGE-ITEMS.md 결과 절
  python3 batch/judge_items.py score --check    # 다시 계산해 metrics·notes와 대조(손 집계 방지) — 다르면 exit 1

규칙은 notes/JUDGE-ITEMS.md 고정 절. 문항은 사람이 본 페이지 HTML의 SCENES JSON에서(.identity·판 묶음 제외),
그림은 368 편집본·나머지 바탕, 인물 문항은 페이지 크롭 상자로 자른 몸 크롭을 함께. 그림·크롭은 레포 밖
~/.local/biblemap-imggen/judge-items/<묶음>/<과제>-<장면>-s<시드>/, 답·사용량은 samples/judge-items/metrics.json에 그림마다 바로."""
import argparse, fcntl, json, os, re, subprocess, sys, threading
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = os.path.expanduser("~/.local/biblemap-imggen/pages")
WORK = os.path.expanduser("~/.local/biblemap-imggen/judge-items")
METRICS = os.path.join(HERE, "samples", "judge-items", "metrics.json")
NOTES = os.path.join(HERE, "notes", "JUDGE-ITEMS.md")
# 과제 → (samples 폴더, 사람 페이지, 그림 = 편집본?)
TASKS = {368: ("night-pilot", "night-pick.html", True), 369: ("whole-fix", "whole-fix-pick.html", False),
         370: ("whole-wide", "whole-wide-pick.html", False), 372: ("jabesh-crowd", "jabesh-crowd-pick.html", False),
         376: ("verse-regen", "verse-regen-pick.html", False)}   # 376: 문항 페이지는 J1용, 사람은 후보 화면(make_cand_page)
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
    # J1(후속 시험): 지물 문항만 묻는 호출 — 몸 크롭을 키워 넘기고, 판정 전에 지물을 먼저 적게 한다
    "p1": """너는 성경 장면 그림의 지물(손에 든 것·몸에 지닌 것)을 검수하는 미술 감독이다. Read 도구로 아래 그림 파일을 모두 연다. 몸 크롭은 그 인물을 크게 키운 그림이다.
문항마다 먼저 그 인물이 실제로 들거나 지닌 물건을 적는다 — 무엇인지, 크기(몸과 견주어), 모양, 쥔 방식(손에 쥠·허리에 참·어깨에 멤), 싸였는지. 그다음 「기대」와 견준다.
- 기대한 물건이 그 모양·크기·쥔 방식으로 분명히 보이면 「맞음」.
- 물건이 없거나, 다른 물건이거나, 크기·모양·쥔 방식·싸임이 기대와 다르면 「틀림」(예: 「작은 수금」인데 몸통만 한 하프, 「보자기에 싼 큰 칼」인데 칼 모양이 안 보이는 작은 꾸러미, 차야 할 칼을 뽑아 듦).
- 출력은 JSON 하나만: {"answers": {"<문항 id>": "맞음" 또는 "틀림", ...}, "reasons": {"<문항 id>": "실제로 본 물건 — 판정 이유", ...}}""",
    # J1 p1(지물 잡기 41~52%)이 너그러워짐 → v2의 엄격함 + 키운 크롭 + 지물만
    "p2": """너는 성경 장면 그림을 깐깐하게 검수하는 미술 감독이다. 같은 장면을 여러 장 뽑아 결함 있는 장을 골라내는 중이다. Read 도구로 아래 그림 파일을 모두 연다. 몸 크롭은 그 인물을 크게 키운 그림이다.
문항마다 그 인물의 지물(손에 든 것·몸에 지닌 것)이 이 그림에서 틀렸는지 판정하라.
- 「기대」 문장의 **모든** 낱말이 그림에 맞아야 「맞음」이다. 물건이 있어도 크기, 모양, 쥐거나 지닌 방식, 싸임 여부 중 하나라도 어긋나면 「틀림」. 예: 「작은 수금」인데 몸통만 한 하프 → 틀림. 「보자기에 싼 칼」인데 칼 모양이 안 보이는 꾸러미 → 틀림.
- 지물은 그 시대 사람이 그 장면에서 지닐 모양과 방식인지까지 본다(칼을 차야 할 장면에서 뽑아 들었거나, 현대식 물건이면 틀림).
- 분명히 맞다고 확인되지 않으면 「틀림」으로 답한다.
- 출력은 JSON 하나만: {"answers": {"<문항 id>": "맞음" 또는 "틀림", ...}, "reasons": {"<문항 id>": "짧은 이유", ...}}""",
    # J1: 무리 문항만 묻는 호출 — 무리가 하는 일을 먼저 적고, 기대와 다른 점이 있을 때만 틀림(엄격 문구가 맞는 무리를 무너뜨렸다)
    "c1": """너는 성경 장면 그림의 무리(배경의 여러 사람)를 검수하는 미술 감독이다. Read 도구로 전체 그림을 연다.
문항마다 먼저 그림 속 무리를 적는다 — 어디에 있는지, 대략 몇 명인지, 무엇을 하고 있는지(서 있음·앉음·걸음·달아남·둘러섬 등), 어느 쪽을 향하는지. 그다음 「기대」와 견준다.
- 적은 무리가 기대와 **다른 점**(무리가 없음, 행동이 다름, 자리가 다름, 방향이 반대)이 있을 때만 「틀림」.
- 작고 멀어 세부가 흐릿한 것은 틀림이 아니다. 기대와 어긋나는 것이 보일 때만 틀림으로 한다.
- 출력은 JSON 하나만: {"answers": {"<문항 id>": "맞음" 또는 "틀림", ...}, "reasons": {"<문항 id>": "실제로 본 무리 — 판정 이유", ...}}""",
    # task 378 이상한 점(두 겹 판정 2층): J1 요소 문항과 따로 부르는 문항 하나 — 명세 글 전체에 비춘 신원·역할·이물·상태 어긋남 + 가드 결함
    "o1": """너는 성경 장면 그림을 깐깐하게 검수하는 미술 감독이다. 아래 장면 명세 글을 먼저 읽고, Read 도구로 그림 파일을 모두 연 뒤, 이 그림에 명세에 비추어 **이상한 점**이 있는지 판정하라. 장면 뜻·배경·무리·자세·지물·방향은 다른 검수자가 요소마다 따로 묻는다. 너는 그 요소 목록이 놓치는 어긋남을 본다:
- 신원: 명세의 인물이 그림에서 누구인지 모호하다(누가 그 사람인지 구별되지 않음), 또는 명세에 없는 사람이 행동의 주체로 보인다.
- 역할: 행동을 하는 사람과 받는 사람이 명세와 바뀌었거나, 명세에 없는 사람이 그 행동을 한다.
- 이물: 그 시대에 없는 물건·건물·옷(현대식 건물·철모 등), 덧붙거나 몸이 겹친 사람.
- 상태: 명세가 말한 상태와 다르다(예: 싸여야 할 것이 드러남, 차야 할 칼을 뽑아 듦).
- 가드 결함: 손가락 수 이상, 두 겹 인물, 종이 테두리·액자, 글자.
- 하나라도 있거나, 있는지 없는지 모호하면 「틀림」(이상한 점 있음). 분명히 없을 때만 「맞음」.
- 인물 몸 크롭은 그 인물을 잘라 낸 그림이다(크롭 가운데 인물이 그 사람이다).
- 출력은 JSON 하나만: {"answers": {"oddity": "맞음" 또는 "틀림"}, "reasons": {"oddity": "본 이상한 점(없으면 없음) — 짧게"}}""",
}


def page_scenes(fn):
    t = open(os.path.join(PAGES, fn), encoding="utf-8").read()
    i = t.index("const SCENES")
    return json.JSONDecoder().raw_decode(t[t.index("=", i) + 1:].lstrip())[0]


def cls(qid):
    return qid.split(".")[-1] if "." in qid else re.sub(r"\[\d+\]$", "", qid)


def items(set_name, only=None, tasks=None):
    """→ 그림 목록 [{key, task, scene, title, range, seed, src, qs, labels}] — 문항·라벨은 사람 페이지·metrics 그대로.
    only = 문항 종류 목록(J1 종류별 호출) — 그 종류 문항만 남기고, 남는 문항이 없는 그림은 뺀다."""
    out = []
    if not tasks and set_name not in SETS:   # 「t<과제>」 — 과제 하나(라벨 전 예측 · 함께 판정 화면)
        tasks = [int(set_name[1:])]
    for task in tasks or SETS[set_name]:
        d, fn, edited = TASKS[task]
        if not os.path.exists(os.path.join(PAGES, fn)):   # 생성 중인 과제(문항 페이지 전) — 원장에서 건너뜀
            continue
        m = json.load(open(os.path.join(HERE, "samples", d, "metrics.json")))
        for s in page_scenes(fn):
            sc = m["scenes"][s["id"]]
            qs = [q for q in s["qs"] if not q["id"].endswith(".identity") and q.get("grp") != "plate" and (not only or cls(q["id"]) in only)]
            if not qs:
                continue
            by = {x["seed"]: x for x in sc["seeds"]}
            rec = sc.get("items") or {}   # 사람 판정 전이면 비어 있다 → 라벨 없이 예측만
            # 라벨에서 뺄 칸: 모르겠음 · 장면째 넘김(skipped) · 믿음 관문 자동 결정(auto)
            drop = lambda q: rec.get(q["id"], {}).get("unsure") or rec.get(q["id"], {}).get("skipped") or rec.get(q["id"], {}).get("auto")
            for seed in s["seeds"]:
                x = by[seed]
                # 후보 화면(task 376)은 칸마다 사람이 본 시드(seeds)만 라벨 — 없으면 8시드 전부(368~372)
                labels = {q["id"]: ("틀림" if seed in rec[q["id"]]["wrong"] else "맞음") for q in qs
                          if q["id"] in rec and not drop(q) and seed in rec[q["id"]].get("seeds", s["seeds"])}
                out.append({"key": f"{task}:{s['id']}:{seed}", "task": task, "scene": s["id"], "title": s["title"], "range": s["range"],
                            "seed": seed, "src": x["edits"][sc["who"][-1]] if edited else x["base"], "qs": qs, "labels": labels,
                            "qids": list(labels) if rec else [q["id"] for q in qs],
                            # 기계 표시를 보고 판정한 칸 — 판정자 평가에서는 뺀다(닻 효과), 학습에는 쓴다
                            "premarked": {q for q in labels if rec[q].get("machine") is not None and not rec[q].get("blind")},
                            "unsure": sum(1 for q in qs if rec.get(q["id"], {}).get("unsure"))})
    return out


def oddity_spec(sid):
    """이상한 점 문항에 줄 명세 한국어 — 순간·뜻·관계·배경·무리·인물(역할·자세·지물·몸짓·표정·차림)."""
    s = json.load(open(os.path.join(HERE, "scenes", f"{sid}.json"), encoding="utf-8"))
    ko = lambda v: v.get("ko") if isinstance(v, dict) else v
    lines = [f"순간: {s['moment']['why']}"]
    lines += [f"{n}: {ko(s[k])}" for k, n in (("meaning", "장면 뜻"), ("relation", "관계")) if s.get(k)]
    lines.append(f"배경: {ko(s.get('whole_background')) or ' · '.join(b['what'] for b in s.get('background', []))}")
    lines += [f"무리: {c.get('what')}" for c in s.get("crowds", [])]
    for f in s["figures"]:
        parts = [f"자세 {f.get('pose')}", f"지물 {f.get('prop')}"] + [f"{n} {ko(f[k])}" for k, n in (("gesture", "몸짓"), ("expression", "표정"), ("costume", "차림")) if f.get(k)]
        lines.append(f"인물 {f['cast']} — {f.get('role')}: " + " · ".join(parts))
    return "\n".join(lines)


def oddity_items(set_name):
    """이상한 점 판정 그림 — 「oddity」 = notes/SPEC-JUDGE.md 고정 절의 라벨 칸, 그 밖은 items(set_name) 그대로(예: t376 112장).
    문항은 oddity 하나(「틀림」 = 이상한 점 있음). 인물 크롭은 원래 문항의 크롭 상자를 그대로 쓴다."""
    if set_name == "oddity":
        import judge_spec
        od = judge_spec.fixed()["oddity"]
        keys = set(od["pos"] + od["neg"])
        its = [it for t in sorted({int(k.split(":")[0]) for k in keys}) for it in items(None, tasks=[t]) if it["key"] in keys]
    else:
        its = items(set_name)
    return [{**it, "qids": ["oddity"], "labels": {}, "spec": oddity_spec(it["scene"])} for it in its]


def oddity_prompt(it, files, header):
    lines = [header, "", f"장면: {it['title']} ({it['range']})", "", "장면 명세(그림이 따라야 할 글):", it["spec"], "",
             f"전체 그림: {files['full']}"]
    lines += [f"{w} 몸 크롭: {p}" for w, p in files.items() if w != "full"]
    lines += ["", "문항:", "- oddity: 이 그림에 명세에 비추어 이상한 점이 있는가 — 「맞음」 = 없음, 「틀림」 = 있음"]
    return "\n".join(lines)


def prepare(it, set_name, zoom=1.0):
    """그림 폴더에 full.jpg + 인물마다 몸 크롭 <who>.jpg(zoom ≠ 1이면 키운 <who>-z<zoom>.jpg) → (폴더, 파일 목록)."""
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
        p = os.path.join(d, f"{who}.jpg" if zoom == 1 else f"{who}-z{zoom:g}.jpg")
        if not os.path.exists(p):
            W, H = im.size
            c = im.crop((round(x * W), round(y * H), round((x + w) * W), round((y + h) * H)))
            if zoom != 1:
                c = c.resize((round(c.width * zoom), round(c.height * zoom)), Image.LANCZOS)
            c.save(p, quality=92)
        files[who] = p
    return d, files


def prompt(it, files, header):
    lines = [header, "", f"장면: {it['title']} ({it['range']})", f"전체 그림: {files['full']}"]
    lines += [f"{w} 몸 크롭: {files[w]}" for w in dict.fromkeys(q["who"] for q in it["qs"] if q.get("who"))]
    lines += ["", "문항:"]
    for q in it["qs"]:
        if q["id"] not in it["qids"]:
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
    tmp = f"{METRICS}.{os.getpid()}.tmp"
    json.dump(m, open(tmp, "w"), ensure_ascii=False, indent=1)
    os.replace(tmp, METRICS)


def update(fn):
    """여러 run이 동시에 돌아도 서로의 답을 지우지 않게 — 짧게 잠그고 디스크의 최신 metrics를 다시 읽어 fn(m)만 합쳐 쓴다."""
    os.makedirs(WORK, exist_ok=True)
    with open(os.path.join(WORK, "metrics.lock"), "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        m = load()
        fn(m)
        save(m)
        return m


def run(a):
    # 다른 run과는 동시에 돌 수 있다(답마다 update로 합쳐 씀). 같은 묶음·같은 키 run이 겹치면 같은 그림을 두 번 부르니 그것만 막는다.
    os.makedirs(WORK, exist_ok=True)
    held = open(os.path.join(WORK, f"run-{a.set}-{a.key}.lock"), "w")
    try:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        sys.exit(f"[JudgeItems] {a.set}/{a.key} run이 이미 도는 중")
    only = a.only.split(",") if a.only else None
    meta = {"model": a.model, "header": a.header, "answers": {}, **({"only": only, "zoom": a.zoom} if only else {}), **({"learn": a.learn} if a.learn else {})}

    def start(m):
        r = m.setdefault(a.set, {}).setdefault(a.key, meta)
        assert (r["model"], r["header"], r.get("only")) == (a.model, a.header, only), f"{a.set}/{a.key}는 {r['model']}·{r['header']}·{r.get('only')}로 이미 시작함"
        m.setdefault("headers", {})[a.header] = HEADERS[a.header]
    done = update(start)[a.set][a.key]["answers"]
    tasks = [int(x) for x in a.tasks.split(",")] if a.tasks else None
    odd = a.header == "o1"   # 이상한 점(task 378) — 문항 oddity 하나, 명세 글을 함께
    todo = [it for it in (oddity_items(a.set) if odd else items(a.set, only, tasks)) if it["key"] not in done][: a.limit or None]
    books = {}
    if a.learn:   # 판정 학습: 그림마다 그 과제보다 앞선 과제에서 배운 규칙집을 머리말 뒤에(batch/judge_learn.py)
        import judge_learn as L
        books = {t: L.rulebook(t) for t in {it["task"] for it in todo}}
    print(f"[JudgeItems] {a.set}/{a.key} {a.model}·{a.header} — 남은 그림 {len(todo)}", flush=True)

    def one(it):
        d, files = prepare(it, a.set, a.zoom)
        rules = L.rules_for(it, set(only or J_CLASSES_OF(it)), books[it["task"]], other=0 if a.learn == "same" else L.OTHER_SCENE_CAP) if a.learn else ""
        text, tries, got = (oddity_prompt(it, files, HEADERS[a.header]) if odd else prompt(it, files, HEADERS[a.header] + rules)), [], None
        for _ in range(2):   # JSON이 깨지면 한 번만 다시
            o = call(text, d, a.model)
            tries.append(use(o) | {"error": bool(o.get("is_error"))})
            got = None if o.get("is_error") else parse(o.get("result"), it["qids"])
            if got:
                break
        rec = {"tries": tries, "raw": None if got else str(o.get("result"))[:400], **(got or {"answers": None})}
        update(lambda m: m[a.set][a.key]["answers"].__setitem__(it["key"], rec))
        print(f"[JudgeItems] {it['key']} {'ok' if got else '답 없음'} · 시도 {len(tries)} · {sum(t['seconds'] for t in tries):.0f}초", flush=True)

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(one, todo))


def ratio(h):
    return round(h[0] / h[1], 4) if h[1] else None


def J_CLASSES_OF(it):
    return {cls(q) for q in it["qids"]}


def summarize(set_name, r):
    """원 답 → 요약(잡기·통과·부류별·8/8 칸·쏠림·사용량). 호출한 그림만 세고, 답 없음(실패 호출)은 라벨 반대로 셈."""
    its = [it for it in items(set_name, r.get("only")) if it["key"] in r["answers"]]
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
            "catch": ratio(hits["틀림"]), "pass": ratio(hits["맞음"]),
            "machine_wrong_rate": round(machine_wrong / n, 4),
            "by_class": {c: {"catch": f"{v['틀림'][0]}/{v['틀림'][1]}", "pass": f"{v['맞음'][0]}/{v['맞음'][1]}"}
                         for c, v in by.items() if v["틀림"][1] + v["맞음"][1]},
            "full_wrong_cells": {"n": len(full), "caught_all": sum(1 for k in full if cells[k][2] == cells[k][1]),
                                 "missed": [k for k in full if cells[k][2] < cells[k][1]]},
            "usage": {k: round(sum(t[k] for t in tries), 4) for k in ("seconds", "input", "output", "cache_read", "cache_create", "cost_usd")}}


# 판정자 = 종류별 호출 묶음 {set: {"base": 전 문항 run, 종류: run}} — notes 「후속 시험 — 판정자 J1」 고정 절
SYSTEMS = {"J1": {"dev": {"base": "r2", "prop": "p2-sonnet"}, "holdout": {"base": "sonnet", "prop": "p2-sonnet"}}}


def system_summary(m, set_name, route):
    """종류별 run 답을 묶어 채점 — 종류 run에 답이 없으면(실패 호출) 라벨 반대로 셈."""
    hits = {"틀림": [0, 0], "맞음": [0, 0]}
    by = {c: {"틀림": [0, 0], "맞음": [0, 0]} for c in CLASSES}
    for it in items(set_name):
        for qid, lab in it["labels"].items():
            ans = (m[set_name][route.get(cls(qid), route["base"])]["answers"].get(it["key"]) or {}).get("answers")
            ok = (ans[qid] if ans else ("맞음" if lab == "틀림" else "틀림")) == lab
            for h in (hits[lab], by[cls(qid)][lab]):
                h[0] += ok
                h[1] += 1
    return {"route": route, "catch": round(hits["틀림"][0] / hits["틀림"][1], 4), "pass": round(hits["맞음"][0] / hits["맞음"][1], 4),
            "n": hits["틀림"][1] + hits["맞음"][1], "by_class": {c: {"catch": f"{v['틀림'][0]}/{v['틀림'][1]}", "pass": f"{v['맞음'][0]}/{v['맞음'][1]}"}
                                                               for c, v in by.items() if v["틀림"][1] + v["맞음"][1]}}


def systems(m):
    return {name: {s: system_summary(m, s, r) for s, r in sets.items() if all(k in m.get(s, {}) for k in r.values())}
            for name, sets in SYSTEMS.items()}


def verdict(m):
    h = m.get("holdout", {})
    ok = lambda k: k in h and h[k]["summary"]["catch"] >= PASS_LINE and h[k]["summary"]["pass"] >= PASS_LINE
    if ok("sonnet"):
        return "합격 (Sonnet)"
    if "opus" in h:
        return "합격 (Opus)" if ok("opus") else "불합격"
    return None


def pct(x):
    return "—" if x is None else f"{x * 100:.1f}%"


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
    sys_rows = []
    for name, per in systems(m).items():
        for s, x in per.items():
            ok = x["catch"] >= PASS_LINE and x["pass"] >= PASS_LINE
            sys_rows.append(f"| {name} {s} | {x['n']} | {pct(x['catch'])} | {pct(x['pass'])} | {'합격' if ok else '불합격'} | "
                            + " · ".join(f"{c} 잡기 {v['catch']} 통과 {v['pass']}" for c, v in x["by_class"].items()) + " |")
        if "holdout" in per:
            x = per["holdout"]
            head.append(f"{name} 판정: {'합격' if x['catch'] >= PASS_LINE and x['pass'] >= PASS_LINE else '불합격'}")
    if sys_rows:
        sys_rows = ["", "판정자(종류별 호출 묶음):", "", "| 판정자·묶음 | 라벨 | 잡기 | 통과 | 기준 | 종류별 |", "|---|---|---|---|---|---|"] + sys_rows
    return "\n".join(head + rows + ["", "문항 부류별(맞힌 수/라벨 수):", ""] + cls_rows + sys_rows)


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
    def put(m):   # 그 사이 다른 run이 쓴 답을 지우지 않게 요약만 합쳐 쓴다
        for s in fresh:
            for k, x in fresh[s].items():
                m[s][k]["summary"] = x
    m = update(put)
    m = {**m, **{s: {k: {**r, "summary": fresh[s][k]} if k in fresh[s] else r for k, r in m[s].items()} for s in fresh}}
    notes = open(NOTES, encoding="utf-8").read()
    block = f"{BEGIN}\n{table(m)}\n{END}"
    notes = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), lambda _: block, notes, flags=re.S) if BEGIN in notes else notes.rstrip() + "\n\n## 결과\n\n" + block + "\n"
    open(NOTES, "w", encoding="utf-8").write(notes)
    print(table(m), flush=True)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--set", required=True, help="dev · holdout · t<과제>(라벨 전 예측, 예: t372)")
    r.add_argument("--key", required=True)
    r.add_argument("--header", choices=HEADERS, required=True)
    r.add_argument("--model", required=True)
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--only", default="", help="문항 종류만(쉼표) — 예: prop · crowds")
    r.add_argument("--zoom", type=float, default=1.0, help="인물 몸 크롭 확대 배율")
    r.add_argument("--tasks", default="", help="이 과제 그림만(쉼표) — 예: 369")
    r.add_argument("--learn", nargs="?", const="all", default="", choices=["all", "same"],
                   help="그 과제 앞까지 배운 규칙집을 머리말 뒤에 붙임(judge_learn) — same이면 같은 장면 규칙만")
    pr = sub.add_parser("predict", help="새 묶음에 J1(v2 전 문항 + p2 지물만)과 이상한 점(o1)을 동시에 — 후보 화면 전에")
    pr.add_argument("--task", type=int, required=True)
    s = sub.add_parser("score")
    s.add_argument("--check", action="store_true")
    a = p.parse_args()
    if a.cmd == "predict":   # J1 두 호출을 동시에(답마다 update로 합쳐 씀)
        me = [sys.executable, os.path.abspath(__file__), "run", "--set", f"t{a.task}", "--model", "sonnet"]
        ps = [subprocess.Popen(me + ["--key", "J1", "--header", "v2"]),
              subprocess.Popen(me + ["--key", "J1-prop", "--header", "p2", "--only", "prop", "--zoom", "2.5"]),
              subprocess.Popen(me + ["--key", "O1", "--header", "o1"])]   # 이상한 점 — 결합 켬/끔과 무관하게 기록(task 378)
        sys.exit(max(p.wait() for p in ps))
    run(a) if a.cmd == "run" else score(a)


if __name__ == "__main__":
    main()
