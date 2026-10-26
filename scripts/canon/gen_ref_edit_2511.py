#!/usr/bin/env python3
"""task#359 — 358과 같은 참조 편집을 Qwen-Image-Edit-2511로. mask·strength가 없어 그림 전체를 편집한 뒤 358 몸 상자만 입력 그림에 되붙인다.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV gen_ref_edit_2511.py one <양자화> [장면] [시드]   # S0 첫 1장(「안 돔」·이음매·지목 확인) — 장면 기본 gilgal, 시드 11 → ref-edit-2511/try/
  $VENV gen_ref_edit_2511.py edit <양자화>               # 본 편집 32번(엔게디는 사울 → 다윗 차례), 이미 있으면 건너뜀

편집은 mflux CLI를 한 번에 하나씩 부른다(생성 프로세스 중첩 금지). 시간·피크는 /usr/bin/time -l.
산출은 레포 밖 ~/.local/biblemap-imggen/ref-edit-2511/, 목록은 samples/ref-edit-2511/metrics.json(params.REF_EDIT_2511_*, notes/REF-EDIT-2511.md 고정 절)."""
import json, os, re, signal, subprocess, sys, time

import numpy as np
from PIL import Image, ImageFilter

import params
import gen_ref_edit as G

OUT = os.path.join(G.ROOT, "ref-edit-2511")
METRICS = os.path.join(G.HERE, "samples", "ref-edit-2511", "metrics.json")
NAME, CLI = params.REF_EDIT_2511_MODEL


def side(scene, who, path):
    """정본 인물 둘의 머리 상자 x 중심 순서로 left/right."""
    x = {w: sum(G.head(scene, w, path)[0][0::2]) / 2 for w in params.LORA_SCENE_SCENES[scene][1]}
    other = [w for w in x if w != who]
    if not other:
        return None
    return "left" if x[who] < x[other[0]] else "right"


def paste(raw, src, mask, out):
    """raw(전체 편집)의 몸 상자 안만 src에 얹는다 — 상자 마스크를 FEATHER px로 흐린 알파."""
    s = Image.open(src).convert("RGB")
    r = Image.open(raw).convert("RGB")
    resized = r.size != s.size
    if resized:
        r = r.resize(s.size, Image.LANCZOS)
    a = Image.open(mask).convert("L").filter(ImageFilter.GaussianBlur(params.REF_EDIT_2511_FEATHER))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    Image.composite(r, s, a).save(out)
    return resized


def mask_diff(out, src, box):
    x0, y0, x1, y1 = box
    a = np.asarray(Image.open(out).convert("RGB"), dtype=np.float32)[y0:y1, x0:x1]
    b = np.asarray(Image.open(src).convert("RGB"), dtype=np.float32)[y0:y1, x0:x1]
    return round(float(np.abs(a - b).mean()), 2)


def run_edit(q, src, who, sd, prompt, raw):
    cmd = ["/usr/bin/time", "-l", os.path.join(G.MFLUX, CLI), "--model", NAME, "-q", str(q)]
    cmd += ["--low-ram"] if q == 8 else []
    cmd += ["--image-paths", src, *G.refs(who), "--prompt", prompt, "--seed", str(sd),
            "--steps", str(params.REF_EDIT_2511_STEPS), "--guidance", str(params.REF_EDIT_2511_GUIDANCE),
            "--width", str(G.W), "--height", str(G.H), "--output", raw]
    os.makedirs(os.path.dirname(raw), exist_ok=True)
    t = time.time()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        so, err = p.communicate(timeout=params.REF_EDIT_2511_MAX_SEC * 2)
        rc = p.returncode
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)   # /usr/bin/time만 죽이면 mflux가 고아로 남아 다음 편집과 겹친다(S0 q8에서 실제로 남음)
        so, err = p.communicate()
        rc, err = -9, "timeout " + err
    sec = round(time.time() - t, 1)
    peak = re.search(r"(\d+)\s+peak memory footprint", err)
    ok = rc == 0 and os.path.exists(raw) and sec <= params.REF_EDIT_2511_MAX_SEC
    e = {"raw": raw, "who": who, "seed": sd, "quantize": q, "model": NAME, "status": "ok" if ok else "error", "sec": sec,
         "peak_gb": round(int(peak.group(1)) / 2**30, 2) if peak else None}
    if not ok:
        e["error"] = ("slow > MAX_SEC\n" if rc == 0 and sec > params.REF_EDIT_2511_MAX_SEC else "") + (so[-800:] + "\n" + err[-1500:]).strip()
    print(f"  [RefEdit2511] {who} s{sd} q{q} {e['status']} {sec}s peak {e['peak_gb']}GB", flush=True)
    return e


def edit_one(q, scene, who, sd, base0, src, out, tag):
    mk = G.make_mask(scene, who, base0, os.path.join(OUT, "mask", scene, f"{who}-s{sd}.png"))
    sd_side = side(scene, who, base0)
    prompt = params.REF_EDIT_2511_PROMPT.format(side=sd_side)
    raw = os.path.join(OUT, "raw" if tag == "edit" else "try", scene, f"s{sd}-{who}.png")
    e = {**run_edit(q, src, who, sd, prompt, raw), **mk, "scene": scene, "base": base0, "src": src, "side": sd_side}
    if e["status"] == "ok":
        e["resized"] = paste(raw, src, mk["mask"], out)
        e["out"] = out
        e["mask_diff"] = mask_diff(out, src, mk["mask_box"])
        print(f"  [RefEdit2511] {scene} {who} s{sd} mask_diff {e['mask_diff']} side {sd_side}", flush=True)
    return e


def load_m():
    return json.load(open(METRICS)) if os.path.exists(METRICS) else {"model": NAME}


def save_m(m):
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    json.dump(m, open(METRICS, "w"), ensure_ascii=False, indent=1)


def one(q, scene, sd):
    m = load_m()
    base0 = src = G.base_path(scene, sd)
    for i, who in enumerate(params.REF_EDIT_SCENES[scene]):
        last = i == len(params.REF_EDIT_SCENES[scene]) - 1
        out = os.path.join(OUT, "try", scene, f"q{q}-s{sd}.png" if last else f"q{q}-s{sd}-{who}.png")
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
    for sc, whos in params.REF_EDIT_SCENES.items():
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
        m["mask_diff_mean"] = round(sum(e["mask_diff"] for e in ok) / len(ok), 2)
        m["mask_diff_by_scene"] = {sc: round(float(np.mean([e["mask_diff"] for e in ok if e["scene"] == sc])), 2)
                                   for sc in params.REF_EDIT_SCENES if any(e["scene"] == sc for e in ok)}
    m["edits"] = edits
    save_m(m)
    print(f"[RefEdit2511] 편집 {len(ok)}/{len(edits)} mask_diff_mean {m.get('mask_diff_mean')}", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "one":
        one(int(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else "gilgal", int(sys.argv[4]) if len(sys.argv) > 4 else 11)
    elif cmd == "edit":
        edit(int(sys.argv[2]))
