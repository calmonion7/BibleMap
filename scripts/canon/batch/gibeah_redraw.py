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

TRY = sys.argv[sys.argv.index("--try") + 1] if "--try" in sys.argv else None   # task 400 단계 ②③ 시도(a1, a2 …)
NAME = f"gibeah-step23/{TRY}" if TRY else "gibeah-redraw"
NOTES = os.path.join(HERE, "notes", "GIBEAH-STEP23.md" if TRY else "GIBEAH-REDRAW.md")
METRICS = os.path.join(HERE, "samples", NAME, "metrics.json")
OUT = os.path.expanduser(f"~/.local/biblemap-imggen/{NAME}")
APPROVED = os.path.join("samples", NAME, "approved-authored-saul-gibeah-spear.png")   # 레포 사본(CANON_DIR 기준 상대 경로)
LOCK = threading.Lock()
with open(NOTES, encoding="utf-8") as _fh:
    FX = json.loads(re.search(rf"```json fixed{' ' + TRY if TRY else ''}\n(.*?)\n```", _fh.read(), re.S).group(1))
LINE = "통과" if TRY else "후보"   # 노트 결론 줄 머리 — task 400 DoD는 「통과: N/8」
SID = FX["scene"]
QS = {"S": FX["style"], "E": FX["elements"]}


def img(s):
    """그림 자리 — 고정 절 images_from(다른 시도 이름)이 있으면 그 시도 그림을 다시 묻는다(task 402 b0: 새 문항이 사람 거절 그림을 잡는가)."""
    src = os.path.join(os.path.dirname(OUT), FX["images_from"]) if FX.get("images_from") else OUT
    return os.path.join(src, f"s{s}.png")


def load():
    return json.load(open(METRICS, encoding="utf-8")) if os.path.exists(METRICS) else {"answers": {}}


def save(m):
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    with open(METRICS, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=1)


def guide_ok(spec):
    """명세에 guide가 있으면 고정 절 guide 파일이 그 명세에서 다시 그린 가이드와 바이트까지 같아야 한다(빠뜨림·낡은 가이드 방지)."""
    if "guide" not in spec:
        return
    import io
    import make_guide
    if not FX.get("guide"):
        sys.exit("[GibeahRedraw] 명세에 guide가 있는데 고정 절 guide가 없다 — 가이드 없이 그리지 않는다")
    for key, stage in (("guide", 1), ("guide2", 2)):   # h1: guide.split이면 둘째 가이드(깊이)도 고정 절 guide2와 같아야
        if key == "guide2" and not spec["guide"].get("split"):
            continue
        if not FX.get(key):
            sys.exit(f"[GibeahRedraw] 명세 guide에 맞는 고정 절 {key}가 없다")
        buf = io.BytesIO()
        make_guide.make(spec, stage).save(buf, format="PNG")
        with open(os.path.join(HERE, FX[key]), "rb") as fh:
            if fh.read() != buf.getvalue():
                sys.exit(f"[GibeahRedraw] 고정 절 {key} {FX[key]}가 지금 명세의 가이드와 다르다 — make_guide로 다시 그릴 것")


def head_top(spec, key):
    """h1 — 지물 구역과 가로가 겹치는 뼈대 인물 중 가장 높은 머리 꼭대기(화면 비율) — 편집 마스크가 그 머리에 닿지 않게. 없으면 None."""
    import make_guide as M
    R, pose = spec["regions"], (spec.get("guide") or {}).get("pose", {})
    x0, _, x1, _ = R[key]
    tops = []
    for k, name in pose.items():
        a0, b0, a1, b1 = R[k]
        pts, hh = M.pose_points((a0 * M.W, b0 * M.H, a1 * M.W, b1 * M.H), name)   # 화소 → 화면 비율로 되돌림
        hx = [x / M.W for i, (x, y) in pts.items() if i in (0, 14, 15, 16, 17)]
        hy = (min(y for i, (x, y) in pts.items() if i in (0, 14, 15, 16, 17)) - M.HEAD_R["person"] * hh) / M.H
        if hx and min(hx) - 0.05 < x1 and max(hx) + 0.05 > x0:
            tops.append(hy)
    return min(tops) if tops else None


