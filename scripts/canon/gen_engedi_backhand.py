#!/usr/bin/env python3
"""task 367 — 엔게디 마주 봄 귀속·손: 365 B 위에 B′(Bp, 사울 몸짓 `David` 낱말)·Bh(다윗이 자락을 들어 올림)를 같은 시드로 그린다.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV gen_engedi_backhand.py --seeds 202   # S0: Bp·Bh 각 한 장
  $VENV gen_engedi_backhand.py               # Bp·Bh × params.REF_EDIT_SEEDS
  python3 gen_engedi_backhand.py --tally     # 판정 원문(notes/ENGEDI-BACKHAND.md) + screens → 집계·결론 줄 재계산

바탕은 지금 명세(=365 A 채택본). 365 `gen_engedi_gaze.DIFF_B`로 B를 만들고(365 metrics의 B 프롬프트와 글자까지 같은지 확인),
그 위에 고정 절(notes/ENGEDI-BACKHAND.md)의 Bp·Bh diff를 **메모리 명세에만** 적용한다. old 구절이 정확히 한 번 없으면 멈춘다.
산출은 레포 밖 <out>/<Bp|Bh>/s<시드>.png, 이미 있으면 건너뜀. 대조 A·B(365 그림)는 다시 그리지 않는다.
"""
import argparse, copy, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.expanduser("~/.local/biblemap-imggen/engedi-backhand")
METRICS = os.path.join(HERE, "samples", "engedi-backhand", "metrics.json")
GAZE_METRICS = os.path.join(HERE, "samples", "engedi-gaze", "metrics.json")
NOTE_MD = os.path.join(HERE, "notes", "ENGEDI-BACKHAND.md")
GAZE_A_EN = "looking down at the hem he is cutting"
# 고정 절 문구 diff — (어디, 언어, old, new). B 위에 적용.
DIFF = {
    "Bp": [
        ("saul.gesture", "en", "facing toward the cave mouth, his back to the man on the left, his long cloak",
         "facing toward the cave mouth, his back to David, his long cloak"),
        ("saul.gesture", "ko", "어귀 쪽을 바라보며 등을 왼쪽 사람 쪽으로 둔다", "어귀 쪽을 바라보며 다윗에게 등을 둔다"),
    ],
    "Bh": [
        ("david.gesture", "en", "one hand holding the hem of the king's cloak that lies on the ground, the other hand cutting it with a small knife",
         "one hand lifting the hem of the king's cloak off the ground, the other hand cutting it with a small knife"),
        ("david.gesture", "ko", "한 손으로 땅에 끌린 사울의 겉옷자락을 잡고 다른 손의 작은 칼로 가만히 벤다",
         "한 손으로 사울의 겉옷자락을 땅에서 들어 올리고 다른 손의 작은 칼로 가만히 벤다"),
    ],
}
ARMS = ("A", "B", "Bp", "Bh")      # 판정 페이지의 팔(A·B는 365 그림)
AXES = (("G-face", "마주 봄"), ("G-look", "다윗 시선"), ("G-hand", "손·칼"), ("G-guard", "가드"))


def out_path(t, seed):
    if t in ("A", "B"):
        return os.path.expanduser(f"~/.local/biblemap-imggen/engedi-gaze/{t}/s{seed}.png")
    return os.path.join(OUT, t, f"s{seed}.png")


def apply(s, diff):
    fig = {f["cast"]: f for f in s["figures"]}
    for where, lang, old, new in diff:
        obj = s["relation"] if where == "relation" else fig[where.split(".")[0]]["gesture"]
        assert obj[lang].count(old) == 1, (where, lang, old)
        obj[lang] = obj[lang].replace(old, new)


def treat(spec, t):
    """메모리 명세에 B(365) + 처치 t 적용(채택 시 명세에 그대로 옮길 값). t == "B"면 B만."""
    import derive_scene as ds
    import gen_engedi_gaze as Z
    s = copy.deepcopy(spec)
    fig = {f["cast"]: f for f in s["figures"]}
    assert fig["david"]["gaze"]["en"] == GAZE_A_EN, fig["david"]["gaze"]
    apply(s, Z.DIFF_B)
    if t != "B":
        apply(s, DIFF[t])
    assert "screen_light" in s and not ds.check_whole(s), ds.check_whole(s)
    return s


