#!/usr/bin/env python3
"""task 363 — 512토큰 수리(파생 중복 제거 + 엔게디 관계 중복 제거) 뒤 세 장면을 같은 시드로 다시 그린다.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV gen_prompt_512.py --scenes engedi --seeds 7   # S0: 한 장
  $VENV gen_prompt_512.py                             # 세 장면 × params.REF_EDIT_SEEDS

문구는 지금 명세에서 derive_scene.whole_prompt로 파생(손으로 쓴 영문 없음). 생성 경로·캔버스는 353과 같다.
산출은 레포 밖 <out>/<장면>/s<시드>.png, 이미 있으면 건너뜀. 프롬프트·토큰 수·그린 시드 → samples/prompt-512/metrics.json.
이전 그림(비교 대조): 엔게디 = task 362 문구 A(engedi-text/A), 길갈·라마 = 353 바탕(gen_ref_edit.base_path).
"""
import argparse, json, os, sys

import params
import derive_scene as ds
import check_scenes as cs
import gen_ref_edit as G

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "batch"))
SCENES = ("engedi", "gilgal", "ramah")
SIZE = (1216, 640)                     # = gen_cast_v2_pilot.SCENE_SIZE
OUT = os.path.expanduser("~/.local/biblemap-imggen/prompt-512")
METRICS = os.path.join(HERE, "samples", "prompt-512", "metrics.json")
ROUND = 2   # r1(차림 몸짓 앞·장면 방향 문장)은 <OUT>/r1·metrics-r1.json에 보관 — notes/PROMPT-512.md


def old_path(scene, seed):
    if scene == "engedi":
        return os.path.expanduser(f"~/.local/biblemap-imggen/engedi-text/A/s{seed}.png")
    return G.base_path(scene, seed)


def new_path(scene, seed):
    return os.path.join(OUT, scene, f"s{seed}.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenes", nargs="+", default=SCENES, choices=SCENES)
    ap.add_argument("--seeds", type=int, nargs="+", default=params.REF_EDIT_SEEDS)
    a = ap.parse_args()
    n = cs.zimage_tokens()
    m = json.load(open(METRICS)) if os.path.exists(METRICS) else {"round": ROUND, "prompts": {}, "tokens": {}, "done": {}}
    js = []
    for sc in a.scenes:
        p = ds.whole_prompt(ds.load(G.SC[sc]))
        m["prompts"][sc], m["tokens"][sc] = p, n(p)
        assert m["tokens"][sc] <= cs.WHOLE_MAX, (sc, m["tokens"][sc])
        os.makedirs(os.path.join(OUT, sc), exist_ok=True)
        js += [{"prompt": p, "seed": s, "w": SIZE[0], "h": SIZE[1], "out": new_path(sc, s), "scene": sc} for s in a.seeds]
    todo = [j for j in js if not os.path.exists(j["out"])]
    print(f"[Prompt512] {len(js)}장 중 {len(todo)}장 생성 · 토큰 {m['tokens']}", flush=True)
    if todo:
        import run_scene
        secs = run_scene.gen_zimage([{k: v for k, v in j.items() if k != "scene"} for j in todo], OUT)
        print(f"[Prompt512] 완료 {len(secs)}장 합 {sum(secs):.0f}s", flush=True)
    for j in js:
        d = m["done"].setdefault(j["scene"], [])
        if os.path.exists(j["out"]) and j["seed"] not in d:
            d.append(j["seed"])
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    json.dump(m, open(METRICS, "w"), ensure_ascii=False, indent=1)
