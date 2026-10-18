#!/usr/bin/env python3
"""task 366 — 엔게디 마주 봄: 365 B를 둘로 나눈 처치 B1(등 돌림 긍정문만)·B2(맞보기 절 빼기만)를 같은 시드로 그린다.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV gen_engedi_away.py --seeds 202   # S0: B1·B2 각 한 장
  $VENV gen_engedi_away.py               # B1·B2 × params.REF_EDIT_SEEDS
  python3 gen_engedi_away.py --tally     # 판정 원문(notes/ENGEDI-AWAY.md) + screens → 집계·결론 줄 재계산

바탕은 지금 명세(=365 A 채택본). 고정 절(notes/ENGEDI-AWAY.md)의 문구 diff를 **메모리 명세에만** 적용하고 derive_scene.whole_prompt로 파생한다.
old 구절이 명세에 정확히 한 번 없으면 멈춘다. 다윗 gaze·screen_light는 건드리지 않는다. 생성 경로·캔버스는 365와 같다.
산출은 레포 밖 <out>/<B1|B2>/s<시드>.png, 이미 있으면 건너뜀. 대조 A·B(365 그림)는 다시 그리지 않는다.
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.expanduser("~/.local/biblemap-imggen/engedi-away")
METRICS = os.path.join(HERE, "samples", "engedi-away", "metrics.json")
NOTES = os.path.join(HERE, "notes", "ENGEDI-AWAY.md")
GAZE_A_EN = "looking down at the hem he is cutting"
# 고정 절 문구 diff — (어디, 언어, old, new). 지금 명세 위에 적용.
DIFF = {
    "B1": [
        ("saul.gesture", "en", "facing toward the cave mouth, not looking back, his long cloak",
         "facing toward the cave mouth, his back to David, his long cloak"),
        ("saul.gesture", "ko", "어귀 쪽을 바라보고 뒤를 돌아보지 않는다", "어귀 쪽을 바라보며 다윗에게 등을 둔다"),
        ("relation", "en", "Saul crouches looking toward the cave mouth and does not look back;",
         "Saul crouches looking toward the cave mouth with his back to David;"),
        ("relation", "ko", "사울은 어귀 쪽을 바라보며 웅크려 있고 뒤를 돌아보지 않으며,", "사울은 어귀 쪽을 바라보며 다윗에게 등을 둔 채 웅크려 있고,"),
    ],
    "B2": [
        ("relation", "en", "; their eyes do not meet", ""),
        ("relation", "ko", ". 둘의 시선은 마주치지 않는다", ""),
    ],
}
ARMS = ("A", "B1", "B2", "B")      # 판정 페이지의 팔(A·B는 365 그림)
AXES = (("G-face", "마주 봄"), ("G-look", "다윗 시선"), ("G-hand", "손·칼"), ("G-guard", "가드"))


def out_path(t, seed):
    if t in ("A", "B"):
        return os.path.expanduser(f"~/.local/biblemap-imggen/engedi-gaze/{t}/s{seed}.png")
    return os.path.join(OUT, t, f"s{seed}.png")


def treat(spec, t):
    """메모리 명세에 처치 t 적용(채택 시 명세에 그대로 옮길 값)."""
    import copy
    import derive_scene as ds
    s = copy.deepcopy(spec)
    fig = {f["cast"]: f for f in s["figures"]}
    assert fig["david"]["gaze"]["en"] == GAZE_A_EN, fig["david"]["gaze"]
    for where, lang, old, new in DIFF[t]:
        obj = s["relation"] if where == "relation" else fig["saul"]["gesture"]
        assert obj[lang].count(old) == 1, (where, lang, old)
        obj[lang] = obj[lang].replace(old, new)
    assert "screen_light" in s and not ds.check_whole(s), ds.check_whole(s)
    return s


def tally(m, raw):
    """판정 원문 → 팔마다 8장 중 눌린 수 · 결론 줄(고정 절 판정 규칙)."""
    pressed = {sid: {int(x) for x in re.search(rf"\[{sid}\][^\n]*→ ?([\d, ]*)", raw).group(1).replace(" ", "").split(",") if x}
               for sid, _ in AXES}
    cnt = {sid: {a: sum(1 for e in m["screens"][sid] if e["kind"] == a and e["n"] in pressed[sid]) for a in ARMS} for sid, _ in AXES}
    ref = {sid: any(e["kind"] == "ref" and e["n"] in pressed[sid] for e in m["screens"][sid]) for sid, _ in AXES}
    F, G, H, X = (cnt[s] for s, _ in AXES)
    ok = [t for t in ("B1", "B2") if F[t] <= F["A"] - 2 and H[t] <= H["A"] + 1 and X[t] <= X["A"] + 1 and G[t] <= G["A"] + 1]
    pick = min(ok, key=lambda t: (F[t], H[t], X[t], t != "B2")) if ok else None
    line = f"결론: {pick + ' 채택' if pick else '미채택'} · " + " · ".join(
        f"{lab} " + "·".join(f"{a} {cnt[sid][a]}" for a in ARMS) for sid, lab in AXES)
    return cnt, ref, ok, line


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--treat", nargs="+", default=["B1", "B2"], choices=["B1", "B2"])
    ap.add_argument("--seeds", type=int, nargs="+")
    ap.add_argument("--tally", action="store_true")
    a = ap.parse_args()
    if a.tally:
        raw = open(NOTES, encoding="utf-8").read().split("## 사람 판정 원문", 1)[1]
        cnt, ref, ok, line = tally(json.load(open(METRICS)), raw)
        for sid, lab in AXES:
            print(f"{lab}: {cnt[sid]} · 기준 눌림 {ref[sid]}")
        print("통과:", ok or "없음")
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
    js = []
    for t in a.treat:
        p = ds.whole_prompt(treat(base, t))
        m["prompts"][t], m["tokens"][t] = p, n(p)
        assert m["tokens"][t] <= cs.WHOLE_MAX, (t, m["tokens"][t])
        os.makedirs(os.path.join(OUT, t), exist_ok=True)
        js += [{"prompt": p, "seed": s, "w": P.SIZE[0], "h": P.SIZE[1], "out": out_path(t, s), "treat": t} for s in seeds]
    todo = [j for j in js if not os.path.exists(j["out"])]
    print(f"[EngediAway] {len(js)}장 중 {len(todo)}장 생성 · 토큰 {m['tokens']}", flush=True)
    if todo:
        import run_scene
        secs = run_scene.gen_zimage([{k: v for k, v in j.items() if k != "treat"} for j in todo], OUT)
        print(f"[EngediAway] 완료 {len(secs)}장 합 {sum(secs):.0f}s", flush=True)
    for j in js:
        d = m["done"].setdefault(j["treat"], [])
        if os.path.exists(j["out"]) and j["seed"] not in d:
            d.append(j["seed"])
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    json.dump(m, open(METRICS, "w"), ensure_ascii=False, indent=1)
