#!/usr/bin/env python3
"""task 362 — 엔게디 장면 문구 수리: 굴 벽 색 낱말(문구 A)·빛 문장(문구 B)이 「굴 어둠·빛」 무너짐을 고치는가.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV gen_engedi_text.py A --seeds 7          # S0: 한 장
  $VENV gen_engedi_text.py A                    # S2: params.REF_EDIT_SEEDS 8장
  $VENV gen_engedi_text.py --choose             # 밝음 수가 적은 쪽, 같으면 평균이 기준에 가까운 쪽 → chosen
  $VENV gen_engedi_text.py --apply              # chosen 문구를 장면 명세에 적는다(S3)

문구는 계획 고정 절 그대로(명세 사본에 덮어 derive_scene.whole_prompt로 파생 — 손으로 쓴 영문 없음, PROMPTING 7·15).
생성 경로·캔버스는 353과 같다(run_scene.gen_zimage, 1216×640). 산출은 레포 밖 <out>/<A|B>/s<시드>.png, 이미 있으면 건너뜀.
밝기 = 회색조 평균(0~1) → samples/engedi-text/metrics.json 의 lum[문구][시드].
"""
import argparse, copy, json, os, sys

import numpy as np
from PIL import Image

import params
import derive_scene as ds

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "batch"))
SCENE = "authored-david-en-gedi-saul"
SIZE = (1216, 640)                     # = gen_cast_v2_pilot.SCENE_SIZE
OUT = os.path.expanduser("~/.local/biblemap-imggen/engedi-text")
METRICS = os.path.join(HERE, "samples", "engedi-text", "metrics.json")
REF = os.path.join(HERE, "samples", "face-ab", "approved-engedi.png")
BRIGHT, TOO_DARK = 0.36, 0.15          # 353 판정 경계 · 기준 0.219 아래

# 고정 절(실행 중 바꾸지 않는다) — (필드, 언어, 옛 글자, 새 글자)
EDITS_A = [
    ("whole_background", "en", "a huge, deep, dark cave of pale limestone",
     "a huge, deep, dark cave with dark brown-black rock walls and a low dark rock ceiling"),
    ("whole_background", "ko", "크고 깊고 어두운 굴 내부",
     "짙은 갈흑색 바위 벽과 낮고 어두운 바위 천장의 크고 깊은 굴 내부"),
    ("whole_background", "verse", "석회암", "바위 색"),
]
EDITS_B = EDITS_A + [
    ("screen_light", "en", "Daylight from the small cave mouth far on the right lights only these two men",
     "A thin beam of light from the tiny cave mouth far on the right falls only on these two men"),
    ("screen_light", "ko", "오른쪽 멀리 굴 어귀에서 들어오는 빛이 두 사람만 비춘다",
     "오른쪽 멀리 작은 굴 어귀에서 가는 빛줄기가 두 사람에게만 떨어진다"),
]
EDITS = {"A": EDITS_A, "B": EDITS_B}


def variant(spec, v):
    s = copy.deepcopy(spec)
    for field, lang, old, new in EDITS[v]:
        assert s[field][lang].count(old) == 1, (field, lang, old)
        s[field][lang] = s[field][lang].replace(old, new)
    return s


def lum(path):
    return round(float(np.asarray(Image.open(path).convert("L"), dtype=float).mean() / 255), 3)


def load_m():
    return json.load(open(METRICS)) if os.path.exists(METRICS) else {"lum": {}, "prompts": {}, "ref_lum": lum(REF)}


def save_m(m):
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    json.dump(m, open(METRICS, "w"), ensure_ascii=False, indent=1)


def gen(v, seeds):
    prompt = ds.whole_prompt(variant(ds.load(SCENE), v))
    d = os.path.join(OUT, v)
    os.makedirs(d, exist_ok=True)
    js = [{"prompt": prompt, "seed": s, "w": SIZE[0], "h": SIZE[1], "out": os.path.join(d, f"s{s}.png")} for s in seeds]
    todo = [j for j in js if not os.path.exists(j["out"])]
    print(f"[EngediText] 문구 {v}: {len(js)}장 중 {len(todo)}장 생성", flush=True)
    if todo:
        import run_scene
        secs = run_scene.gen_zimage(todo, d)
        print(f"[EngediText] 완료 {len(secs)}장 합 {sum(secs):.0f}s", flush=True)
    m = load_m()
    m["prompts"][v] = prompt
    L = m["lum"].setdefault(v, {})
    for j in js:
        L[str(j["seed"])] = lum(j["out"])
    save_m(m)
    for s in seeds:
        x = L[str(s)]
        print(f"[EngediText] {v} s{s} 밝기 {x}{' 밝음' if x >= BRIGHT else ''}{' 너무 어두움' if x < TOO_DARK else ''}")


def choose():
    m = load_m()
    full = {v: L for v, L in m["lum"].items() if len(L) == len(params.REF_EDIT_SEEDS)}
    key = lambda v: (sum(x >= BRIGHT for x in full[v].values()), abs(np.mean(list(full[v].values())) - m["ref_lum"]))
    m["chosen"] = min(full, key=key)
    save_m(m)
    print(f"[EngediText] chosen {m['chosen']} " + " · ".join(f"{v}: 밝음 {key(v)[0]}" for v in full))


def apply():
    m = load_m()
    path = os.path.join(ds.SCENES_DIR, f"{SCENE}.json")
    raw = open(path, encoding="utf-8").read()
    for field, lang, old, new in EDITS[m["chosen"]]:
        assert raw.count(old) == 1, old
        raw = raw.replace(old, new)
    open(path, "w", encoding="utf-8").write(raw)
    assert ds.whole_prompt(ds.load(SCENE)) == m["prompts"][m["chosen"]], "파생 문구 ≠ 생성 문구"
    print(f"[EngediText] 명세에 문구 {m['chosen']} 반영 — 파생 문구 = 생성 문구")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("variant", nargs="?", choices=("A", "B"))
    ap.add_argument("--seeds", type=int, nargs="+", default=params.REF_EDIT_SEEDS)
    ap.add_argument("--choose", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if a.variant:
        gen(a.variant, a.seeds)
    if a.choose:
        choose()
    if a.apply:
        apply()