def edit_prop():
    """task 403 d3e — 고정 절 edit(from 시도 · 지물 구역 키 · 사전 id · klein 시드) → 그 시도 그림의 지물만 국소 편집(규칙 edit.small-prop-orient)."""
    import gen_local_edit as GL
    from PIL import Image
    e = FX["edit"]
    spec = D.load(SID)
    words = json.load(open(os.path.join(HERE, "..", "..", "data", "scripture_words", "words.json"), encoding="utf-8"))["words"]
    look = next(w for w in words if w["id"] == e["word"])["look"]["L2"]["en"]
    os.makedirs(OUT, exist_ok=True)
    m = load()
    ends = e.get("ends", ["back"])   # d4: 끝마다 지시 하나씩 차례로(뒤끝 촉 지움 → 앞 촉 모양)
    for s in FX["seeds"]:
        src = os.path.join(os.path.dirname(OUT), e["from"], f"s{s}.png")
        w, h = Image.open(src).size
        steps = []
        for i, end in enumerate(ends):
            out = img(s) if i == len(ends) - 1 else os.path.join(OUT, f"s{s}-{end}.png")
            crop, box = GL.prop_box(spec["regions"][e["region"]], w, h, end, head_top(spec, e["region"]))
            prompt = GL.prop_prompt(look, end)
            r = GL.edit(src, crop, box, None, e["seed"], out, prompt=prompt, mask_shape="rect")   # h2e2: 긴 지물은 둥근 사각 마스크
            steps.append({"end": end, "src": os.path.relpath(src, os.path.dirname(OUT)), "crop": crop, "box": box, "prompt": prompt, **r})
            print(f"[GibeahRedraw] 편집 s{s} {end} {r}", flush=True)
            src = out
        hd = e.get("held")   # h2: 쥔 지물(뼈대 인물 두 손목 자리) — 창 끝 편집 뒤에 차례로
        if hd:
            import make_guide as MG
            a0, b0, a1, b1 = spec["regions"][hd["figure"]]
            pts, _ = MG.pose_points((a0 * MG.W, b0 * MG.H, a1 * MG.W, b1 * MG.H), spec["guide"]["pose"][hd["figure"]])
            crop, box = GL.held_box([(pts[i][0] / MG.W, pts[i][1] / MG.H) for i in (4, 7)], w, h)
            hlook = next(x for x in words if x["id"] == hd["word"])["look"]["L2"]["en"]
            prompt = GL.held_prompt(hlook)
            src0, out = img(s), os.path.join(OUT, f"s{s}-held.png")
            shutil.copyfile(src0, os.path.join(OUT, f"s{s}-tips.png"))
            r = GL.edit(os.path.join(OUT, f"s{s}-tips.png"), crop, box, None, e["seed"], out, prompt=prompt)
            steps.append({"end": "held", "figure": hd["figure"], "word": hd["word"], "crop": crop, "box": box, "prompt": prompt, **r})
            shutil.copyfile(out, img(s))
            print(f"[GibeahRedraw] 편집 s{s} held {r}", flush=True)
        m.setdefault("edit", {})[str(s)] = steps
    save(m)


def gen():
    if FX.get("edit"):
        return edit_prop()
    import recheck
    recheck.require_pass(SID)   # task 399 generate.spec-gate — 명세 규칙에 걸리면 그리지 않는다
    guide_ok(D.load(SID))       # task 400 generate.thrown-guide — 명세에 가이드가 있으면 그 가이드로만
    busy = subprocess.run(["pgrep", "-fl", "mflux|run_scene.py --worker|gen_video_pilot|mlx_video"], capture_output=True, text=True).stdout.strip()
    if busy:
        sys.exit(f"[GibeahRedraw] 다른 생성 프로세스가 돈다 — 겹치지 않게 멈춤:\n{busy}")
    import run_scene
    prompt = D.route_prompt(D.load(SID))
    w, h = FX["size"]
    cn = {"control": os.path.join(HERE, FX["guide"]), "scale": FX["cn"]["scale"], "cn_steps": FX["cn"]["cn_steps"]} if FX.get("guide") else {}
    if FX.get("guide2"):   # h1 스텝별 가이드: 앞 cn_steps는 guide(뼈대), 다음 cn_steps2는 guide2(깊이)
        cn.update(control2=os.path.join(HERE, FX["guide2"]), cn_steps2=FX["cn"]["cn_steps2"])
    jobs = [{"prompt": prompt, "seed": s, "w": w, "h": h, "out": img(s), **cn} for s in FX["seeds"] if not os.path.exists(img(s))]
    m = load()
    m["prompt"] = prompt
    save(m)
    print(f"[GibeahRedraw] {len(FX['seeds'])}장 중 {len(jobs)}장 생성", flush=True)
    if jobs:
        os.makedirs(OUT, exist_ok=True)
        secs = run_scene.gen_zimage(jobs, OUT, "gencn" if cn else "gen")
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
    head = "" if TRY else "통과 "
    return f"{head}{len(ok)}/{len(FX['seeds'])} (후보 {', '.join(f's{s}' for s in cands)})"


