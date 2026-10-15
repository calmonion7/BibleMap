#!/usr/bin/env python3
"""task#347 S1/S4 — 머리 하나 단위로 화풍 거리 + 얼굴 마진 점수 + VLM 같은 사람을 재고 통과를 판정한다.
자(영역·지표·집계 단위·통과 기준)는 params.FACE_STYLE_*에 실행 전 고정돼 있다 — 여기서 바꾸지 않는다.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV metrics_face_style.py --control   # 대조군: face-ab 16장 + 승인본의 화풍 거리만(VLM·CLIP 없음) → samples/face-style/control.json
  $VENV metrics_face_style.py             # B-e 4장 · 승인본 2장 · R1/R2 16장 전부 → samples/face-style/metrics.json

화풍 거리 = 「승인본의 같은 영역」과 비교한 (sat_p95, val_p05, ink) 절대차의 평균을 두 영역(머리 2배 상자 · 그림 전체)에서 평균.
통과 = 화풍 거리 ≤ B-e 원본 × DIST_MAX_RATIO  그리고  얼굴 점수 ≥ B-e 원본 × FACE_MIN_RATIO  그리고  같은 사람."""
import glob, json, os, re, sys, tempfile

import numpy as np
from PIL import Image

import params
from judge_style import DARK_CUT
from face_ab_heads import heads

HERE = os.path.dirname(os.path.abspath(__file__))
AB = os.path.join(HERE, "samples", "face-ab")
OUT = os.path.join(HERE, "samples", "face-style")
FROZEN_DIR = os.path.join(HERE, "frozen")
OTHERS = ["jonathan", "samuel", "abner", "joab", "nathan", "absalom"]   # metrics_face_ab와 같은 마진 기준
WHO = {"gilgal": ["saul"], "engedi": ["david", "saul"]}


def metrics(im):
    """judge_style.style_metrics와 같은 정의를 이미 연 그림(영역 크롭)에 건다."""
    lum = np.asarray(im.convert("L"), dtype=np.float32) / 255.0
    sat = np.asarray(im.convert("HSV"), dtype=np.float32)[..., 1] / 255.0
    return {"ink": float((lum < DARK_CUT).mean()), "val_p05": float(np.percentile(lum, 5)),
            "sat_p95": float(np.percentile(sat, 95))}


def region(box, im):
    x0, y0, x1, y1 = box
    cx, cy, s = (x0 + x1) / 2, (y0 + y1) / 2, params.FACE_STYLE_REGION_SCALE
    w, h = (x1 - x0) * s / 2, (y1 - y0) * s / 2
    return (max(0, round(cx - w)), max(0, round(cy - h)), min(im.width, round(cx + w)), min(im.height, round(cy + h)))


def style(im, ref, box):
    """두 영역 × 세 지표. 같은 좌표를 승인본에서도 잘라 비교한다."""
    r = region(box, im)
    regs = {"head2x": (im.crop(r), ref.crop(r)), "whole": (im, ref)}
    out, diffs = {}, []
    for k, (a, b) in regs.items():
        ma, mb = metrics(a), metrics(b)
        out[k] = {m: round(ma[m], 4) for m in params.FACE_STYLE_METRICS}
        diffs += [abs(ma[m] - mb[m]) for m in params.FACE_STYLE_METRICS]
    return round(float(np.mean(diffs)), 4), out


def parse(name):
    """R1-g1.3-engedi-s42 / R2-s0.25-gilgal-s23 / B-e-engedi-s42 / approved-gilgal / A-f-…"""
    scene = "gilgal" if "gilgal" in name else "engedi"
    m = re.search(r"-s(\d+)$", name)
    return scene, int(m.group(1)) if m else None


def approved(scene):
    return Image.open(os.path.join(AB, f"approved-{scene}.png")).convert("RGB")


def control():
    """대조군: 자가 B-e의 화풍 손실을 잡고(거리 > 0) 승인본 자신은 0인지. VLM·CLIP 없이 화풍만."""
    res = {}
    for path in sorted(glob.glob(os.path.join(AB, "*.png"))):
        name = os.path.basename(path)[:-4]
        scene, _ = parse(name)
        im = Image.open(path).convert("RGB")
        res[name] = {}
        for who, box in heads(scene, path).items():
            if who in WHO[scene]:
                d, _ = style(im, approved(scene), box)
                res[name][who] = d
        print(name, res[name], flush=True)
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "control.json"), "w"), ensure_ascii=False, indent=1)


def full():
    import check_face_scale as cfs
    import check_face_judge as cfj
    import judge_metrics as jm
    emb = jm.Embedder()
    canon = {w: Image.open(os.path.join(FROZEN_DIR, f"{w}.png")).convert("RGB") for w in ("saul", "david")}
    cbox = {w: cfs.detect_head(os.path.join(FROZEN_DIR, f"{w}.png")) for w in canon}
    old = [Image.open(os.path.join(FROZEN_DIR, f"{k}.png")).convert("RGB") for k in OTHERS]
    tmp = tempfile.mkdtemp()
    paths = (sorted(glob.glob(os.path.join(AB, "B-e-*.png"))) + sorted(glob.glob(os.path.join(AB, "approved-*.png")))
             + sorted(glob.glob(os.path.join(OUT, "R[12]-*.png"))))
    res = {}
    for path in paths:
        name = os.path.basename(path)[:-4]
        scene, seed = parse(name)
        im = Image.open(path).convert("RGB")
        hs = {}
        for who, box in heads(scene, path).items():
            if who not in WHO[scene]:
                continue
            d, regs = style(im, approved(scene), box)
            others = old + [canon[o] for o in canon if o != who]
            score, px = cfs.face_score(canon[who], im, box, emb, cbox[who], others)
            crop = os.path.join(tmp, f"{name}-{who}.png")
            cfs.head_crop(im, box)[0].save(crop)
            v = cfj.same_person(os.path.join(FROZEN_DIR, f"{who}.png"), crop)
            hs[who] = {"box": [round(b) for b in box], "face_px": round(px), "face_score": round(score, 3),
                       "same": v.get("same"), "reason": v.get("reason"), "style_dist": d, "style": regs}
            print(name, who, hs[who]["style_dist"], hs[who]["face_score"], hs[who]["same"], flush=True)
        res[name] = {"scene": scene, "seed": seed, "heads": hs}
    for name, r in res.items():   # 통과는 같은 장면·시드·인물의 B-e 원본 대비 — 그래서 측정이 다 끝난 뒤에 매긴다
        if r["seed"] is None:      # 승인본은 시드가 없어 기준 B-e가 없다(대조군 — 화풍 거리 0만 본다)
            for h in r["heads"].values():
                h["pass"] = None
            continue
        base = res[f"B-e-{r['scene']}-s{r['seed']}"]["heads"]
        for who, h in r["heads"].items():
            b = base.get(who)
            h["pass"] = bool(b and h["style_dist"] <= b["style_dist"] * params.FACE_STYLE_DIST_MAX_RATIO
                             and h["face_score"] >= b["face_score"] * params.FACE_STYLE_FACE_MIN_RATIO
                             and (h["same"] is True or not params.FACE_STYLE_REQUIRE_SAME))
    json.dump(res, open(os.path.join(OUT, "metrics.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    control() if "--control" in sys.argv else full()
