#!/usr/bin/env python3
"""task#450 — 정본 참조 편집(2511 + Lightning, ADR 261017-152627)을 지금 화풍 기준으로 재검: 기브아 창 시드 11 한 장, C·E·W·T 갈래.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV gen_ref_edit_recheck.py edit [양자화]      # 편집 5번(사울 원본 · 다윗 E 위 · 다윗 W 위 · T 둘), 이미 있으면 건너뜀
  python3 gen_ref_edit_recheck.py eye <키> '<한 줄>'  # Claude 눈 「얼굴이 바뀌었나」 기록(키 = saul · david-E · david-W · T-saul · T-david)
  $VENV gen_ref_edit_recheck.py gram               # 사울·다윗 × C·E·W·T 머리 둘레 Gram 2·6층 거리 → metrics gram
  $VENV gen_ref_edit_recheck.py page               # 사람 화풍 화면(9문항) → ~/.local/biblemap-imggen/pages/ref-edit-recheck.html
  python3 gen_ref_edit_recheck.py record < 답.txt   # 「판정 문장 복사」 글 → metrics verdict(고정 절 판정 규칙)
  python3 gen_ref_edit_recheck.py stop "<사유>"     # 고정 절 정지 조건일 때만 — metrics `stop`

편집·마스크·좌우·되붙임은 gen_ref_edit_lightning·gen_ref_edit·gen_ref_edit_2511 그대로, 참조는 초상 하나(notes/REF-EDIT-RECHECK.md 고정 절).
산출은 레포 밖 ~/.local/biblemap-imggen/ref-edit-recheck/, 목록은 samples/ref-edit-recheck/metrics.json."""
import json, os, re, sys

from PIL import Image

import params
import derive_scene as D
import face_ab_heads as FH
import gen_ref_edit as G
import gen_ref_edit_2511 as R
import gen_ref_edit_lightning as L
import make_cast_v2_pilot_page as P

SID, SEED = params.REF_EDIT_RECHECK_SCENE
SC = "gibeah"
OUT = os.path.join(G.ROOT, "ref-edit-recheck")
METRICS = os.path.join(G.HERE, "samples", "ref-edit-recheck", "metrics.json")
BASE = os.path.join(G.ROOT, "face-lora-v4", "scene", f"C-s{SEED}.png")
SAUL, DAVID = params.REF_EDIT_RECHECK_WHO

# 358 장면표에 기브아가 없다 — 실행 때만 등록(make_mask·side가 읽는 표)
P.SC[SC] = SID
P.SIDE[SC] = params.REF_EDIT_RECHECK_SIDE
params.LORA_SCENE_SCENES[SC] = (SID, list(params.REF_EDIT_RECHECK_WHO))


def load():
    return json.load(open(METRICS, encoding="utf-8")) if os.path.exists(METRICS) else \
        {"scene": SID, "seed": SEED, "base": BASE, "model": L.NAME, "lora": params.REF_EDIT_LIGHTNING_LORA[1]}


def save(m):
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    with open(METRICS, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=1)


def costume(who):
    f = next(f for f in D.load(SID)["figures"] if f.get("cast") == who)
    return re.sub(r"^in ", "", f["costume"]["en"])   # 「wearing in a」 비문 방지(고정 절)


def look(who, arm):
    ident = params.REF_EDIT_RECHECK_SELF_LOOK[who] if arm == "T" else params.REF_EDIT_LIGHTNING_LOOK_IDENTITY[who]
    return ident + ", wearing " + costume(who)


def head_box(im, who):
    """448 head_box와 같은 길 — OWLv2 점수 0.05 이상 후보 중 그 인물 쪽 범위의 가장 큰 상자."""
    lo, hi = params.REF_EDIT_RECHECK_SIDE[who]
    f = [b for b, s in FH._faces(im) if s >= 0.05 and lo * im.width <= (b[0] + b[2]) / 2 <= hi * im.width]
    return max(f, key=lambda b: (b[2] - b[0]) * (b[3] - b[1])) if f else None


def head_crop(src, who, out):
    """→ 머리 상자(원래 화소) 또는 None. gen_face_detail.region 정사각 → 3배(448 head_crop 장면 쪽과 같음)."""
    import gen_face_detail as GF
    im = Image.open(src).convert("RGB")
    b = head_box(im, who)
    if b is None:
        return None
    c = im.crop(tuple(GF.region(b, *im.size)))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    c.resize((c.width * 3, c.height * 3), Image.LANCZOS).save(out)
    return [round(v) for v in b]


