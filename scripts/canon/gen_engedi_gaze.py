#!/usr/bin/env python3
"""task 365 — 엔게디 시선 축: 처치 A(다윗 시선 = 자르는 옷자락 내려다봄)·B(A + 사울 부정문 → 등 돌림)를 같은 시드로 그린다.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV gen_engedi_gaze.py --seeds 202   # S0: A·B 각 한 장
  $VENV gen_engedi_gaze.py               # A·B × params.REF_EDIT_SEEDS

고정 절(notes/ENGEDI-GAZE.md)의 문구 diff를 **메모리 명세에만** 적용하고 derive_scene.whole_prompt로 파생한다(명세 파일은 채택 뒤에만 고침).
old 구절이 명세에 정확히 한 번 없으면 멈춘다. screen_light는 건드리지 않는다(PROMPTING 20). 생성 경로·캔버스는 364와 같다.
산출은 레포 밖 <out>/<A|B>/s<시드>.png, 이미 있으면 건너뜀. 프롬프트·토큰 수·그린 시드 → samples/engedi-gaze/metrics.json.
대조: r2 = task 363 r2 그림(prompt-512/engedi, 지금 명세 파생 그대로) — 다시 그리지 않는다.
"""
import argparse, copy, json, os, sys

import params
import derive_scene as ds
import check_scenes as cs
import gen_ref_edit as G
import gen_prompt_512 as P

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "batch"))
OUT = os.path.expanduser("~/.local/biblemap-imggen/engedi-gaze")
METRICS = os.path.join(HERE, "samples", "engedi-gaze", "metrics.json")
GAZE_A = {"ko": "자르는 옷자락을 내려다봄", "en": "looking down at the hem he is cutting",
          "verse": "삼상 24:4 「가만히 베니라」 · 시선 본문 밖 · 저작자 정함(2026-10-18 사용자 기준)"}
# 고정 절 문구 diff(B) — (어디, 언어, old, new). A 위에 적용.
DIFF_B = [
    ("saul.gesture", "en", "facing toward the cave mouth, not looking back, his long cloak",
     "facing toward the cave mouth, his back to the man on the left, his long cloak"),
    ("relation", "en", "Saul crouches looking toward the cave mouth and does not look back;",
     "Saul crouches looking toward the cave mouth with his back to David;"),
    ("relation", "en", "; their eyes do not meet", ""),
    ("saul.gesture", "ko", "어귀 쪽을 바라보고 뒤를 돌아보지 않는다", "어귀 쪽을 바라보며 등을 왼쪽 사람 쪽으로 둔다"),
    ("relation", "ko", "사울은 어귀 쪽을 바라보며 웅크려 있고 뒤를 돌아보지 않으며,", "사울은 어귀 쪽을 바라보며 다윗에게 등을 둔 채 웅크려 있고,"),
    ("relation", "ko", ". 둘의 시선은 마주치지 않는다", ""),
]


def out_path(t, seed):
    return os.path.join(OUT, t, f"s{seed}.png")


def treat(spec, t):
    """메모리 명세에 처치 t 적용(채택 시 명세에 그대로 옮길 값)."""
    s = copy.deepcopy(spec)
    fig = {f["cast"]: f for f in s["figures"]}
    assert fig["david"]["gaze"] == "saul", fig["david"]["gaze"]
    fig["david"]["gaze"] = dict(GAZE_A)
    if t == "B":
        for where, lang, old, new in DIFF_B:
            obj = s["relation"] if where == "relation" else fig["saul"]["gesture"]
            assert obj[lang].count(old) == 1, (where, lang, old)
            obj[lang] = obj[lang].replace(old, new)
    assert "screen_light" in s and not ds.check_whole(s), ds.check_whole(s)
    return s


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--treat", nargs="+", default=["A", "B"], choices=["A", "B"])
    ap.add_argument("--seeds", type=int, nargs="+", default=params.REF_EDIT_SEEDS)
    a = ap.parse_args()
    n = cs.zimage_tokens()
    base = ds.load(G.SC["engedi"])
    m = json.load(open(METRICS)) if os.path.exists(METRICS) else {"prompts": {}, "tokens": {}, "done": {}}
    js = []
    for t in a.treat:
        p = ds.whole_prompt(treat(base, t))
        m["prompts"][t], m["tokens"][t] = p, n(p)
        assert m["tokens"][t] <= cs.WHOLE_MAX, (t, m["tokens"][t])
        os.makedirs(os.path.join(OUT, t), exist_ok=True)
        js += [{"prompt": p, "seed": s, "w": P.SIZE[0], "h": P.SIZE[1], "out": out_path(t, s), "treat": t} for s in a.seeds]
    todo = [j for j in js if not os.path.exists(j["out"])]
    print(f"[EngediGaze] {len(js)}장 중 {len(todo)}장 생성 · 토큰 {m['tokens']}", flush=True)
    if todo:
        import run_scene
        secs = run_scene.gen_zimage([{k: v for k, v in j.items() if k != "treat"} for j in todo], OUT)
        print(f"[EngediGaze] 완료 {len(secs)}장 합 {sum(secs):.0f}s", flush=True)
    for j in js:
        d = m["done"].setdefault(j["treat"], [])
        if os.path.exists(j["out"]) and j["seed"] not in d:
            d.append(j["seed"])
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    json.dump(m, open(METRICS, "w"), ensure_ascii=False, indent=1)
