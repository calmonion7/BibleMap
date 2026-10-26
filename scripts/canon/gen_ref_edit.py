#!/usr/bin/env python3
"""task#358 — 353 바탕 위에서 처치 인물(사울·다윗)의 몸 상자를 마스크로 잡고 정본 참조 2장으로 편집한다(mflux Qwen edit).

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV gen_ref_edit.py base                    # 바탕: 판정 시드 중 353에 없는 5시드 × 3장면 + 미리보기 시드 2(길갈) — Z-Image, 이미 있으면 건너뜀
  $VENV gen_ref_edit.py one <모델순번> [세기]     # 길갈 사울 s11 편집 1장(「안 돔」 시험) → ref-edit/try/
  $VENV gen_ref_edit.py preview                 # 세기 미리보기 6장(길갈 사울 × 미리보기 시드 2 × 세기 3)
  $VENV gen_ref_edit.py edit <세기>              # 본 편집 32번(엔게디는 사울 → 다윗 차례)
  $VENV gen_ref_edit.py masks <장면> <바탕>...    # 마스크만 만들어 확인

편집은 mflux CLI를 한 번에 하나씩 부른다(생성 프로세스 중첩 금지). 시간·피크는 /usr/bin/time -l.
산출은 레포 밖 ~/.local/biblemap-imggen/ref-edit/, 목록은 samples/ref-edit/metrics.json(params.REF_EDIT_*, notes/REF-EDIT.md 고정 절)."""
import json, os, re, subprocess, sys, time

from PIL import Image, ImageDraw

import params
import derive_scene as ds
from make_cast_v2_pilot_page import head, SC

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.expanduser("~/.local/biblemap-imggen")
OUT = os.path.join(ROOT, "ref-edit")
PILOT = os.path.join(ROOT, "cast-v2-pilot", "scene")
MFLUX = os.path.join(ROOT, ".venv-mflux", "bin")
METRICS = os.path.join(HERE, "samples", "ref-edit", "metrics.json")
W, H = 1216, 640
PROMPT = ("Replace the person in the masked area of image 1 with the man shown in image 2 and image 3 — same face, hair, "
          "beard, body build and clothing. Keep his pose and position, and keep the pencil and watercolor drawing style, "
          "lighting and everything else of image 1 unchanged.")
_OWL = {}


def base_path(scene, seed):
    p = os.path.join(PILOT, SC[scene], f"s{seed}.png")
    return p if os.path.exists(p) else os.path.join(OUT, "base", scene, f"s{seed}.png")


def refs(who):
    full = params.REF_EDIT_REF_FULL[who]
    return [os.path.join(HERE, "frozen", f"{who}.png"), os.path.join(ROOT, "lora-sheet-v2", who, f"{full}.png")]


def _persons(im):
    import torch
    from transformers import Owlv2Processor, Owlv2ForObjectDetection
    if not _OWL:
        m = "google/owlv2-base-patch16-ensemble"
        _OWL["p"], _OWL["m"] = Owlv2Processor.from_pretrained(m), Owlv2ForObjectDetection.from_pretrained(m).eval()
    p, m = _OWL["p"], _OWL["m"]
    with torch.no_grad():
        o = m(**p(text=[["a person", "a standing man in a robe"]], images=im, return_tensors="pt"))
    S = max(im.size)
    r = p.post_process_grounded_object_detection(o, threshold=0.08, target_sizes=torch.tensor([[S, S]]))[0]
    return [([float(v) for v in b], float(s)) for b, s in zip(r["boxes"], r["scores"])]


def body_box(scene, who, path):
    """→ (몸 상자, 머리 상자, 출처). 머리 중심을 담고 장면의 다른 정본 인물 머리는 담지 않는 「a person」 상자 중 최고 점수 — 장면 절반 폭 초과 무리 상자는 뺀다."""
    im = Image.open(path).convert("RGB")
    hb, _ = head(scene, who, path)
    cx, cy = (hb[0] + hb[2]) / 2, (hb[1] + hb[3]) / 2
    others = [head(scene, o, path)[0] for o in params.LORA_SCENE_SCENES[scene][1] if o != who]
    inside = lambda b, h: b[0] <= (h[0] + h[2]) / 2 <= b[2] and b[1] - 0.5 * (h[3] - h[1]) <= (h[1] + h[3]) / 2 <= b[3]
    c = [(s, b) for b, s in _persons(im)
         if inside(b, hb) and not any(inside(b, o) for o in others) and (b[2] - b[0]) < 0.5 * im.width]
    if c:
        b = max(c)[1]
        return [b[0], max(0, min(b[1], hb[1]) - (hb[3] - hb[1])), b[2], b[3]], hb, "owl"   # 위로 머리 높이 하나 더 — 든 손(S0 첫 장: 길갈 사울 손이 마스크 밖에 남음)
    hw, hh = hb[2] - hb[0], hb[3] - hb[1]
    return [cx - 1.25 * hw, hb[1], cx + 1.25 * hw, min(im.height, hb[1] + 6 * hh)], hb, "fallback"


def make_mask(scene, who, path, out):
    b, hb, src = body_box(scene, who, path)
    im = Image.open(path)
    pw, ph = (b[2] - b[0]) * params.REF_EDIT_MASK_PAD, (b[3] - b[1]) * params.REF_EDIT_MASK_PAD
    b = [max(0, b[0] - pw), max(0, b[1] - ph), min(im.width, b[2] + pw), min(im.height, b[3] + ph)]
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rectangle(b, fill=255)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    m.save(out)
    return {"mask": out, "mask_box": [round(v) for v in b], "head": [round(v) for v in hb], "mask_src": src}


