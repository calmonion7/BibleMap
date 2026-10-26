#!/usr/bin/env python3
"""task 364 — 엔게디 「굴 어둠·빛」: 처치 A(밝음 낱말 빼기)·B(A + 먼 굴 입구)를 같은 시드로 그린다.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV gen_engedi_dark.py --seeds 7   # S0: A·B 각 한 장
  $VENV gen_engedi_dark.py             # A·B × params.REF_EDIT_SEEDS

고정 절(notes/ENGEDI-DARK.md)의 문구 diff를 **메모리 명세에만** 적용하고 derive_scene.whole_prompt로 파생한다(명세 파일은 채택 뒤에만 고침).
old 구절이 명세에 정확히 한 번 없으면 멈춘다. 생성 경로·캔버스는 363과 같다(Z-Image-Turbo, 1216×640).
산출은 레포 밖 <out>/<A|B>/s<시드>.png, 이미 있으면 건너뜀. 프롬프트·토큰 수·그린 시드 → samples/engedi-dark/metrics.json.
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
OUT = os.path.expanduser("~/.local/biblemap-imggen/engedi-dark")
METRICS = os.path.join(HERE, "samples", "engedi-dark", "metrics.json")
# 고정 절 문구 diff — (필드, old, new). B는 A 위에 적용.
EN_A = ("with the cave mouth only a small bright opening far away at the right edge;",
        "with the cave mouth only a small opening far away at the right edge;")
EN_B = (EN_A[1], "with the cave mouth only a tiny distant opening at the far end of a long dark passage on the right;")
KO_A = ("굴 어귀는 화면 오른쪽 멀리 작고 밝은 구멍이다", "굴 어귀는 화면 오른쪽 멀리 작은 구멍이다")
KO_B = (KO_A[1], "굴 어귀는 화면 오른쪽 긴 어두운 통로 끝 멀리 아주 작은 구멍이다")
DIFFS = {"A": [EN_A], "B": [EN_A, EN_B]}
KO = {"A": [KO_A], "B": [KO_A, KO_B]}


def r2_path(seed):
    return P.new_path("engedi", seed)


def out_path(t, seed):
    return os.path.join(OUT, t, f"s{seed}.png")


def treat(spec, t):
    """메모리 명세에 처치 t 적용 — en·ko 구절 교체 + screen_light 삭제(채택 시 명세에 그대로 옮길 값)."""
    s = copy.deepcopy(spec)
    wb = s["whole_background"]
    for lang, steps in (("en", DIFFS[t]), ("ko", KO[t])):
        for old, new in steps:
            assert wb[lang].count(old) == 1, (t, lang, old)
            wb[lang] = wb[lang].replace(old, new)
    del s["screen_light"]
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
    print(f"[EngediDark] {len(js)}장 중 {len(todo)}장 생성 · 토큰 {m['tokens']}", flush=True)
    if todo:
        import run_scene
        secs = run_scene.gen_zimage([{k: v for k, v in j.items() if k != "treat"} for j in todo], OUT)
        print(f"[EngediDark] 완료 {len(secs)}장 합 {sum(secs):.0f}s", flush=True)
    for j in js:
        d = m["done"].setdefault(j["treat"], [])
        if os.path.exists(j["out"]) and j["seed"] not in d:
            d.append(j["seed"])
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    json.dump(m, open(METRICS, "w"), ensure_ascii=False, indent=1)
