#!/usr/bin/env python3
"""task#397 — 기브아 창 장면을 394 새 명세로 다시 그려(C 장면만, 얼굴 보정 없음) 낡은 승인을 사람이 고른 새 승인으로 바꾼다.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV batch/gibeah_redraw.py gen        # route_prompt 문구 · 8시드 Z-Image(생성 프로세스 한 번에 하나)
  python3 batch/gibeah_redraw.py judge    # 8장 × 화풍 S·요소 E × 3회 — claude -p Sonnet · 머리말 v2
  python3 batch/gibeah_redraw.py report   # 장마다 다수결 · 거르기 틀림 · `후보:` 줄
  python3 batch/gibeah_redraw.py cand     # 후보 2장 블라인드 좌우 1화면(+ 접힌 칸 8장·옛 승인 참고) → ~/.local/biblemap-imggen/pages/gibeah-redraw-cand.html
  python3 batch/gibeah_redraw.py record samples/gibeah-redraw/pick-verdict.txt   # 사람 답 → 고르면 approved.final(night-pick 바탕)
  python3 batch/gibeah_redraw.py check    # 그림·답 빠짐 0 · 노트 `후보:` 줄 = 다시 셈 → ok

규칙은 notes/GIBEAH-REDRAW.md 고정 절. 그림 ~/.local/biblemap-imggen/gibeah-redraw/s<시드>.png · 답 samples/gibeah-redraw/metrics.json.
판정·화면 틀은 restyle_try(요단 r3~r6)와 같은 부품(judge_items.prepare/prompt/call, plain_words.PAGE_G, make_cand_page.scripture)."""
import json, os, re, shutil, subprocess, sys, threading
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "batch"))
import derive_scene as D
import judge_items as J

NAME = "gibeah-redraw"
NOTES = os.path.join(HERE, "notes", "GIBEAH-REDRAW.md")
METRICS = os.path.join(HERE, "samples", NAME, "metrics.json")
OUT = os.path.expanduser(f"~/.local/biblemap-imggen/{NAME}")
APPROVED = os.path.join("samples", NAME, "approved-authored-saul-gibeah-spear.png")   # 레포 사본(CANON_DIR 기준 상대 경로)
LOCK = threading.Lock()
with open(NOTES, encoding="utf-8") as _fh:
    FX = json.loads(re.search(r"```json fixed\n(.*?)\n```", _fh.read(), re.S).group(1))
SID = FX["scene"]
QS = {"S": FX["style"], "E": FX["elements"]}


def img(s):
    return os.path.join(OUT, f"s{s}.png")


def load():
    return json.load(open(METRICS, encoding="utf-8")) if os.path.exists(METRICS) else {"answers": {}}


def save(m):
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    with open(METRICS, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=1)


def gen():
    import recheck
    recheck.require_pass(SID)   # task 399 generate.spec-gate — 명세 규칙에 걸리면 그리지 않는다
    busy = subprocess.run(["pgrep", "-fl", "mflux|run_scene.py --worker|gen_video_pilot|mlx_video"], capture_output=True, text=True).stdout.strip()
    if busy:
        sys.exit(f"[GibeahRedraw] 다른 생성 프로세스가 돈다 — 겹치지 않게 멈춤:\n{busy}")
    import run_scene
    prompt = D.route_prompt(D.load(SID))
    w, h = FX["size"]
    jobs = [{"prompt": prompt, "seed": s, "w": w, "h": h, "out": img(s)} for s in FX["seeds"] if not os.path.exists(img(s))]
    m = load()
    m["prompt"] = prompt
    save(m)
    print(f"[GibeahRedraw] {len(FX['seeds'])}장 중 {len(jobs)}장 생성", flush=True)
    if jobs:
        os.makedirs(OUT, exist_ok=True)
        secs = run_scene.gen_zimage(jobs, OUT)
        m["secs"] = m.get("secs", []) + list(secs)
        save(m)
        print(f"[GibeahRedraw] 생성 끝 {secs}", flush=True)


def ask(m, s, kind, rep):
    spec = D.load(SID)
    it = {"key": f"g:{s}", "task": NAME, "scene": SID, "title": spec["title"], "range": spec["verses"]["range"],
          "seed": s, "src": img(s), "qs": [dict(q) for q in QS[kind]], "qids": [q["id"] for q in QS[kind]]}
    d, files = J.prepare(it, NAME)
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
    todo = [(s, k, r) for s in FX["seeds"] for k in QS for r in range(1, FX["reps"] + 1)
            if not ((m["answers"].get(f"g:{s}") or {}).get(k, {}).get(str(r)) or {}).get("answers")]
    print(f"[GibeahRedraw] 판정 {len(todo)}건", flush=True)
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda job: ask(m, *job), todo))


def votes(m, s, qid):
    kind = "S" if qid.startswith("s.") else "E"
    return [(r.get("answers") or {}).get(qid) for _, r in sorted((m["answers"].get(f"g:{s}") or {}).get(kind, {}).items())]


def maj(v):
    return "맞음" if v.count("맞음") * 2 > len(v) else "틀림"


def wrongs(m, s):
    return sum(maj(votes(m, s, q["id"])) == "틀림" for q in QS["S"] + QS["E"])


def pick(m):
    """후보 2장 = 거르기 틀림 최소 → 전체 틀림 최소 → 시드 순서(통과가 모자라면 불통과로 채우고 화면에 표시)."""
    fails = {s: sum(maj(votes(m, s, q)) == "틀림" for q in FX["filter_qs"]) for s in FX["seeds"]}
    order = sorted(FX["seeds"], key=lambda s: (fails[s], wrongs(m, s), FX["seeds"].index(s)))
    return [s for s in FX["seeds"] if fails[s] == 0], order[:2], fails