def report():
    m = load()
    qs = [q["id"] for q in QS["S"] + QS["E"]]
    print("시드 " + " ".join(q.split(".")[1][:10] for q in qs))
    for s in FX["seeds"]:
        print(f"s{s:<3} " + " ".join("".join(x[0] if x else "-" for x in votes(m, s, q)) for q in qs))
    print("다수결 맞음(8장 중): " + " · ".join(f"{q['q']} {sum(maj(votes(m, s, q['id'])) == '맞음' for s in FX['seeds'])}" for q in QS["S"] + QS["E"]))
    print(f"[GibeahRedraw] 거르기 틀림 {pick(m)[2]}")
    print(f"{LINE}: {conclude(m)}")


def key_img(k):
    """후보 키 「g:<시드>」(이 시도) | 「<시도>:<시드>」(다른 시도, task 403 d) → 그림 경로."""
    t, s = k.split(":")
    return img(int(s)) if t == "g" else os.path.join(os.path.dirname(OUT), t, f"s{s}.png")


def cand():
    from PIL import Image
    sys.argv += ["--set", "jordan-guide"]   # plain_words는 import 때 묶음을 읽는다 — 화면 틀·원문만 빌린다
    import plain_words as PW
    import make_cand_page as C
    m = load()
    if FX.get("cand"):   # task 403 d 시도(한 장 반복): 후보는 서로 다른 시도의 그림 — 고정 절 cand = [{try, seed, label}] 1위 먼저
        cands = [c["seed"] for c in FX["cand"]]
        one, two = (f"{c['try']}:{c['seed']}" for c in FX["cand"][:2])
        keys = [(f"{c['try']}:{c['seed']}", c["label"]) for c in FX["cand"]] + [("ref:0", FX["ref"]["label"])]
    else:
        ok, cands, _ = pick(m)
        assert len(cands) == 2, f"후보 2장 아님: {cands}"
        one, two = f"g:{cands[0]}", f"g:{cands[1]}"
        keys = [(f"g:{s}", f"새 명세 s{s}{'' if s in ok else ' (기계 불통과)'}") for s in FX["seeds"]] + [("ref:0", FX["ref"]["label"])]
    src = lambda k: os.path.expanduser(FX["ref"]["image"]) if k.startswith("ref:") else key_img(k)
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
    k = a[a["answer"]]
    t, s = k.split(":")[0], int(k.split(":")[1])
    shutil.copyfile(key_img(k), os.path.join(HERE, APPROVED))
    spec = approve.load_spec(SID)
    em = m if t == "g" else json.load(open(METRICS.replace(f"/{TRY}/", f"/{t}/"), encoding="utf-8"))
    if em.get("edit"):   # d 시도: 생성 뒤 국소 편집(edit.small-prop-orient)이면 편집 차례를 함께
        base_try = FX["edit"]["from"] if t == "g" else next(c for c in FX["cand"] if c["try"] == t).get("base", t)
        bm = json.load(open(METRICS.replace(f"/{TRY}/", f"/{base_try}/"), encoding="utf-8"))
        spec = approve.local_edit(spec, s, APPROVED, em["edit"][str(s)], "user", bm["prompt"])
    else:
        spec = approve.night_pick(spec, s, "base", APPROVED, "user", (em or m)["prompt"])
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
    with open(NOTES, encoding="utf-8") as fh:
        text = fh.read()
    if TRY:   # 시도 절(「## 시도 a1」 ~ 다음 「## 」) 안의 결론 줄만
        text = re.search(rf"^## 시도 {TRY}\b(.*?)(?=^## |\Z)", text, re.S | re.M).group(1)
    line = re.findall(rf"^{LINE}: (.+)$", text, re.M)
    if not err and line != [conclude(m)]:
        err.append(f"노트 {LINE} 줄 {line} ≠ 다시 셈 {conclude(m)}")
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
