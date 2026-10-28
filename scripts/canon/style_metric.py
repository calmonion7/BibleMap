#!/usr/bin/env python3
"""화풍 자동 측정자 맞춰 보기(GPU 0급 · task 447 후속 fu-2a5d064ebf09, notes/STYLE-METRIC.md).
그림마다 「사람 승인 장면 그림(명세 approved.final)」 묶음과의 결 거리를 재고, 사람 화풍 라벨(393·445)을 얼마나 가르는지 AUC로 본다.
  $VENV style_metric.py      # 특징 계산(캐시) → AUC 표 · 447 갈래 점수 → samples/style-metric/metrics.json"""
import glob, json, os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.expanduser("~/.local/biblemap-imggen")
SAMP = os.path.join(HERE, "samples", "style-metric")
# 사람 화풍 라벨: True = 맞음. 393 C 맞음 · V2·V3 틀림(FACE-LORA-V4.md 고정 절) · 445 L 다름(같은 문서 「사람 판정」), 445 C는 대조군(LoRA 없음 = 393 C와 같은 경로)
LABELED = [(f"393-{a}", f"{IMG}/lora-v3-scene/{a}-s*.png", a == "C") for a in ("C", "V2", "V3")] + \
          [(f"445-{a}", f"{IMG}/face-lora-v4/scene/{a}-s*.png", a == "C") for a in ("C", "L")]
TEST = [(f"447-{a}", f"{IMG}/lora-style/scene/{a}-s11.png") for a in ("C", "L", "K5", "K3", "R")]
LAYERS = (2, 3, 4, 6, 8)


def refs():
    out = []
    for p in sorted(glob.glob(os.path.join(HERE, "scenes", "*.json"))):
        f = ((json.load(open(p)).get("approved") or {}).get("final") or {}).get("image")
        if f:
            f = f if os.path.isabs(f) else os.path.join(HERE, f)
            if os.path.exists(f):
                out.append(f)
    return out


def feats(paths):
    """→ {경로: {특징 이름: 벡터}} — DINOv2 중간층 Gram(채널 공분산 윗삼각) · DINOv2 CLS. (CLIP은 가중치 미설치 — 토크나이저만 캐시)"""
    import torch
    import numpy as np
    from transformers import AutoModel
    torch.set_grad_enabled(False)
    dm = AutoModel.from_pretrained("facebook/dinov2-base").eval()   # 캐시에 전처리 설정이 없어 ImageNet 정규화를 직접
    mean, std = np.array([0.485, 0.456, 0.406]), np.array([0.229, 0.224, 0.225])
    iu = torch.triu_indices(768, 768)
    out = {}
    for p in paths:
        im = Image.open(p).convert("RGB")
        s = 476 / min(im.size)   # 결을 보려면 224 가운데 자르기는 너무 작다 — 짧은 변 476(14의 배수), 자르지 않음
        im2 = im.resize((round(im.width * s / 14) * 14, round(im.height * s / 14) * 14), Image.BICUBIC)
        x = torch.tensor(((np.asarray(im2) / 255 - mean) / std).transpose(2, 0, 1)[None], dtype=torch.float32)
        hs = dm(pixel_values=x, output_hidden_states=True).hidden_states
        f = {"dino_cls": torch.nn.functional.normalize(hs[-1][0, 0], dim=0)}
        for L in LAYERS:
            t = hs[L][0, 1:]
            t = t - t.mean(0)
            g = (t.T @ t) / t.shape[0]
            f[f"gram{L}"] = torch.nn.functional.normalize(g[iu[0], iu[1]], dim=0)
        out[p] = {k: v.numpy() for k, v in f.items()}
        print(f"[StyleMetric] {os.path.relpath(p, IMG) if p.startswith(IMG) else os.path.relpath(p, HERE)}", flush=True)
    return out


def auc(pos, neg):
    """맞음 점수가 틀림 점수보다 작을(거리) 확률."""
    return sum((p < n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def main():
    import numpy as np
    R = refs()
    lab = [(g, p, ok) for g, pat, ok in LABELED for p in sorted(glob.glob(pat))]
    tst = [(g, p) for g, p in TEST if os.path.exists(p)]
    F = feats(R + [p for _, p, _ in lab] + [p for _, p in tst])
    names = list(F[R[0]])
    m = {"refs": [os.path.relpath(r, HERE) if r.startswith(HERE) else r for r in R], "auc": {}, "groups": {}, "test": {}}
    for k in names:
        ref = np.stack([F[r][k] for r in R])
        dist = lambda p: float(1 - (ref @ F[p][k]).mean())   # 승인 묶음과의 평균 코사인 거리
        d = {p: dist(p) for _, p, _ in lab}
        m["auc"][k] = round(auc([d[p] for _, p, ok in lab if ok], [d[p] for _, p, ok in lab if not ok]), 3)
        m["groups"][k] = {g: [round(d[p], 4) for gg, p, _ in lab if gg == g] for g, _, _ in LABELED}
        m["test"][k] = {g: round(dist(p), 4) for g, p in tst}
        # 대조 있는 쌍: 같은 시드 C보다 승인 묶음에서 먼가(LoRA 실험처럼 C를 늘 함께 그릴 때의 관문)
        seed = lambda p: os.path.basename(p).split("-", 1)[1]
        cs = {(g[:3], seed(p)): d[p] for g, p, _ in lab if g.endswith("-C")}
        m.setdefault("paired", {})[k] = {g: [round(d[p] - cs[(g[:3], seed(p))], 4) for gg, p, _ in lab if gg == g]
                                         for g, _, ok in LABELED if not ok}
        m["paired"][k]["447"] = {g[4:]: round(dist(p) - dist(tst[0][1]), 4) for g, p in tst[1:]}
    os.makedirs(SAMP, exist_ok=True)
    json.dump(m, open(os.path.join(SAMP, "metrics.json"), "w"), ensure_ascii=False, indent=1)
    print(f"승인 기준 {len(R)}장 · 라벨 {len(lab)}장 (맞음 {sum(ok for *_, ok in lab)})")
    for k in names:
        g = m["groups"][k]
        print(f"{k:9s} AUC {m['auc'][k]:.3f} | " + " · ".join(f"{n} {min(v):.4f}~{max(v):.4f}" for n, v in g.items())
              + " | 447 " + " ".join(f"{n[4:]} {v:.4f}" for n, v in m["test"][k].items()))
        pr = m["paired"][k]
        print(f"{'':9s} 같은 시드 C보다 멂: " + " · ".join(f"{g} {sum(x > 0 for x in v)}/{len(v)}" for g, v in pr.items() if g != "447")
              + " | 447 C 대비 " + " ".join(f"{a} {v:+.4f}" for a, v in pr["447"].items()))


if __name__ == "__main__":
    main()