def conclude(m):
    ok, cands, _ = pick(m)
    return f"통과 {len(ok)}/{len(FX['seeds'])} (후보 {', '.join(f's{s}' for s in cands)})"


def report():
    m = load()
    qs = [q["id"] for q in QS["S"] + QS["E"]]
    print("시드 " + " ".join(q.split(".")[1][:10] for q in qs))
    for s in FX["seeds"]:
        print(f"s{s:<3} " + " ".join("".join(x[0] if x else "-" for x in votes(m, s, q)) for q in qs))
    print("다수결 맞음(8장 중): " + " · ".join(f"{q['q']} {sum(maj(votes(m, s, q['id'])) == '맞음' for s in FX['seeds'])}" for q in QS["S"] + QS["E"]))
    print(f"[GibeahRedraw] 거르기 틀림 {pick(m)[2]}")
    print(f"후보: {conclude(m)}")


def cand():
    from PIL import Image
    sys.argv += ["--set", "jordan-guide"]   # plain_words는 import 때 묶음을 읽는다 — 화면 틀·원문만 빌린다
    import plain_words as PW
    import make_cand_page as C
    m = load()
    ok, cands, _ = pick(m)
    assert len(cands) == 2, f"후보 2장 아님: {cands}"
    one, two = f"g:{cands[0]}", f"g:{cands[1]}"
    keys = [(f"g:{s}", f"새 명세 s{s}{'' if s in ok else ' (기계 불통과)'}") for s in FX["seeds"]] + [("ref:0", FX["ref"]["label"])]
    src = lambda k: os.path.expanduser(FX["ref"]["image"]) if k.startswith("ref:") else img(int(k.split(":")[1]))
    tpl = (PW.PAGE_G.replace("<title>요단 구도 그림 비교 388</title>", "<title>기브아 창 다시 그리기</title>")
           .replace("const TASK = 388;", f'const TASK = "{NAME}";')
           .replace("가이드·본 실행·격자·387 참고 ${s.all.length}장", "새 명세 8장·옛 승인 참고 ${s.all.length}장"))
    assert f'const TASK = "{NAME}";' in tpl and "<title>기브아 창 다시 그리기</title>" in tpl
    verses = [[r, t, b or r in FX["bold"]] for r, t, b in C.scripture(SID)]   # 18:10(같은 자리)도 굵게
    spec = D.load(SID)
    left, right = (one, two) if PW.left_is_a(SID) else (two, one)
    for w, q in C.SIZES:
        data = {k: PW.P.uri(Image.open(src(k)), w, q) for k, _ in keys}
        scenes = [{"id": SID, "title": spec["title"], "range": spec["verses"]["range"], "ab": True, "reject": False,
                   "left": left, "right": right, "left_is": "1위" if left == one else "2위", "right_is": "1위" if right == one else "2위",
                   "all": [list(x) for x in keys], "verses": verses}]
        page = (tpl.replace("/*STYLE*/", C.STYLE + C.VERSE_STYLE).replace("/*SCENES*/[]", json.dumps(scenes, ensure_ascii=False))
                .replace("/*IMGS*/{}", json.dumps(data)))
        if len(page) <= PW.P.LIMIT:
            break
    out = os.path.join(J.PAGES, f"{NAME}-cand.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(page)
    m["cand"] = {"left": left, "right": right, "cands": cands}
    save(m)
    print(f"[GibeahRedraw] 후보 화면 {out} {len(page) / 1e6:.2f}MB · {w}px q{q} · 후보 {cands}", flush=True)


def record(path):
    """사람 답(「판정 task gibeah-redraw」 + JSON 한 줄) → 고른 시드 바탕을 레포에 복사하고 approved.final(night-pick 바탕). 「none」이면 옛 승인 그대로."""
    import approve
    v = json.loads(open(path, encoding="utf-8").read().split("\n", 1)[1].splitlines()[0])
    a = v["scenes"][SID]
    m = load()
    m["verdict"] = a
    save(m)
    if a["answer"] not in ("left", "right"):
        print("[GibeahRedraw] 둘 다 아님 — 옛 승인 그대로(판정: 보류)", flush=True)
        return
    s = int(a[a["answer"]].split(":")[1])
    shutil.copyfile(img(s), os.path.join(HERE, APPROVED))
    spec = approve.load_spec(SID)
    spec = approve.night_pick(spec, s, "base", APPROVED, "user", m["prompt"])
    spec["approved"]["final"]["round"] = NAME
    approve.save_spec(spec)
    print(f"[GibeahRedraw] 장면 채택 — s{s} · {APPROVED}", flush=True)


def check():
    m, err = load(), []
    for s in FX["seeds"]:
        if not os.path.exists(img(s)):
            err.append(f"그림 없음 s{s}")
        for q in QS["S"] + QS["E"]:
            v = votes(m, s, q["id"])
            if len(v) != FX["reps"] or None in v:
                err.append(f"s{s} {q['id']} 답 {v}")
    line = re.findall(r"^후보: (.+)$", open(NOTES, encoding="utf-8").read(), re.M)
    if not err and line != [conclude(m)]:
        err.append(f"노트 후보 줄 {line} ≠ 다시 셈 {conclude(m)}")
    print("ok" if not err else "\n".join(err[:20]))
    return not err


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "record":
        record(sys.argv[2])
        sys.exit(0)
    fn = {"gen": gen, "judge": judge, "report": report, "check": check, "cand": cand}.get(cmd)
    if not fn:
        sys.exit(__doc__)
    r = fn()
    if cmd == "check":
        sys.exit(0 if r else 1)
