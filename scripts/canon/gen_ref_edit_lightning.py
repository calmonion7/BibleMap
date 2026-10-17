#!/usr/bin/env python3
"""task#360 — 359와 같은 참조 편집을 2511 + Lightning 4스텝 LoRA로(guidance 1 래퍼). 지시문에 정본 외형(cast_describe)을 넣는다.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV gen_ref_edit_lightning.py one <양자화> [장면] [시드]   # S0 첫 1장(「안 돔」·targeted·지목 확인) — 장면 기본 gilgal, 시드 11 → ref-edit-lightning/try/
  $VENV gen_ref_edit_lightning.py edit <양자화>               # 본 편집 32번(엔게디는 사울 → 다윗 차례), 이미 있으면 건너뜀
  $VENV gen_ref_edit_lightning.py stop "<사유>"               # 고정 절 정지 조건일 때만 — metrics `stop`

마스크·좌우·되붙임·mask_diff는 gen_ref_edit_2511 그대로. 조작 확인 `targeted` = 전체 편집 원본 대 입력 그림의 몸 상자 안 평균 차 − 밖 평균 차.
산출은 레포 밖 ~/.local/biblemap-imggen/ref-edit-lightning/, 목록은 samples/ref-edit-lightning/metrics.json(params.REF_EDIT_LIGHTNING_*, notes/REF-EDIT-LIGHTNING.md 고정 절).
task#361: params.REF_EDIT_LIGHTNING_LOOK_SRC = "image+scene"이면 {look} = 정체성 + 장면 명세 차림, 엔게디만, 산출 ref-edit-costume/(notes/REF-EDIT-COSTUME.md).
360 재현은 LOOK_SRC를 "image"로 되돌린다."""
import json, os, re, signal, subprocess, sys, time

import numpy as np
from PIL import Image

import params
import derive_scene as D
import gen_ref_edit as G
import gen_ref_edit_2511 as R

COSTUME = params.REF_EDIT_LIGHTNING_LOOK_SRC == "image+scene"   # task#361 — 360 산출을 덮지 않게 루트·목록 분리, 엔게디만
SET = "ref-edit-costume" if COSTUME else "ref-edit-lightning"
OUT = os.path.join(G.ROOT, SET)
METRICS = os.path.join(G.HERE, "samples", SET, "metrics.json")
SCENES = params.REF_EDIT_COSTUME_SCENES if COSTUME else params.REF_EDIT_SCENES
NAME = R.NAME
TRY = "try" if params.REF_EDIT_LIGHTNING_LOOK_SRC == "card" else f"try-{params.REF_EDIT_LIGHTNING_LOOK_SRC}"   # S0 첫 시도(card) 산출을 덮지 않게


def lora_path():
    repo, fname, _ = params.REF_EDIT_LIGHTNING_LORA
    d = os.path.expanduser(f"~/.cache/huggingface/hub/models--{repo.replace('/', '--')}")
    for root, _, fs in os.walk(d):
        if fname in fs:
            return os.path.join(root, fname)
    sys.exit("[RefEditLightning] LoRA 파일 없음")


def look(scene, who):
    """"image"(S0 뒤 개정) = 정본 그림 쪽 서술 · "card" = 장면 문구와 같은 낱말(정본 카드 층 + 그 장면 cast_override)
    · "image+scene"(task#361) = 정본 그림 쪽 정체성 + 장면 명세 차림."""
    if params.REF_EDIT_LIGHTNING_LOOK_SRC == "image":
        return params.REF_EDIT_LIGHTNING_LOOK_IMAGE[who]
    spec = D.load(params.LORA_SCENE_SCENES[scene][0])
    f = next(f for f in spec["figures"] if f.get("cast") == who)
    if params.REF_EDIT_LIGHTNING_LOOK_SRC == "image+scene":
        return params.REF_EDIT_LIGHTNING_LOOK_IDENTITY[who] + ", wearing " + f["costume"]["en"]
    return D.cast_describe(D._cast_in_scene(f))


def targeted(raw, src, box):
    s = Image.open(src).convert("RGB")
    r = Image.open(raw).convert("RGB")
    if r.size != s.size:
        r = r.resize(s.size, Image.LANCZOS)
    d = np.abs(np.asarray(r, np.float32) - np.asarray(s, np.float32)).mean(2)
    x0, y0, x1, y1 = box
    inside = np.zeros(d.shape, bool)
    inside[y0:y1, x0:x1] = True
    i, o = float(d[inside].mean()), float(d[~inside].mean())
    return round(i - o, 2), round(i, 2), round(o, 2)


