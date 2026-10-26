#!/usr/bin/env python3
"""restyle-try — CN이 누른 화풍을 되살리는 안 해 본 두 방법(388 다음 수단 2 · 389 `점검: CN 탓` 뒤).

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV batch/restyle_try.py gen       # ① 두 단계 img2img 6장 · ② CN 앞 1·2스텝 4장 (생성 프로세스 한 번에 하나)
  python3 batch/restyle_try.py judge   # 12장(+ 바탕 388 1.0·4 두 장) × S·E 3회 — claude -p Sonnet · 머리말 v2
  python3 batch/restyle_try.py report  # 장마다 다수결 · 통과 설정
  python3 batch/restyle_try.py check   # 개수·빈 답·노트 `시험:` 줄 = 다시 셈 → ok

r3(`--round r3`, notes/RESTYLE-R3.md): 다윗 왕(60세 전후·왕 표지)·시므이 방향을 넣은 정본 문구 + 1단계 CN만 8시드 → 문항 둘 더 → 후보 2장.
r2(`--round r2`, notes/RESTYLE-R2.md): 8시드 — 1단계 CN 1.0·앞 4 → A img2img 0.7 · B2/B3 img2img 0.7 + 약한 CN 0.2/0.3 → 방법 고르기.
규칙은 notes/RESTYLE-TRY.md 고정 절. 문구·가이드·시드는 388 격자 1.0·4 job(_zjobs.json) 그대로, 문항은 JORDAN-GUIDE 고정 절 style·elements.
그림 ~/.local/biblemap-imggen/restyle-try/<갈래>/s<시드>.png · 답 samples/restyle-try/metrics.json."""
import json, os, re, sys, threading
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "batch"))
import derive_scene as D
import judge_items as J

ROUND = sys.argv[sys.argv.index("--round") + 1] if "--round" in sys.argv else "r1"
NAME = {"r1": "restyle-try", "r2": "restyle-r2", "r3": "restyle-r3", "r4": "restyle-r4", "r4e": "restyle-r4e", "r5": "restyle-r5", "r6": "restyle-r6"}[ROUND]
NOTE_MD = os.path.join(HERE, "notes", {"r1": "RESTYLE-TRY.md", "r2": "RESTYLE-R2.md", "r3": "RESTYLE-R3.md", "r4": "RESTYLE-R4.md",
                                     "r4e": "RESTYLE-R4E.md", "r5": "RESTYLE-R5.md", "r6": "RESTYLE-R6.md"}[ROUND])
METRICS = os.path.join(HERE, "samples", NAME, "metrics.json")
IMG = os.path.expanduser("~/.local/biblemap-imggen")
OUT = f"{IMG}/{NAME}"
SID = "authored-david-returns-jerusalem"
BASE = f"{IMG}/jordan-guide/g-1.0-4/{SID}"
LOCK = threading.Lock()
LINE = {"r1": "시험", "r2": "선택", "r3": "후보", "r4": "후보", "r4e": "후보", "r5": "후보", "r6": "후보"}[ROUND]


def fixed(path):
    return json.loads(re.search(r"```json fixed\n(.*?)\n```", open(path, encoding="utf-8").read(), re.S).group(1))


FX = fixed(NOTE_MD)
G = fixed(os.path.join(HERE, "notes", "JORDAN-GUIDE.md"))["scenes"][SID]
QS = {"S": G["style"], "E": FX["elements"] if "elements" in FX else G["elements"] + FX.get("extra_elements", [])}


def arms():
    """갈래 이름 → (방법, 값). r1: ① i2i-<강도> · ② cn-<스텝> · 바탕 base(388 1.0·4, 생성 안 함). r2: 고정 절 arms + base(1단계)."""
    if ROUND == "r4e":   # 국소 편집 — 바탕(채택본) + 지시 갈래
        return {"base": ("base", None), **{a: ("edit", v) for a, v in FX["arms"].items()}}
    if ROUND in ("r3", "r4", "r5", "r6"):
        return {"cn": ("gencn", FX["stage1"])}
    if ROUND == "r2":
        return {"base": ("base", None), **{a: ("i2icn" if v.get("cn") else "i2i", v) for a, v in FX["arms"].items()}}
    return {"base": ("base", None), **{f"i2i-{s}": ("i2i", s) for s in FX["i2i_strengths"]},
            **{f"cn-{k}": ("cn", k) for k in FX["cn_steps"]}}


