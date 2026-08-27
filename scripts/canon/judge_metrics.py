"""task#315 S5(기계) — ④ 정본대로인가(교차 유사도) · ⑤ 화풍이 통일되는가(잉크 밀도/대비).

①②③은 사람이 육안으로 본다(이 스크립트의 범위 밖). 여기서는 기계로 재는 두 문항만 잰다.

  ④ 정본대로인가 — masks/{david,goliath}.png의 바운딩 박스로 각 장면의 인물 영역을 크롭하고,
    IP-Adapter의 CLIP 이미지 인코더(params.params.IMAGE_ENCODER — IP-Adapter 저장소의
    sdxl_models/image_encoder, CLIP ViT-bigG)로
    임베딩해 코사인 유사도를 잰다. 통과 = sim(내 영역, 내 동결본) > sim(내 영역, 남의 동결본),
    다윗·골리앗 대칭 성립.
  ⑤ 화풍이 통일되는가 — 그레이스케일 평균·표준편차·에지밀도 3statistics(잉크 밀도/대비 지표,
    아래 ink_style_vector 근거 참조)를 z-score 정규화해 유클리드 거리로 잰다. 각 조건을 같은
    시드의 (a)와 비교하고, 조건 내 3시드끼리도 비교한다.

Usage: /Users/calmonion/.local/biblemap-imggen/.venv314/bin/python judge_metrics.py
"""
import json
import os

import numpy as np
import torch
from PIL import Image
from transformers import (CLIPTextModelWithProjection, CLIPTokenizer,
                          CLIPVisionModelWithProjection)

import params

SCENE = os.path.join(params.OUT_ROOT, "scene")
MASKS = os.path.join(params.OUT_ROOT, "masks")

CONDITIONS = ["a-none", "b-nomask", "c-mask", "d-mask-bg"]

# OpenAI CLIP 표준 전처리 상수 — 이 스냅샷엔 preprocessor_config.json이 없어(config.json·
# model.safetensors뿐) diffusers/CLIPImageProcessor 기본값을 그대로 재현한다(새 의존성 없음).
CLIP_MEAN = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
CLIP_STD = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)
EDGE_THRESHOLD = 15  # 인접 픽셀 명도차 임계(0~255) — 잉크 선 경계 판정용, prep_cond.py류 관례값


def bbox_from_mask(path):
    """마스크 PNG에서 바운딩 박스를 파생한다(손으로 옮겨 적지 않는다 — S3 make_masks.py와 동일 원칙)."""
    m = np.array(Image.open(path).convert("L"))
    ys, xs = np.where(m > 0)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def clip_preprocess(im):
    im = im.convert("RGB")
    w, h = im.size
    scale = 224 / min(w, h)
    im = im.resize((round(w * scale), round(h * scale)), Image.BICUBIC)
    w, h = im.size
    left, top = (w - 224) // 2, (h - 224) // 2
    im = im.crop((left, top, left + 224, top + 224))
    arr = np.asarray(im).astype(np.float32) / 255.0
    arr = (arr - CLIP_MEAN) / CLIP_STD
    return torch.from_numpy(arr.transpose(2, 0, 1)).unsqueeze(0)


class Embedder:
    def __init__(self):
        self.device = "cpu"  # bigG(3.7GB) 1회 로드 후 27회 추론뿐 — mps 전환 복잡도 대비 이득 없음
        self.model = CLIPVisionModelWithProjection.from_pretrained(
            params.IMAGE_ENCODER, torch_dtype=torch.float32).to(self.device)
        self.model.eval()

    @torch.no_grad()
    def embed(self, im):
        x = clip_preprocess(im).to(self.device)
        out = self.model(x).image_embeds[0]
        return (out / out.norm()).cpu().numpy()


class TextEmbedder:
    """CLIP bigG **텍스트** 타워. `Embedder`(이미지 타워)와 같은 CLIP 쌍이라 결합 공간이 성립한다 —
    둘 다 `projection_dim = 1280`이고, 이미지 쪽은 IP-Adapter의 `sdxl_models/image_encoder`,
    텍스트 쪽은 SDXL의 `text_encoder_2`로 **둘 다 laion2B ViT-bigG-14**다.

    **새 의존성이 아니다** — 두 모델 다 이 파이프라인이 이미 받아 둔 캐시 안에 있다
    (`loop.md` Authorized replan scope의 「새 의존성 도입 금지」에 걸리지 않는다).
    """

    def __init__(self):
        self.device = "cpu"      # Embedder와 같은 이유 — 1회 로드 후 수십 회 추론뿐
        self.tok = CLIPTokenizer.from_pretrained(params.SDXL_BASE, subfolder="tokenizer_2")
        self.model = CLIPTextModelWithProjection.from_pretrained(
            params.SDXL_BASE, subfolder="text_encoder_2", torch_dtype=torch.float32).to(self.device)
        self.model.eval()

    @torch.no_grad()
    def embed(self, text):
        t = self.tok(text, padding="max_length", max_length=self.tok.model_max_length,
                     truncation=True, return_tensors="pt").to(self.device)
        e = self.model(**t).text_embeds[0]
        return (e / e.norm()).cpu().numpy()