def run_edit(model_i, src, mask, who, seed, strength, out):
    name, cli, q = params.REF_EDIT_MODELS[model_i]
    cmd = ["/usr/bin/time", "-l", os.path.join(MFLUX, cli), "--model", name, "-q", str(q), "--low-ram",
           "--image-paths", src, *refs(who), "--mask-image", mask, "--prompt", PROMPT, "--seed", str(seed),
           "--steps", str(params.REF_EDIT_STEPS), "--width", str(W), "--height", str(H),
           "--strength", str(strength), "--output", out]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    t = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    sec = round(time.time() - t, 1)
    err = r.stderr
    peak = re.search(r"(\d+)\s+peak memory footprint", err)
    rss = re.search(r"(\d+)\s+maximum resident set size", err)
    ok = r.returncode == 0 and os.path.exists(out)
    e = {"out": out, "who": who, "seed": seed, "strength": strength, "model": name, "status": "ok" if ok else "error",
         "sec": sec, "peak_gb": round(int(peak.group(1)) / 2**30, 2) if peak else None,
         "rss_gb": round(int(rss.group(1)) / 2**30, 2) if rss else None}
    if not ok:
        e["error"] = (r.stdout[-800:] + "\n" + err[-1500:]).strip()
    print(f"  [RefEdit] {who} s{seed} st{strength} {e['status']} {sec}s peak {e['peak_gb']}GB", flush=True)
    return e


def load_m():
    return json.load(open(METRICS)) if os.path.exists(METRICS) else {}


def save_m(m):
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    json.dump(m, open(METRICS, "w"), ensure_ascii=False, indent=1)


def base():
    sys.path.insert(0, os.path.join(HERE, "batch"))
    js = []
    for sc in params.REF_EDIT_SCENES:
        for s in params.REF_EDIT_SEEDS:
            js.append((sc, s))
    js += [("gilgal", s) for s in params.REF_EDIT_PREVIEW_SEEDS]
    todo = []
    for sc, s in js:
        p = base_path(sc, s)
        if not os.path.exists(p):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            todo.append({"prompt": ds.whole_prompt(ds.load(SC[sc])), "seed": s, "w": W, "h": H, "out": p})
    print(f"[RefEdit] 바탕 {len(js)}장 중 {len(todo)}장 생성", flush=True)
    if todo:
        import run_scene
        secs = run_scene.gen_zimage(todo, os.path.join(OUT, "base"))
        print(f"[RefEdit] 바탕 완료 {len(secs)}장 합 {sum(secs):.0f}s", flush=True)


def one(model_i, strength):
    src = base_path("gilgal", 11)
    mk = make_mask("gilgal", "saul", src, os.path.join(OUT, "mask", "gilgal", "saul-s11.png"))
    e = run_edit(model_i, src, mk["mask"], "saul", 11, strength, os.path.join(OUT, "try", f"m{model_i}-gilgal-saul-s11-st{strength}.png"))
    m = load_m()
    m.setdefault("try", []).append({**e, **mk})
    save_m(m)


def preview():
    m = load_m()
    m["axis"] = params.REF_EDIT_AXIS
    m["axis_values"] = params.REF_EDIT_AXIS_VALUES
    pv = []
    for s in params.REF_EDIT_PREVIEW_SEEDS:
        src = base_path("gilgal", s)
        mk = make_mask("gilgal", "saul", src, os.path.join(OUT, "mask", "gilgal", f"saul-s{s}.png"))
        for v in params.REF_EDIT_AXIS_VALUES:
            out = os.path.join(OUT, "preview", f"gilgal-saul-s{s}-st{v}.png")
            e = {"out": out, "status": "ok", "skipped": True} if os.path.exists(out) else run_edit(m["model_i"], src, mk["mask"], "saul", s, v, out)
            pv.append({**e, **mk, "seed": s, "strength": v, "base": src})
    m["preview"] = pv
    save_m(m)


def edit(strength):
    m = load_m()
    old = {(e["scene"], e["who"], e["seed"]): e for e in m.get("edits", []) if e.get("status") == "ok"}
    edits = []
    for sc, whos in params.REF_EDIT_SCENES.items():
        for s in params.REF_EDIT_SEEDS:
            base0 = base_path(sc, s)
            src = base0
            for i, who in enumerate(whos):
                last = i == len(whos) - 1
                out = os.path.join(OUT, "edit", sc, f"s{s}.png" if last else f"s{s}-{who}.png")
                mk = make_mask(sc, who, base0, os.path.join(OUT, "mask", sc, f"{who}-s{s}.png"))
                if (sc, who, s) in old and os.path.exists(out):
                    e = old[(sc, who, s)]
                else:
                    e = {**run_edit(m["model_i"], src, mk["mask"], who, s, strength, out), **mk, "scene": sc, "base": base0, "src": src}
                edits.append(e)
                m["edits"] = edits
                save_m(m)
                if e["status"] != "ok":
                    break
                src = out
    m["edits"] = edits
    save_m(m)
    print(f"[RefEdit] 편집 {sum(e['status'] == 'ok' for e in edits)}/{len(edits)}", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "base":
        base()
    elif cmd == "one":
        one(int(sys.argv[2]), float(sys.argv[3]) if len(sys.argv) > 3 else 1.0)
    elif cmd == "preview":
        preview()
    elif cmd == "edit":
        edit(float(sys.argv[2]))
    elif cmd == "masks":
        for p in sys.argv[3:]:
            for who in params.REF_EDIT_SCENES[sys.argv[2]]:
                print(p, who, make_mask(sys.argv[2], who, p, os.path.join(OUT, "mask-check", sys.argv[2], f"{who}-{os.path.basename(p)}")))