def img(arm, s):
    if ROUND == "r4e":
        return os.path.join(HERE, FX["base"]) if arm == "base" else f"{OUT}/{arm}/s{s}.png"
    if arm == "ref":   # r4 접힌 칸 참고 — r3 승인본
        return os.path.join(HERE, FX["ref_image"]) if "ref_image" in FX else f"{IMG}/restyle-r3/cn/s{s}.png"
    if arm == "base" and ROUND == "r2" and s not in (11, 42):
        return f"{OUT}/stage1/s{s}.png"
    return f"{BASE}/s{s}.png" if arm == "base" else f"{OUT}/{arm}/s{s}.png"


def gen():
    import recheck
    recheck.require_pass(SID)   # task 399 generate.spec-gate
    sys.path.insert(0, os.path.join(HERE, "batch"))
    import run_scene
    src = {j["seed"]: j for j in json.load(open(f"{BASE}/_zjobs.json"))}
    if ROUND == "r4e":   # task 371·386 조리법: 작은 크롭 → 1024 klein 지시 하나 → color_match → 타원 마스크 되붙임
        import gen_local_edit as LE
        m = load()
        for a, prompt in FX["arms"].items():
            for s in FX["seeds"]:
                os.makedirs(f"{OUT}/{a}", exist_ok=True)
                r = LE.edit(img("base", 0), tuple(FX["crop"]), tuple(FX["box"]), a, s, img(a, s), prompt=prompt)
                m.setdefault("edits", {})[f"{a}:{s}"] = r
                print(f"[RestyleTry] r4e {a} s{s} {r}", flush=True)
        save(m)
        return
    if ROUND in ("r3", "r4", "r5", "r6"):   # 문구는 고친 정본에서 바로(388 문구 = 그때 정본의 route_prompt — 같음을 확인함)
        prompt = D.route_prompt(D.load(SID))
        jobs = [{"prompt": prompt, "seed": s, "w": 1216, "h": 640, "out": img("cn", s), "control": os.path.join(HERE, FX["guide"]) if "guide" in FX else src[11]["control"],
                 "scale": FX["stage1"]["scale"], "cn_steps": FX["stage1"]["cn_steps"]} for s in FX["seeds"] if not os.path.exists(img("cn", s))]
        m = load()
        m["prompt"] = prompt
        save(m)
        if jobs:
            os.makedirs(os.path.join(OUT, "cn"), exist_ok=True)
            print(f"[RestyleTry] {ROUND} gencn {len(jobs)}장 {run_scene.gen_zimage(jobs, os.path.join(OUT, 'cn'), 'gencn')}", flush=True)
        return
    if ROUND == "r2":
        return gen_r2(run_scene, src[11])
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


def gen_r2(run_scene, s0):
    """1단계(없는 시드만 CN 1.0·앞 4) → 갈래마다 2단계. 문구·가이드는 388 1.0·4 job 그대로(두 시드 같은 문구)."""
    st = FX["stage1"]
    for mode in ("gencn", "i2i", "i2icn"):
        jobs = []
        for s in FX["seeds"]:
            j = {"prompt": s0["prompt"], "seed": s, "w": s0["w"], "h": s0["h"], "control": s0["control"]}
            if mode == "gencn" and not os.path.exists(img("base", s)):
                jobs.append({**j, "out": img("base", s), "scale": st["scale"], "cn_steps": st["cn_steps"]})
            for a, (k, v) in arms().items():
                if k == mode and mode != "gencn" and not os.path.exists(img(a, s)):
                    jobs.append({**j, "out": img(a, s), "src": img("base", s), "strength": v["strength"],
                                 "scale": v.get("cn", 0), "cn_steps": 9})
        for x in jobs:
            os.makedirs(os.path.dirname(x["out"]), exist_ok=True)
        if jobs:
            d = os.path.join(OUT, f"_{mode}")
            os.makedirs(d, exist_ok=True)
            print(f"[RestyleTry] r2 {mode} {len(jobs)}장 {run_scene.gen_zimage(jobs, d, mode)}", flush=True)


def load():
    return json.load(open(METRICS, encoding="utf-8")) if os.path.exists(METRICS) else {"answers": {}}


def save(m):
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    with open(METRICS, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=1)