def cos(a, b):
    return float(np.dot(a, b))


def ink_style_vector(im):
    """화풍 지표 = (그레이스케일 평균, 표준편차=대비, 에지밀도=잉크 선 밀도 근사).

    후보 셋(그램 행렬·색 히스토그램·잉크 밀도/대비) 중 이것을 고른 근거:
    1) SWEEP.md가 이미 실측한 실패 양상이 정확히 이것이다 — "화풍이 잉크 만화 쪽으로 기움"은
       대비 상승·선 밀도 상승으로 나타난다(연필 동화=낮은 대비·옅은 선, 잉크 만화=높은 대비·
       굵고 진한 선). 이 프로젝트의 실제 실패모드에 가장 직접 대응한다.
    2) 그램 행렬은 사전학습 CNN(VGG 등)의 중간 특징이 필요한데 torchvision이 이 환경에 없다 —
       새 의존성을 깔지 말라는 지시와 상충한다.
    3) 색 히스토그램도 후보였으나, 다윗·골리앗 레퍼런스 자체가 이미 같은 palette(warm cream,
       muted)라 색 분포만으로는 SWEEP.md가 지목한 "잉크화" 경향(선의 굵기·대비 문제)을 못 잡는다.
    4) CLIP 임베딩(④에 쓴 지표)은 내용에 강하게 반응한다고 요구사항이 명시 경고했으므로 화풍
       지표로는 배제한다 — PIL/numpy만으로 되는 그레이스케일 통계는 내용과 무관하게 화풍(선의
       밀도·대비)만 잰다.
    """
    g = np.asarray(im.convert("L"), dtype=np.float64)
    mean = g.mean()
    std = g.std()
    dx = np.abs(np.diff(g, axis=1))
    dy = np.abs(np.diff(g, axis=0))
    edge_density = (float((dx > EDGE_THRESHOLD).mean()) + float((dy > EDGE_THRESHOLD).mean())) / 2
    return np.array([mean, std, edge_density])


