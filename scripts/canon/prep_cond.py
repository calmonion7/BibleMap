"""조건 입력 PNG -> ControlNet 2값 조건 입력. `.forge/reports/storyboard-density/prep_ctrl.py`와
같은 산식(임계 60)을 쓰되, 배경 밝기를 코너 픽셀에서 실측해 **극성을 자동 판정**한다 — prep_ctrl.py는
"흰 종이+검은 잉크"만 가정하는데(255-a), `#/cast` 카드 배경은 어두운 테마 토큰(--bg-2: #1e2144, 밝은
크림색 잉크)이라 그 식을 그대로 쓰면 배경/잉크가 뒤집힌다(실측: cond-david.png 코너 그레이값 ≈ 어둠).
|a - bg| > 60 은 bg가 밝든 어둡든 같이 맞는 일반형이고, bg≈255(밝은 종이)일 때는
prep_ctrl.py의 (255-a) 식과 정확히 같은 값이 된다 — 그 레시피를 좁혀서 재사용한 것이지 새로 지은
임계가 아니다.

출력은 항상 흰 선(255)/검은 바탕(0) — 스크리블 ControlNet(params.CN_MODEL)이 기대하는 형식(run_grid.py
선례와 동일 관례).
"""
import json
import os
import sys

import numpy as np
from PIL import Image

import params

# (원본 파일, 목표 크기 WxH) — 크기의 근거는 params.py의 PERSON_SIZE·SCENE_SIZE 주석에 있다.
JOBS = [
    ("cond-david.png", params.PERSON_SIZE),
    ("cond-goliath.png", params.PERSON_SIZE),
    ("cond-scene.png", params.SCENE_SIZE),
]


def main():
    report = {}
    for src_name, size in JOBS:
        src = os.path.join(params.OUT_ROOT, src_name)
        if not os.path.exists(src):
            sys.exit(f"조건 입력이 없다: {src}")
        im = Image.open(src).convert("L").resize(size, Image.LANCZOS)
        a = np.array(im).astype(int)
        bg = int(np.median(a[0:8, 0:8]))  # 좌상단 코너 = 배경(모든 조건 입력이 그 모서리는 배경이다)
        ctrl = np.where(np.abs(a - bg) > params.THRESHOLD, 255, 0).astype(np.uint8)
        ink_ratio = ctrl.mean() / 255
        out = os.path.join(params.OUT_ROOT, src_name.replace(".png", "-ctrl.png"))
        Image.fromarray(np.stack([ctrl] * 3, -1)).save(out)
        print(f"{out}  bg={bg}  잉크율 {ink_ratio * 100:.2f}%  크기 {size}")
        report[src_name] = {"bg_corner_gray": bg, "ink_ratio": ink_ratio, "size": size, "out": out}
    write_cond_meta(report)
    return report


def write_cond_meta(report):
    """조건 입력 3건의 메타를 하나로 합쳐 cond-meta.json에 쓴다. 손으로 조립하지 않는다 —
    두상 2건은 cond_shoot_heads.py가, 장면 1건은 render_scene.py가 렌더 시각에 남긴 것을 읽는다."""
    meta = {}
    with open(os.path.join(params.NOTES, "cond-heads-meta.json"), encoding="utf-8") as f:
        meta.update(json.load(f))
    for v in meta.values():
        v["thin_stroke_width"] = params.THIN_SW
    with open(os.path.join(params.NOTES, "cond-scene-meta.json"), encoding="utf-8") as f:
        sc = json.load(f)
    shot = sc["shots"][0]
    meta["scene"] = {
        "target": "scene", "source": "frontend/src/sketches/davidUnitedKingdom.jsx GoliathScene",
        "at_ms": sc["at_ms"], "total_strokes": sc.get("total_strokes"),
        "inked_strokes": sc.get("inked_strokes"), "ghost_strokes": sc.get("ghost_strokes"),
        "text_nodes": shot.get("text_nodes"), "path": shot.get("path"),
    }
    for name, key in (("david", "cond-david.png"), ("goliath", "cond-goliath.png"),
                      ("scene", "cond-scene.png")):
        meta[name]["ctrl"] = report[key]["out"]
        meta[name]["ctrl_ink_ratio"] = round(report[key]["ink_ratio"], 5)
        meta[name]["ctrl_size"] = report[key]["size"]
    out = os.path.join(params.NOTES, "cond-meta.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"기록: {out}")


if __name__ == "__main__":
    main()