def edit_one(q, who, arm, src, raw, out=None):
    """src 위에서 who를 편집 → raw(전체 편집). out이 있으면 몸 상자만 src에 되붙여 out(E)."""
    mk = G.make_mask(SC, who, BASE, os.path.join(OUT, "mask", f"{who}.png"))
    sd_side = R.side(SC, who, BASE)
    if arm == "T":
        ref = os.path.join(OUT, "self-ref", f"{who}.png")
        if not os.path.exists(ref):
            head_crop(BASE, who, ref)
        refs = [ref]
    else:
        refs = [os.path.join(G.HERE, "frozen", f"{who}.png")]
    lk = look(who, arm)
    prompt = params.REF_EDIT_RECHECK_PROMPT.format(side=sd_side, look=lk)
    e = {**L.run_edit(q, src, who, SEED, prompt, raw, refs=refs), **mk, "arm": arm, "src": src, "side": sd_side,
         "refs": refs, "look": lk, "prompt": prompt}
    if e["status"] == "ok":
        e["targeted"], e["diff_in"], e["diff_out"] = L.targeted(raw, src, mk["mask_box"])
        if out:
            e["resized"] = R.paste(raw, src, mk["mask"], out)
            e["out"] = out
            e["mask_diff"] = R.mask_diff(out, src, mk["mask_box"])
        print(f"  [RefEditRecheck] {arm} {who} targeted {e['targeted']} (안 {e['diff_in']} / 밖 {e['diff_out']}) side {sd_side}", flush=True)
    return e


def edit(q):
    """편집 차례: saul(원본 → E 되붙임 · W 원본) → david-E · david-W → T-saul → T-david. 첫 편집 600초 초과·오류면 멈춤(정지 조건은 사람이 q6로 다시)."""
    m = load()
    m.setdefault("edits", {})
    d = lambda *p: os.path.join(OUT, *p)
    plan = [("saul", SAUL, "EW", BASE, d("raw", "saul.png"), d("E", "saul.png")),
            ("david-E", DAVID, "E", d("E", "saul.png"), d("raw", "david-E.png"), d("E", "final.png")),
            ("david-W", DAVID, "W", d("raw", "saul.png"), d("W", "final.png"), None),
            ("T-saul", SAUL, "T", BASE, d("T", "saul.png"), None),
            ("T-david", DAVID, "T", d("T", "saul.png"), d("T", "final.png"), None)]
    for i, (key, who, arm, src, raw, out) in enumerate(plan):
        old = m["edits"].get(key)
        if old and old.get("status") == "ok" and os.path.exists(raw) and (out is None or os.path.exists(out)):
            continue
        e = edit_one(q, who, arm, src, raw, out)
        m["edits"][key] = e
        save(m)
        if e["status"] != "ok" or (i == 0 and e["sec"] > params.REF_EDIT_LIGHTNING_MAX_SEC):
            print(f"[RefEditRecheck] 정지 조건: {key} {e['status']} {e['sec']}s (q{q})", flush=True)
            return
    m["arms"] = {"C": BASE, "E": d("E", "final.png"), "W": d("W", "final.png"), "T": d("T", "final.png")}
    m["sec"] = {k: e["sec"] for k, e in m["edits"].items()}
    m["look"] = {k: e["look"] for k, e in m["edits"].items()}
    save(m)
    print(f"[RefEditRecheck] 편집 5/5 · 초 {m['sec']}", flush=True)


def gram():
    import gen_lora_v5 as V5
    m = load()
    crops, boxes = {}, {}
    for who in (SAUL, DAVID):
        for arm, p in m["arms"].items():
            o = os.path.join(OUT, "heads", f"{who}-{arm}.png")
            b = head_crop(p, who, o)
            boxes[f"{who}-{arm}"] = b
            if b and max(b[2] - b[0], b[3] - b[1]) >= params.REF_EDIT_RECHECK_MIN_HEAD:
                crops[(who, arm)] = o
    Gm = V5.gram(list(crops.values()))
    res = {}
    for who in (SAUL, DAVID):
        res[who] = {}
        for arm in ("E", "W", "T"):
            if (who, "C") in crops and (who, arm) in crops:
                res[who][arm] = {k: round(V5.dist(Gm[crops[(who, arm)]][k], Gm[crops[(who, "C")]][k]), 5) for k in params.LORA_V5_LAYERS}
            else:
                res[who][arm] = "측정 불가"
    m["gram"], m["head_boxes"] = res, boxes
    save(m)
    for who in res:
        print(who, " · ".join(f"{a} {v}" for a, v in res[who].items()), "| 상자", {k: v for k, v in boxes.items() if k.startswith(who)})


NAME = {SAUL: "사울", DAVID: "다윗"}
PAGE = os.path.join(G.ROOT, "pages", "ref-edit-recheck.html")
ASKED = ("E", "W", "T")