def run_edit(q, src, who, sd, prompt, raw):
    _, _, scale = params.REF_EDIT_LIGHTNING_LORA
    cmd = ["/usr/bin/time", "-l", os.path.join(G.MFLUX, "python"), os.path.join(G.HERE, "mflux_qwen_edit_cfg1.py"),
           "--model", NAME, "-q", str(q), *(["--low-ram"] if q == 8 else []), "--lora", lora_path(), str(scale),
           "--image-paths", src, *G.refs(who), "--prompt", prompt, "--seed", str(sd),
           "--steps", str(params.REF_EDIT_LIGHTNING_STEPS), "--guidance", str(params.REF_EDIT_LIGHTNING_GUIDANCE),
           "--width", str(G.W), "--height", str(G.H), "--output", raw]
    os.makedirs(os.path.dirname(raw), exist_ok=True)
    t = time.time()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        so, err = p.communicate(timeout=params.REF_EDIT_LIGHTNING_MAX_SEC * 2)
        rc = p.returncode
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)   # 그룹째 — mflux가 고아로 남아 다음 편집과 겹치지 않게(359 결함)
        so, err = p.communicate()
        rc, err = -9, "timeout " + err
    sec = round(time.time() - t, 1)
    peak = re.search(r"(\d+)\s+peak memory footprint", err)
    ok = rc == 0 and os.path.exists(raw)
    e = {"raw": raw, "who": who, "seed": sd, "quantize": q, "model": NAME, "status": "ok" if ok else "error", "sec": sec,
         "peak_gb": round(int(peak.group(1)) / 2**30, 2) if peak else None}
    if not ok:
        e["error"] = (so[-800:] + "\n" + err[-1500:]).strip()
    print(f"  [RefEditLightning] {who} s{sd} q{q} {e['status']} {sec}s peak {e['peak_gb']}GB", flush=True)
    return e


def edit_one(q, scene, who, sd, base0, src, out, tag):
    mk = G.make_mask(scene, who, base0, os.path.join(OUT, "mask", scene, f"{who}-s{sd}.png"))
    sd_side = R.side(scene, who, base0)
    prompt = params.REF_EDIT_LIGHTNING_PROMPT.format(side=sd_side, look=look(scene, who))
    raw = os.path.join(OUT, "raw" if tag == "edit" else TRY, scene, f"s{sd}-{who}.png")
    e = {**run_edit(q, src, who, sd, prompt, raw), **mk, "scene": scene, "base": base0, "src": src, "side": sd_side,
         "look_src": params.REF_EDIT_LIGHTNING_LOOK_SRC}
    if e["status"] == "ok":
        e["resized"] = R.paste(raw, src, mk["mask"], out)
        e["out"] = out
        e["mask_diff"] = R.mask_diff(out, src, mk["mask_box"])
        e["targeted"], e["diff_in"], e["diff_out"] = targeted(raw, src, mk["mask_box"])
        print(f"  [RefEditLightning] {scene} {who} s{sd} targeted {e['targeted']} (안 {e['diff_in']} / 밖 {e['diff_out']}) side {sd_side}", flush=True)
    return e


def load_m():
    return json.load(open(METRICS)) if os.path.exists(METRICS) else {"model": NAME, "lora": params.REF_EDIT_LIGHTNING_LORA[1]}


def save_m(m):
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    json.dump(m, open(METRICS, "w"), ensure_ascii=False, indent=1)


def one(q, scene, sd):
    m = load_m()
    base0 = src = G.base_path(scene, sd)
    for i, who in enumerate(SCENES[scene]):
        last = i == len(SCENES[scene]) - 1
        out = os.path.join(OUT, TRY, scene, f"q{q}-s{sd}.png" if last else f"q{q}-s{sd}-{who}.png")
        e = edit_one(q, scene, who, sd, base0, src, out, "try")
        m.setdefault("try", []).append(e)
        save_m(m)
        if e["status"] != "ok":
            break
        src = out


def edit(q):
    m = load_m()
    m["quantize"] = q
    old = {(e["scene"], e["who"], e["seed"]): e for e in m.get("edits", []) if e.get("status") == "ok" and e.get("quantize") == q}
    edits = []
    for sc, whos in SCENES.items():
        for s in params.REF_EDIT_SEEDS:
            base0 = src = G.base_path(sc, s)
            for i, who in enumerate(whos):
                last = i == len(whos) - 1
                out = os.path.join(OUT, "edit", sc, f"s{s}.png" if last else f"s{s}-{who}.png")
                if (sc, who, s) in old and os.path.exists(out):
                    e = old[(sc, who, s)]
                else:
                    e = edit_one(q, sc, who, s, base0, src, out, "edit")
                edits.append(e)
                m["edits"] = edits
                save_m(m)
                if e["status"] != "ok":
                    break
                src = out
    ok = [e for e in edits if e["status"] == "ok"]
    if ok:
        for k in ("targeted", "mask_diff"):
            m[f"{k}_mean"] = round(float(np.mean([e[k] for e in ok])), 2)
            m[f"{k}_by_scene"] = {sc: round(float(np.mean([e[k] for e in ok if e["scene"] == sc])), 2)
                                  for sc in SCENES if any(e["scene"] == sc for e in ok)}
        m["sec_mean"] = round(float(np.mean([e["sec"] for e in ok])), 1)
    m["edits"] = edits
    save_m(m)
    print(f"[RefEditLightning] 편집 {len(ok)}/{len(edits)} targeted_mean {m.get('targeted_mean')}", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "one":
        one(int(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else "gilgal", int(sys.argv[4]) if len(sys.argv) > 4 else 11)
    elif cmd == "edit":
        edit(int(sys.argv[2]))
    elif cmd == "stop":
        m = load_m()
        m["stop"] = sys.argv[2]
        save_m(m)