def tally(m, raw):
    """판정 원문 → 팔마다 8장 중 눌린 수 · 결론 줄(고정 절 판정 규칙)."""
    pressed = {sid: {int(x) for x in re.search(rf"\[{sid}\][^\n]*→ ?([\d, ]*)", raw).group(1).replace(" ", "").split(",") if x}
               for sid, _ in AXES}
    cnt = {sid: {a: sum(1 for e in m["screens"][sid] if e["kind"] == a and e["n"] in pressed[sid]) for a in ARMS} for sid, _ in AXES}
    ref = {sid: any(e["kind"] == "ref" and e["n"] in pressed[sid] for e in m["screens"][sid]) for sid, _ in AXES}
    F, G, H, X = (cnt[s] for s, _ in AXES)
    ok = F["Bh"] <= F["A"] - 2 and H["Bh"] <= H["A"] + 1 and X["Bh"] <= X["A"] + 1 and G["Bh"] <= G["A"] + 1
    attr = "판정 불가" if F["B"] >= 2 else "David 낱말" if F["Bp"] - F["B"] >= 2 else "조합"
    line = f"결론: {'Bh 채택' if ok else '미채택'} · 귀속 {attr} · " + " · ".join(
        f"{lab} " + "·".join(f"{a} {cnt[sid][a]}" for a in ARMS) for sid, lab in AXES)
    return cnt, ref, ok, line


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--treat", nargs="+", default=["Bp", "Bh"], choices=["Bp", "Bh"])
    ap.add_argument("--seeds", type=int, nargs="+")
    ap.add_argument("--tally", action="store_true")
    a = ap.parse_args()
    if a.tally:
        raw = open(NOTE_MD, encoding="utf-8").read().split("## 사람 판정 원문", 1)[1]
        cnt, ref, ok, line = tally(json.load(open(METRICS)), raw)
        for sid, lab in AXES:
            print(f"{lab}: {cnt[sid]} · 기준 눌림 {ref[sid]}")
        print("Bh 통과:", ok)
        print(line)
        sys.exit(0)
    import params
    import derive_scene as ds
    import check_scenes as cs
    import gen_ref_edit as G
    import gen_prompt_512 as P
    sys.path.insert(0, os.path.join(HERE, "batch"))
    seeds = a.seeds or params.REF_EDIT_SEEDS
    n = cs.zimage_tokens()
    base = ds.load(G.SC["engedi"])
    m = json.load(open(METRICS)) if os.path.exists(METRICS) else {"prompts": {}, "tokens": {}, "done": {}}
    m["b_matches_365"] = ds.whole_prompt(treat(base, "B")) == json.load(open(GAZE_METRICS))["prompts"]["B"]
    assert m["b_matches_365"], "B 파생이 365 B 프롬프트와 다르다"
    js = []
    for t in a.treat:
        p = ds.whole_prompt(treat(base, t))
        m["prompts"][t], m["tokens"][t] = p, n(p)
        assert m["tokens"][t] <= cs.WHOLE_MAX, (t, m["tokens"][t])
        os.makedirs(os.path.join(OUT, t), exist_ok=True)
        js += [{"prompt": p, "seed": s, "w": P.SIZE[0], "h": P.SIZE[1], "out": out_path(t, s), "treat": t} for s in seeds]
    todo = [j for j in js if not os.path.exists(j["out"])]
    print(f"[EngediBackhand] {len(js)}장 중 {len(todo)}장 생성 · 토큰 {m['tokens']}", flush=True)
    if todo:
        import run_scene
        secs = run_scene.gen_zimage([{k: v for k, v in j.items() if k != "treat"} for j in todo], OUT)
        print(f"[EngediBackhand] 완료 {len(secs)}장 합 {sum(secs):.0f}s", flush=True)
    for j in js:
        d = m["done"].setdefault(j["treat"], [])
        if os.path.exists(j["out"]) and j["seed"] not in d:
            d.append(j["seed"])
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    json.dump(m, open(METRICS, "w"), ensure_ascii=False, indent=1)