def page():
    """폰용 화풍 화면 — 머리 둘레 6(섞음) + 전체 3(섞음), 위 = C · 아래 = 갈래, 원래 화소 같은 배율(화소 적은 쪽이 작게)."""
    import random
    import gen_face_detail as GF
    import make_face_judge_v2 as F
    m = load()
    heads, whole, key = [], [], {}
    for arm in ASKED:
        for who in (SAUL, DAVID):
            c, a = (Image.open(m["arms"][x]).convert("RGB") for x in ("C", arm))
            c, a = (im.crop(tuple(GF.region(head_box(im, who), *im.size))) for im in (c, a))
            big = max(c.width, a.width)
            k = 640 / big
            c, a = (x.resize((round(x.width * k), round(x.height * k)), Image.LANCZOS) for x in (c, a))
            heads.append({"arm": arm, "who": who, "tag": "화풍", "wide": True, "q": f"{NAME[who]} 머리 둘레 — 아래 그림이 위(기준)와 같은 화풍인가요?",
                          "hint": "같은 장면·같은 시드를 줄이지 않고 원래 화소 그대로 같은 배율로 키웠습니다(머리를 작게 그린 그림은 작게 보입니다). 연필 선 모양·색연필 결·색 진함이 같은지만 봅니다(같은 사람인지는 묻지 않습니다).",
                          "yes": "같은 화풍", "no": "다른 화풍", "refs": [F.uri(c, 900)], "caps": ["기준 — 편집 전 그림"], "img": F.uri(a, 900),
                          "rw": round(100 * c.width / round(big * k)), "iw": round(100 * a.width / round(big * k)), "px": [c.width, a.width]})
        whole.append({"arm": arm, "who": "whole", "tag": "화풍", "wide": True, "q": "전체 그림 — 아래 그림이 위(기준)와 같은 화풍인가요?",
                      "hint": "두 그림 모두 원래 크기(1216×640) 그대로입니다. 연필 선 모양·색연필 결·색 진함·종이 바탕이 같은지만 봅니다(인물이 누구인지는 묻지 않습니다).",
                      "yes": "같은 화풍", "no": "다른 화풍", "refs": [F.uri(Image.open(m["arms"]["C"]), 1216)], "caps": ["기준 — 편집 전 그림"],
                      "img": F.uri(Image.open(m["arms"][arm]), 1216)})
    rnd = random.Random(params.REF_EDIT_RECHECK_SHUFFLE_SEED)
    rnd.shuffle(heads)
    rnd.shuffle(whole)
    qs = heads + whole
    for i, q in enumerate(qs, 1):   # 갈래 이름은 화면·답에 안 나오게 문항 번호로만
        key[f"Q{i}"] = [q.pop("arm"), q.pop("who")]
        q["id"] = f"Q{i}"
    verses = [[r, t, r == "18:11"] for r, t, _ in F.scripture() if r in ("18:10", "18:11")]
    html = (F.page(qs, verses).replace("<title>얼굴 판정 v2</title>", "<title>참조 편집 화풍 판정</title>")
            .replace("판정 face-judge-v2", "판정 ref-edit-recheck").replace("18:6-11", "18:10-11")
            .replace(".refs figure.one { max-width: 320px; margin: 0 auto }", ".refs figure.one { margin: 0 }")
            .replace('<img src="${r}"', '<img style="width:${q.rw || 100}%;margin:0 auto" src="${r}"')
            .replace('<img src="${q.img}" alt="판정할 그림">', '<img style="width:${q.iw || 100}%;margin:0 auto" src="${q.img}" alt="판정할 그림">'))
    os.makedirs(os.path.dirname(PAGE), exist_ok=True)
    open(PAGE, "w", encoding="utf-8").write(html)
    m["page"] = {"path": PAGE, "n": len(qs), "key": key, "mb": round(os.path.getsize(PAGE) / 1e6, 2)}
    save(m)
    print(PAGE, len(qs), "문항", m["page"]["mb"], "MB")


def verdict(by):
    """고정 절 판정 규칙 → (갈래별 통과, 판정 한 줄). by = {갈래: {사울·다윗·whole: 답}}."""
    if any(v == "no" for v in by.get("T", {}).values()):
        return [], "미채택 — 편집기 통과만으로 화풍이 바뀜"
    ok = [a for a in ("E", "W") if len(by.get(a, {})) == 3 and all(v == "yes" for v in by[a].values())]
    return ok, (f"화풍 통과({', '.join(ok)})" if ok else "미채택 — 원래 화소 화풍에서 막힘")


def record(text):
    ans = json.loads(re.search(r"\{.*?\}", text.split("판정 ref-edit-recheck", 1)[-1], re.S).group(0))
    m = load()
    by = {}
    for q, (arm, who) in m["page"]["key"].items():
        by.setdefault(arm, {})[who] = ans.get(q)
    ok, line = verdict(by)
    m["verdict"] = {"answers": by, "pass": ok, "line": line}
    save(m)
    open(os.path.join(os.path.dirname(METRICS), "verdict.txt"), "w", encoding="utf-8").write(text.strip() + "\n")
    print(json.dumps(by, ensure_ascii=False), "→", line)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "edit":
        edit(int(sys.argv[2]) if len(sys.argv) > 2 else params.REF_EDIT_LIGHTNING_QUANTS[0])
    elif cmd == "eye":
        m = load()
        m.setdefault("eye", {})[sys.argv[2]] = sys.argv[3]
        save(m)
    elif cmd == "gram":
        gram()
    elif cmd == "page":
        page()
    elif cmd == "record":
        record(sys.stdin.read())
    elif cmd == "stop":
        m = load()
        m["stop"] = sys.argv[2]
        save(m)