def ask(m, arm, s, kind, rep):
    spec = D.load(SID)
    it = {"key": f"{arm}:{s}", "task": f"{ROUND}-{arm}", "scene": SID, "title": spec["title"], "range": spec["verses"]["range"],
          "seed": s, "src": img(arm, s), "qs": [dict(q) for q in QS[kind]], "qids": [q["id"] for q in QS[kind]]}
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
    todo = [(a, s, k, r) for a in arms() for s in seeds_of(a) for k in QS for r in range(1, FX["reps"] + 1)
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


def wrongs(m, a, s):
    return sum(maj(votes(m, a, s, q["id"])) == "틀림" for q in QS["S"] + QS["E"])


def pick_r2(m):
    """그림 통과 = filter_qs 다수결 모두 맞음. 방법 = 통과 장 수 최대 → 전체 틀림 합 최소 → 고정 절 arms 순서. 후보 = 그 방법 통과 장 중 틀림 최소 2장(같으면 시드 순서)."""
    ok = {a: [s for s in FX["seeds"] if all(maj(votes(m, a, s, q)) == "맞음" for q in FX["filter_qs"])] for a in FX["arms"]}
    order = list(FX["arms"])
    best = min(order, key=lambda a: (-len(ok[a]), sum(wrongs(m, a, s) for s in FX["seeds"]), order.index(a)))
    cands = sorted(ok[best], key=lambda s: (wrongs(m, best, s), FX["seeds"].index(s)))[:2]
    return (best if ok[best] else None), cands, ok


def pick_r3(m):
    """후보 2장 = 거르기 문항 틀림 수 최소 → 전체 틀림 최소 → 시드 순서(통과가 모자라면 불통과로 채우고 표시)."""
    fails = {s: sum(maj(votes(m, "cn", s, q)) == "틀림" for q in FX["filter_qs"]) for s in FX["seeds"]}
    order = sorted(FX["seeds"], key=lambda s: (fails[s], wrongs(m, "cn", s), FX["seeds"].index(s)))
    return [s for s in FX["seeds"] if fails[s] == 0], order[:2], fails


def seeds_of(a):
    return [0] if ROUND == "r4e" and a == "base" else FX["seeds"]


def pick_r4e(m):
    """후보 2장 = 편집 갈래 전체에서 거르기 틀림 최소 → 전체 틀림 최소 → 갈래·시드 순서(바탕은 대조라 뺀다)."""
    keys = [(a, s) for a in FX["arms"] for s in FX["seeds"]]
    fails = {k: sum(maj(votes(m, *k, q)) == "틀림" for q in FX["filter_qs"]) for k in keys}
    order = sorted(keys, key=lambda k: (fails[k], wrongs(m, *k), keys.index(k)))
    return [k for k in keys if fails[k] == 0], order[:2], fails


def conclude(m):
    if ROUND == "r4e":
        ok, cands, _ = pick_r4e(m)
        return f"통과 {len(ok)}/{len(FX['arms']) * len(FX['seeds'])} (후보 {', '.join(f'{a} s{s}' for a, s in cands)})"
    if ROUND in ("r3", "r4", "r5", "r6"):
        ok, cands, _ = pick_r3(m)
        return f"통과 {len(ok)}/{len(FX['seeds'])} (후보 {', '.join(f's{s}' for s in cands)})"
    if ROUND == "r2":
        best, cands, _ = pick_r2(m)
        return f"{best} (후보 {', '.join(f's{s}' for s in cands)})" if best else "없음"
    p = passed(m)
    return f"통과 {', '.join(p)}" if p else "통과 없음"


def report():
    m = load()
    qs = [q["id"] for q in QS["S"] + QS["E"]]
    print("갈래      시드 " + " ".join(q.split(".")[1][:10] for q in qs))
    for a in arms():
        for s in seeds_of(a):
            print(f"{a:9} s{s:<3} " + " ".join("".join(x[0] if x else "-" for x in votes(m, a, s, q)) for q in qs))
    if ROUND in ("r3", "r4", "r5", "r6"):
        print(f"[cn] 거르기 문항 틀림 {pick_r3(m)[2]}")
    if ROUND == "r2":
        best, cands, ok = pick_r2(m)
        for a in FX["arms"]:
            print(f"[{a}] 통과 {len(ok[a])}/{len(FX['seeds'])} {['s%d' % s for s in ok[a]]} · 틀림 합 {sum(wrongs(m, a, s) for s in FX['seeds'])}")
    print(f"{LINE}: {conclude(m)}")


def cand():
    """r2 후보 사람 1화면 — 고른 방법 후보 2장 블라인드 좌우(388 화면 틀 PAGE_G) + 접힌 칸에 1단계·세 갈래 32장(기계 불통과 포함)."""
    from PIL import Image
    sys.argv += ["--set", "jordan-guide"]   # plain_words는 import 때 묶음을 읽는다 — 화면 틀·원문만 빌린다
    import plain_words as PW
    import make_cand_page as C
    m = load()
    if ROUND == "r4e":
        oks, cands, _ = pick_r4e(m)
        best, ok = "edit", {a: [s for b, s in oks if b == a] for a in arms()}
    elif ROUND in ("r3", "r4", "r5", "r6"):
        oks, cands, _ = pick_r3(m)
        best, ok = "cn", {"cn": oks}
    else:
        best, cands, ok = pick_r2(m)
    assert best and len(cands) == 2, f"후보 2장 아님: {best} {cands}"
    one, two = (f"{cands[0][0]}:{cands[0][1]}", f"{cands[1][0]}:{cands[1][1]}") if ROUND == "r4e" else (f"{best}:{cands[0]}", f"{best}:{cands[1]}")
    keys = [(f"{a}:{s}", f"{'편집 전 채택본' if ROUND == 'r4e' and a == 'base' else '1단계 CN' if a in ('base', 'cn') else a} {'' if ROUND == 'r4e' and a == 'base' else f's{s}'}{'' if a == 'base' or s in ok[a] else ' (기계 불통과)'}")
            for a in arms() for s in seeds_of(a)] + [(f"ref:{s}", f"{FX.get('ref_label', 'r3 승인본')} s{s} (참고)") for s in FX.get("ref_seeds", [])]
    tpl = (PW.PAGE_G.replace("<title>요단 구도 그림 비교 388</title>", "<title>요단 화풍 되살리기 비교</title>" if ROUND == "r2" else "<title>요단 다윗과 시므이</title>" if ROUND == "r3" else "<title>요단 다윗과 시므이 r4</title>" if ROUND == "r4" else "<title>요단 다윗 시선 편집</title>" if ROUND == "r4e" else "<title>요단 숙인 다윗</title>" if ROUND == "r5" else "<title>요단 엎드린 시므이</title>")
           .replace("const TASK = 388;", f'const TASK = "{NAME}";')
           .replace("가이드·본 실행·격자·387 참고 ${s.all.length}장", "1단계·세 방법 전부 ${s.all.length}장"))
    for w, q in C.SIZES:
        data = {k: PW.P.uri(Image.open(img(*k.split(":")[:1], int(k.split(":")[1]))), w, q) for k, _ in keys}
        left, right = (one, two) if PW.left_is_a(SID) else (two, one)
        spec = D.load(SID)
        scenes = [{"id": SID, "title": spec["title"], "range": spec["verses"]["range"], "ab": True, "reject": False,
                   "left": left, "right": right, "left_is": "1위" if left == one else "2위", "right_is": "1위" if right == one else "2위",
                   "all": [list(x) for x in keys], "verses": C.scripture(SID)}]
        page = (tpl.replace("/*STYLE*/", C.STYLE + C.VERSE_STYLE).replace("/*SCENES*/[]", json.dumps(scenes, ensure_ascii=False))
                .replace("/*IMGS*/{}", json.dumps(data)))
        if len(page) <= PW.P.LIMIT:
            break
    out = os.path.join(J.PAGES, f"{NAME}-cand.html")
    open(out, "w", encoding="utf-8").write(page)
    m["cand"] = {"best": best, "left": left, "right": right}
    save(m)
    print(f"[RestyleTry] 후보 화면 {out} {len(page) / 1e6:.2f}MB · {w}px q{q} · {best} {cands}", flush=True)


def check():
    m, err = load(), []
    for a in arms():
        for s in seeds_of(a):
            if not os.path.exists(img(a, s)):
                err.append(f"그림 없음 {a} s{s}")
            for q in QS["S"] + QS["E"]:
                v = votes(m, a, s, q["id"])
                if len(v) != FX["reps"] or None in v:
                    err.append(f"{a} s{s} {q['id']} 답 {v}")
    line = re.findall(rf"^{LINE}: (.+)$", open(NOTE_MD, encoding="utf-8").read(), re.M)
    if not err and line != [conclude(m)]:
        err.append(f"노트 {LINE} 줄 {line} ≠ 다시 셈 {conclude(m)}")
    print("ok" if not err else "\n".join(err[:20]))
    return not err


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    fn = {"gen": gen, "judge": judge, "report": report, "check": check, "cand": cand}.get(cmd)
    if not fn:
        sys.exit(__doc__)
    r = fn()
    if cmd == "check":
        sys.exit(0 if r else 1)