def main():
    frozen_d_path = os.path.join(params.FROZEN, "david.png")
    frozen_g_path = os.path.join(params.FROZEN, "goliath.png")
    bbox_d = bbox_from_mask(os.path.join(MASKS, "david.png"))
    bbox_g = bbox_from_mask(os.path.join(MASKS, "goliath.png"))
    print(f"다윗 마스크 bbox={bbox_d}  골리앗 마스크 bbox={bbox_g}")

    print(f"CLIP 이미지 인코더 로드 중 ({params.IP_ADAPTER_REPO} "
          f"{params.IP_ADAPTER_SUBFOLDER}/image_encoder, ViT-bigG)...")
    emb = Embedder()
    ref_d = emb.embed(Image.open(frozen_d_path))
    ref_g = emb.embed(Image.open(frozen_g_path))

    # --- 자가검사(SANITY) — 동결본 자신을 넣으면 유사도가 최대여야 지표가 안 깨진 것이다 ---
    self_d = cos(ref_d, ref_d)
    assert abs(self_d - 1.0) < 1e-4, f"자기 코사인 유사도가 1이 아니다: {self_d}"
    reload_d = emb.embed(Image.open(frozen_d_path))  # 파일을 다시 읽어 재추론(캐시된 벡터 재사용 아님)
    sim_reload_own = cos(reload_d, ref_d)
    sim_reload_other = cos(reload_d, ref_g)
    assert sim_reload_own > 0.999, f"동일 이미지 재인코딩 유사도가 낮다: {sim_reload_own}"
    assert sim_reload_own > sim_reload_other, (
        f"지표가 깨졌다 — 동결본 자신과의 유사도({sim_reload_own})가 "
        f"다른 인물 동결본과의 유사도({sim_reload_other})보다 낮다")
    print(f"SANITY 통과 — 다윗 동결본 재인코딩 자기유사도={sim_reload_own:.4f} > "
          f"교차유사도={sim_reload_other:.4f}")

    scene_images = {}
    style_vecs = {}
    for cond in CONDITIONS:
        for seed in params.SCENE_SEEDS:
            path = os.path.join(SCENE, f"{cond}-s{seed}.png")
            im = Image.open(path).convert("RGB")
            scene_images[(cond, seed)] = im
            style_vecs[(cond, seed)] = ink_style_vector(im)

    all_vecs = np.array([style_vecs[(c, s)] for c in CONDITIONS for s in params.SCENE_SEEDS])
    mu, sigma = all_vecs.mean(axis=0), all_vecs.std(axis=0)
    sigma = np.where(sigma == 0, 1.0, sigma)
    norm_vecs = {k: (v - mu) / sigma for k, v in style_vecs.items()}

    metric4, metric5 = [], []
    for cond in CONDITIONS:
        for seed in params.SCENE_SEEDS:
            im = scene_images[(cond, seed)]
            e_d = emb.embed(im.crop(bbox_d))
            e_g = emb.embed(im.crop(bbox_g))
            sim_d_own, sim_d_other = cos(e_d, ref_d), cos(e_d, ref_g)
            sim_g_own, sim_g_other = cos(e_g, ref_g), cos(e_g, ref_d)
            pass_d = sim_d_own > sim_d_other
            pass_g = sim_g_own > sim_g_other
            metric4.append({
                "condition": cond, "seed": seed,
                "sim_david_own": round(sim_d_own, 4), "sim_david_other": round(sim_d_other, 4),
                "pass_david": pass_d,
                "sim_goliath_own": round(sim_g_own, 4), "sim_goliath_other": round(sim_g_other, 4),
                "pass_goliath": pass_g,
                "pass4": pass_d and pass_g,
            })

            raw = style_vecs[(cond, seed)]
            dist_to_a = float(np.linalg.norm(norm_vecs[(cond, seed)] - norm_vecs[("a-none", seed)]))
            metric5.append({
                "condition": cond, "seed": seed,
                "mean_brightness": round(float(raw[0]), 2), "contrast_std": round(float(raw[1]), 2),
                "edge_density": round(float(raw[2]), 4),
                "style_dist_to_a_same_seed": round(dist_to_a, 4),
            })

    consistency = []
    for cond in CONDITIONS:
        vs = [norm_vecs[(cond, s)] for s in params.SCENE_SEEDS]
        pw = [float(np.linalg.norm(vs[i] - vs[j])) for i in range(3) for j in range(i + 1, 3)]
        consistency.append({
            "condition": cond, "pairwise_seed_distances": [round(x, 4) for x in pw],
            "mean_pairwise": round(sum(pw) / len(pw), 4), "max_pairwise": round(max(pw), 4),
        })

    b_rows = [r for r in metric4 if r["condition"] == "b-nomask"]
    b_fails_q4 = all(not r["pass4"] for r in b_rows)
    b_any_fails = any(not r["pass4"] for r in b_rows)

    out = {
        "bbox_david": bbox_d, "bbox_goliath": bbox_g,
        "metric4_cross_similarity": metric4,
        "metric5_style_distance": metric5,
        "metric5_within_condition_consistency": consistency,
        "b_all_3_seeds_fail_q4": b_fails_q4,
        "b_at_least_1_seed_fails_q4": b_any_fails,
        "sanity": {"self_cosine": self_d, "reload_own": sim_reload_own, "reload_other": sim_reload_other},
    }
    out_path = os.path.join(params.NOTES, "judge-metrics.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("\n=== ④ 교차 유사도 (통과 = 자기유사도 > 교차유사도, 다윗·골리앗 대칭) ===")
    for r in metric4:
        print(f"  {r['condition']:10s} s{r['seed']:<3d} 다윗:{r['sim_david_own']:.3f}/{r['sim_david_other']:.3f}"
              f"({'P' if r['pass_david'] else 'F'})  골리앗:{r['sim_goliath_own']:.3f}/{r['sim_goliath_other']:.3f}"
              f"({'P' if r['pass_goliath'] else 'F'})  전체:{'PASS' if r['pass4'] else 'FAIL'}")
    print(f"\n(b) 3시드 전부 ④ 실패 = {b_fails_q4}   (b) 최소 1시드 실패 = {b_any_fails}")

    print("\n=== ⑤ 화풍 거리(같은 시드의 (a) 대비, z-score 유클리드) ===")
    for r in metric5:
        print(f"  {r['condition']:10s} s{r['seed']:<3d} 거리={r['style_dist_to_a_same_seed']:.4f}"
              f"  (밝기{r['mean_brightness']:.1f} 대비{r['contrast_std']:.1f} 에지{r['edge_density']:.4f})")
    print("\n=== ⑤ 조건 내 3시드 산포(평균/최대 쌍거리) ===")
    for c in consistency:
        print(f"  {c['condition']:10s} 평균={c['mean_pairwise']:.4f} 최대={c['max_pairwise']:.4f}")

    print(f"\n저장: {out_path}")


if __name__ == "__main__":
    main()
