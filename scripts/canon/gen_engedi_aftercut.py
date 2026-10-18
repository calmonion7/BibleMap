#!/usr/bin/env python3
"""엔게디 「막 자른 뒤」 — 칼날이 옷을 가르는 순간은 세 수단 모두 못 그려(notes/ENGEDI-HANDFIX.md),
사용자 선택(2026-10-18)으로 장면 순간을 「다윗이 막 베어 낸 옷자락 조각을 든 모습」으로 바꾼다. 365 B(사울 등 돌림, 마주 봄 0) 위에 C diff.
  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  HF_HUB_OFFLINE=1 $VENV gen_engedi_aftercut.py --check   # 토큰만(GPU 0)
  HF_HUB_OFFLINE=1 $VENV gen_engedi_aftercut.py           # C × params.REF_EDIT_SEEDS
메모리 명세에만 적용(명세 파일은 채택 뒤에만 고침). 산출 ~/.local/biblemap-imggen/engedi-aftercut/C/s<시드>.png."""
import argparse, copy, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.expanduser("~/.local/biblemap-imggen/engedi-aftercut")
METRICS = os.path.join(HERE, "samples", "engedi-aftercut", "metrics.json")
# (어디, 언어, old, new) — B 위에 적용
DIFF_C = [
    ("david.gesture", "en", "one hand holding the hem of the king's cloak that lies on the ground, the other hand cutting it with a small knife",
     "one hand holding up the corner piece he has just cut off the king's cloak, the other hand holding a small knife"),
    ("david.gesture", "ko", "한 손으로 땅에 끌린 사울의 겉옷자락을 잡고 다른 손의 작은 칼로 가만히 벤다",
     "방금 벤 사울의 겉옷자락 조각을 한 손에 들고 다른 손에 작은 칼을 쥐었다"),
    ("david.gaze", "en", "looking down at the hem he is cutting", "looking down at the cut-off piece in his hand"),
    ("david.gaze", "ko", "자르는 옷자락을 내려다봄", "손에 든 잘린 옷자락 조각을 내려다봄"),
    ("saul.costume", "en", "its hem trailing on the ground still whole and being cut at one corner by the man to the left",
     "its hem trailing on the ground with one corner freshly cut off"),
    ("saul.costume", "ko", "아직 온전한 어두운 양모 겉옷(왕의 겉옷, 24:4) — 자락이 땅에 끌려 다윗이 베는 중",
     "어두운 양모 겉옷(왕의 겉옷, 24:4) — 땅에 끌린 자락의 귀퉁이 하나가 막 잘려 나감"),
    ("relation", "en", "and cuts the corner of the cloak trailing on the ground", "and has just cut off a corner of the cloak trailing on the ground"),
    ("relation", "ko", "땅에 끌린 겉옷자락을 벤다", "땅에 끌린 겉옷자락 귀퉁이를 막 베어 냈다"),
]


def out_path(seed):
    return os.path.join(OUT, "C", f"s{seed}.png")


def treat(spec):
    import derive_scene as ds
    import gen_engedi_gaze as Z
    import gen_engedi_backhand as W
    s = copy.deepcopy(spec)
    W.apply(s, Z.DIFF_B)
    fig = {f["cast"]: f for f in s["figures"]}
    for where, lang, old, new in DIFF_C:
        if where == "relation":
            obj = s["relation"]
        else:
            who, key = where.split(".")
            obj = fig[who][key]
        assert obj[lang].count(old) == 1, (where, lang, old)
        obj[lang] = obj[lang].replace(old, new)
    assert "screen_light" in s and not ds.check_whole(s), ds.check_whole(s)
    return s


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--seeds", type=int, nargs="+")
    a = ap.parse_args()
    import params
    import derive_scene as ds
    import check_scenes as cs
    import gen_ref_edit as G
    import gen_prompt_512 as P
    sys.path.insert(0, os.path.join(HERE, "batch"))
    n = cs.zimage_tokens()
    p = ds.whole_prompt(treat(ds.load(G.SC["engedi"])))
    tok = n(p)
    print(f"[EngediAftercut] 토큰 {tok} / {cs.WHOLE_MAX}", flush=True)
    assert tok <= cs.WHOLE_MAX, tok
    if a.check:
        sys.exit(0)
    seeds = a.seeds or params.REF_EDIT_SEEDS
    os.makedirs(os.path.join(OUT, "C"), exist_ok=True)
    js = [{"prompt": p, "seed": s, "w": P.SIZE[0], "h": P.SIZE[1], "out": out_path(s)} for s in seeds]
    todo = [j for j in js if not os.path.exists(j["out"])]
    print(f"[EngediAftercut] {len(js)}장 중 {len(todo)}장 생성", flush=True)
    if todo:
        import run_scene
        secs = run_scene.gen_zimage(todo, OUT)
        print(f"[EngediAftercut] 완료 {len(secs)}장 합 {sum(secs):.0f}s", flush=True)
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    json.dump({"prompt": p, "tokens": tok, "done": [s for s in seeds if os.path.exists(out_path(s))]},
              open(METRICS, "w"), ensure_ascii=False, indent=1)
