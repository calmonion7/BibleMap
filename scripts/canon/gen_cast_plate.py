#!/usr/bin/env python3
"""인물 정본 판 시트 생성기 (2026-09-04, task 331 · ADR `260904-055320`).

어휘 정본 `cast/<id>.json`의 문구로 **빈 종이 위 단독 판**을 뽑아 두 가지를 사람 앞에 놓는다:
  ① 얼굴 동결 후보 — 기준 자세(poses[0]) × 시드 4장(7은 뺀다 — 종이 테두리 prior), 앵커 없음
  ② A/B 몽타주 — 자세 문구 2종(가로) × 앵커 끔/켬(세로). 켬은 ①의 얼굴 한 장을 IP-Adapter 0.25로 물린다.
     끔/켬은 **같은 시드·같은 문구**라 차이는 앵커만이다(ADR `260825-013557` 대조군).
판정은 사람 육안만 — 정체성은 기계가 못 잰다. 판 잉크(lum<0.55 비율, judge_scene C4 산식)는 참고치로 찍는다.

얼굴은 사람이 고르기 **전**에 A/B를 만들어야 하므로(둘 다 사람 관문이면 왕복이 둘) 기본 얼굴은 seeds[0]으로
가정하고 만든다 — 사용자가 다른 시드를 고르면 `--face-seed`로 A/B만 다시 뽑는다(3장).

Usage:
  $VENV gen_cast_plate.py <cast-id> [--seeds 11,42,23,5] [--face-seed 11] [--ip 0.25] [--label a]
  산출: .forge/reports/canon-pilot/cast/<id>/ (판 원본·얼굴 크롭·meta.json) · cast/<id>-faces.png · cast/<id>-ab.png
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import torch
from diffusers import StableDiffusionXLInpaintPipeline
from PIL import Image, ImageDraw, ImageFilter

import params

sys.path.insert(0, params.CANON_DIR)
import derive_scene as ds  # noqa: E402  — 공용 화풍 머리 ST · 부정어 NEG (장면과 같은 것)
import gen_scripture_scene as gs  # noqa: E402  — PAPER·PLATE_*·_fit_neg·_body_box (판 상수는 한 곳)
from make_montage import font  # noqa: E402

CAST_DIR = os.path.join(params.CANON_DIR, "cast")
OUT = os.path.join(params.OUT_ROOT, "cast")
DARK_CUT = 0.55
HEAD_FRAC = 0.20   # eco: 머리 크롭 = 몸 bbox 위쪽 20% 정사각 — 콘티 없는 판에는 cond-meta가 없어 실루엣에서 파생


def load_cast(cid):
    with open(os.path.join(CAST_DIR, f"{cid}.json"), encoding="utf-8") as fh:
        return json.load(fh)


describe = ds.cast_describe   # 장면 판 프롬프트 `{cast:<id>}`와 같은 문구(derive_scene) — 한 곳에서만 정의


def prompt_for(c, pose):
    return f"{ds.ST} {describe(c)}, {pose}."


def neg_for(c):
    extra = list(c.get("neg", []))
    if c.get("beard") == "none":
        extra.append("beard")
    if c.get("headwear") == "none":
        extra += ["helmet", "crown", "turban"]
    return ds.NEG + ", " + ", ".join(extra)


def plate(pipe, prompt, neg, seed, face=None, ip=0.0):
    """빈 종이에 단독으로 그린다 → (판, 알파, 토큰수). gs._plate와 같은 상수, 앵커 인자만 더한다."""
    pw, ph = params.SAMPLE_SIZE
    p = prompt.rstrip() + gs.PLATE_BG
    lim = pipe.tokenizer.model_max_length
    n = len(pipe.tokenizer(p).input_ids)
    if n > lim:
        sys.exit(f"판 프롬프트가 한도를 넘었다({n}/{lim}) — 어휘 정본을 줄여라: {p}")
    ng, dropped = gs._fit_neg(pipe.tokenizer, neg, lim)
    if dropped:
        print(f"    부정어 {len(dropped)}개를 예산에서 뺐다: {', '.join(dropped)}", flush=True)
    kw = {}
    if face is not None:
        pipe.set_ip_adapter_scale(ip)
        kw["ip_adapter_image"] = face
    res = pipe(prompt=p, negative_prompt=ng,
               image=Image.new("RGB", (pw, ph), gs.PAPER),
               mask_image=Image.new("L", (pw, ph), 255),
               width=pw, height=ph, strength=gs.PLATE_STRENGTH,
               num_inference_steps=params.STEPS, guidance_scale=params.GUIDANCE,
               generator=torch.Generator("mps").manual_seed(seed), **kw).images[0]
    d = np.abs(np.asarray(res.convert("RGB")).astype(int) - np.array(gs.PAPER)).max(axis=2)
    al = Image.fromarray(((d > gs.PLATE_CUT) * 255).astype(np.uint8), "L")
    al = al.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    return res, al, n


def ink(res, al):
    bb = gs._body_box(al) if al.getbbox() else None
    if bb is None:
        return 0.0, None
    lum = np.asarray(res.convert("L")).astype(float) / 255.0
    x0, y0, x1, y1 = bb
    return float((lum[y0:y1, x0:x1] < DARK_CUT).mean()), bb


def head_crop(res, al):
    """몸 bbox 위쪽 HEAD_FRAC 높이의 정사각 — 가로 중심은 그 띠의 알파 질량 중심."""
    bb = gs._body_box(al)
    x0, y0, x1, y1 = bb
    h = int((y1 - y0) * HEAD_FRAC)
    band = np.asarray(al)[y0:y0 + h, x0:x1] > 0
    cx = x0 + (int(np.flatnonzero(band.any(axis=0)).mean()) if band.any() else (x1 - x0) // 2)
    box = (max(cx - h // 2, 0), y0, min(cx + h // 2, res.width), y0 + h)
    return res.crop(box), box


def sheet(cells, cols, title, cell_w=416, cell_h=608):
    """cells = [(img, label)] → 격자 몽타주(가로 cols)."""
    rows = (len(cells) + cols - 1) // cols
    W, H = cols * cell_w, rows * (cell_h + 22) + 28
    im = Image.new("RGB", (W, H), (255, 255, 255))
    dr = ImageDraw.Draw(im)
    dr.text((4, 5), title, fill=(0, 0, 0), font=font(15))
    for i, (img, label) in enumerate(cells):
        x, y = (i % cols) * cell_w, 28 + (i // cols) * (cell_h + 22)
        t = img.copy()
        t.thumbnail((cell_w, cell_h))
        im.paste(t, (x, y + 22))
        dr.text((x + 3, y + 3), label, fill=(0, 0, 0), font=font(13))
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cast")
    ap.add_argument("--seeds", default="11,42,23,5", help="얼굴 후보 시드(7 제외 — 종이 테두리 prior)")
    ap.add_argument("--face-seed", type=int, default=None, help="A/B에 물릴 얼굴 시드(기본 seeds[0])")
    ap.add_argument("--ip", type=float, default=0.25)
    ap.add_argument("--label", default="a", help="문구 개정 라벨(같은 인물의 재시도를 구분)")
    ap.add_argument("--ab-only", action="store_true", help="얼굴 후보는 있다고 보고 A/B만(얼굴 교체 시)")
    a = ap.parse_args()
    c = load_cast(a.cast)
    seeds = [int(s) for s in a.seeds.split(",")]
    fseed = a.face_seed or seeds[0]
    out = os.path.join(OUT, a.cast)
    os.makedirs(out, exist_ok=True)
    poses = c["poses"][:2]
    neg = neg_for(c)
    meta = {"cast": a.cast, "label": a.label, "ip": a.ip, "face_seed": fseed,
            "prompts": {f"P{i + 1}": prompt_for(c, p) for i, p in enumerate(poses)}, "neg": neg, "plates": {}}
    mp = os.path.join(out, f"{a.label}-meta.json")
    if os.path.exists(mp):   # --ab-only 재실행이 얼굴 후보 기록을 덮지 않게 병합한다
        meta["plates"] = json.load(open(mp, encoding="utf-8")).get("plates", {})

    t = time.time()
    pipe = StableDiffusionXLInpaintPipeline.from_pretrained(
        params.SDXL_BASE, torch_dtype=torch.float16, variant="fp16", use_safetensors=True).to("mps")
    pipe.set_progress_bar_config(disable=True)
    print(f"로드 {time.time() - t:.0f}s · {a.cast} · {describe(c)}", flush=True)

    def shoot(tag, pose, seed, face=None):
        ts = time.time()
        res, al, n = plate(pipe, prompt_for(c, pose), neg, seed, face, a.ip)
        k, bb = ink(res, al)
        fn = f"{a.label}-{tag}-s{seed}.png"
        res.save(os.path.join(out, fn))
        meta["plates"][fn] = {"pose": pose, "seed": seed, "anchor": face is not None, "tokens": n, "ink": round(k, 3), "body": bb}
        print(f"  [{tag} s{seed} {'켬' if face is not None else '끔'}] {time.time() - ts:.0f}s {n}/77토큰 잉크 {k:.3f} -> {fn}", flush=True)
        return res, al, k

    # ① 얼굴 후보 — 기준 자세 × 시드, 앵커 없음
    cands = {}
    if not a.ab_only:
        for s in seeds:
            res, al, k = shoot("P1", poses[0], s)
            face, box = head_crop(res, al)
            face.save(os.path.join(out, f"{a.label}-face-s{s}.png"))
            meta["plates"][f"{a.label}-P1-s{s}.png"]["face_box"] = box
            cands[s] = (res, face, k)
        cells = []
        for s, (res, face, k) in cands.items():
            cell = res.copy()
            f = face.resize((240, 240))
            cell.paste(f, (cell.width - 250, 10))
            cells.append((cell, f"seed {s} · 잉크 {k:.3f}"))
        sheet(cells, 4, f"{a.cast} 얼굴 후보 {len(cands)}장 — 기준 자세 · 앵커 없음 · 우상단 = 머리 크롭",
              ).save(os.path.join(OUT, f"{a.cast}-faces.png"))

    # ② A/B — 자세 2종 × 끔/켬, 시드 = 얼굴 시드(끔 P1은 ①과 같은 장)
    fp = os.path.join(out, f"{a.label}-face-s{fseed}.png")
    if not os.path.exists(fp):
        sys.exit(f"얼굴 크롭이 없다: {fp} — --ab-only 없이 먼저 돌려라")
    face = Image.open(fp).convert("RGB")
    off = {}
    for i, pose in enumerate(poses):
        tag = f"P{i + 1}"
        if i == 0 and fseed in cands:
            off[tag] = (cands[fseed][0], cands[fseed][2])
        else:
            res, al, k = shoot(tag, pose, fseed)
            off[tag] = (res, k)
    pipe.load_ip_adapter(params.IP_ADAPTER_REPO, subfolder=params.IP_ADAPTER_SUBFOLDER,
                         weight_name=params.IP_ADAPTER_WEIGHT)
    on = {}
    for i, pose in enumerate(poses):
        tag = f"P{i + 1}"
        res, al, k = shoot(f"{tag}on", pose, fseed, face)
        on[tag] = (res, k)
    cells = [(off[f"P{i + 1}"][0], f"끔 · P{i + 1} · 잉크 {off[f'P{i + 1}'][1]:.3f}") for i in range(len(poses))]
    cells += [(on[f"P{i + 1}"][0], f"켬 IP {a.ip} · P{i + 1} · 잉크 {on[f'P{i + 1}'][1]:.3f}") for i in range(len(poses))]
    ab = sheet(cells, len(poses), f"{a.cast} A/B — 위 끔 / 아래 켬(얼굴 seed {fseed}) · 시드 {fseed} · 문구 {a.label}")
    ab.paste(face.resize((120, 120)), (ab.width - 126, 0))
    ab.save(os.path.join(OUT, f"{a.cast}-ab.png"))
    with open(os.path.join(out, f"{a.label}-meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1)
    print(f"완료 {time.time() - t:.0f}s → {a.cast}-faces.png · {a.cast}-ab.png", flush=True)


if __name__ == "__main__":
    main()
