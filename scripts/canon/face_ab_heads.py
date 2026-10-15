#!/usr/bin/env python3
"""task#346 S5 — 장면 그림에서 인물별 머리 상자를 찾는다.
OWLv2(google/owlv2-base-patch16-ensemble, Apache-2.0) 열린어휘 검출 "a human head…/a face" → 장면별 좌우 위치로 인물을 정하고 머리 크기로 넓힌다.
(claude -p VLM의 좌표 읽기는 이 장면들에서 100~200px 어긋나 못 썼다 — 실측.) CPU로 돈다(GPU 생성과 겹치지 않음).
  VENV=~/.local/biblemap-imggen/.venv314/bin/python; $VENV face_ab_heads.py <gilgal|engedi> <이미지>...
다른 스크립트는 heads(scene, path) → {인물: (x0,y0,x1,y1) 픽셀}을 import해 쓴다. 못 찾으면 키가 없다."""
import sys
from PIL import Image

MODEL = "google/owlv2-base-patch16-ensemble"
# 장면별 인물 → 얼굴이 놓이는 가로 구간(화면 폭 비율). 명세의 배치(길갈: 사무엘 왼쪽·사울 오른쪽, 엔게디: 다윗 왼쪽·사울 오른쪽).
SIDE = {"gilgal": {"samuel": (0, 0.35), "saul": (0.6, 1)}, "engedi": {"david": (0, 0.5), "saul": (0.5, 1)}}
GROW = 2.0      # 얼굴 상자 → 머리(머리카락·수염 포함) 배율
LIFT = 0.12     # 머리 중심을 얼굴 높이의 이만큼 위로 — 머리카락이 위쪽에 더 있다
_M = {}


def _faces(im):
    import torch
    from transformers import Owlv2Processor, Owlv2ForObjectDetection
    if not _M:
        _M["p"], _M["m"] = Owlv2Processor.from_pretrained(MODEL), Owlv2ForObjectDetection.from_pretrained(MODEL).eval()
    p, m = _M["p"], _M["m"]
    with torch.no_grad():
        o = m(**p(text=[["a human head with hair and beard", "a face"]], images=im, return_tensors="pt"))
    S = max(im.size)   # OWLv2는 정사각 패딩 기준 좌표
    r = p.post_process_grounded_object_detection(o, threshold=0.05, target_sizes=torch.tensor([[S, S]]))[0]
    return [([float(v) for v in b], float(s)) for b, s in zip(r["boxes"], r["scores"])]


def heads(scene, path):
    im = Image.open(path).convert("RGB")
    faces = _faces(im)
    out = {}
    for who, (lo, hi) in SIDE[scene].items():
        c = [(s, b) for b, s in faces if lo * im.width <= (b[0] + b[2]) / 2 <= hi * im.width]
        if not c:
            continue
        x0, y0, x1, y1 = max(c)[1]
        cx, cy, w, h = (x0 + x1) / 2, (y0 + y1) / 2 - LIFT * (y1 - y0), (x1 - x0) * GROW, (y1 - y0) * GROW
        out[who] = (max(0, cx - w / 2), max(0, cy - h / 2), min(im.width, cx + w / 2), min(im.height, cy + h / 2))
    return out


if __name__ == "__main__":
    for p in sys.argv[2:]:
        print(p, {k: [round(v) for v in b] for k, b in heads(sys.argv[1], p).items()})
