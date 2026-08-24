"""GoliathScene(--at 9000)에서 다윗·골리앗·배경 영역 마스크 3장을 파생한다(task#315 S3).

붓질 단계(delay) 범위로 stroke를 갈라 두 인물만 따로 찍고(render_scene.py --delay-range,
잉크 기준까지 포함 — ADR 260822-111304 2026-08-24 개정), 그 잉크의 **바운딩 박스**를 인물
영역으로 채운다(선→면 변환, 근거는 아래 BBOX_RATIONALE 및 MASKS.md). 배경은 두 인물 영역의
여집합 — 별도로 찍지 않는다.

delay 범위는 scripts/check_mask_ranges.py의 derive_ranges()에서 그대로 가져온다(손으로 옮겨
적지 않는다 — ADR 260820-003946). 그 범위가 무엇을 넣고 뺐는지(충격 표시·흙먼지 처분)는
그 모듈의 docstring과 MASKS.md 참조.
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image

import params

SCRIPTS = os.path.join(params.REPO_ROOT, "scripts")
sys.path.insert(0, SCRIPTS)
from check_mask_ranges import derive_ranges  # noqa: E402

# 임계는 params.THRESHOLD 하나만 읽는다 — 이전에는 prep_cond.py를 경유했지만 그 파일도
# 이제 정본을 읽으므로 경유가 한 겹 늘 뿐이다(같은 임계·같은 극성이라는 요구는 그대로).
OUT_DIR = os.path.join(params.OUT_ROOT, "masks")

BBOX_RATIONALE = (
    "바운딩 박스 채택(볼록껍질·팽창 대신) — 두 인물이 화면에서 좌우로 완전히 분리돼 있어"
    "(다윗 delay-range 잉크의 x범위와 골리앗 것이 실측으로 서로 안 겹친다) 바운딩 박스만으로도"
    "겹침이 0이 되고, 파라미터(팽창 반지름 등) 없이 PIL만으로 되며(eco), 사지 사이 빈 공간까지"
    "인물 영역에 포함해 스타일 참조가 실루엣 가장자리에서 잘리지 않는다(계획이 경고한 두 실패"
    "중 '빡빡해서 잘림' 쪽을 피한다 — '헐거워서 배경이 번짐' 쪽으로 의도적으로 기운다)."
)


def _raw_capture(name, lo, hi, out_path):
    cmd = [sys.executable, os.path.join(SCRIPTS, "render_scene.py"), "GoliathScene",
           "--at", "9000", "--no-labels", "--no-build",
           "--delay-range", f"{lo},{hi}", "--out", out_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        sys.exit(f"{name} 캡처 실패:\n{r.stderr}")


def _ink_mask(png_path):
    """prep_cond.py와 같은 산식 — 코너를 배경으로 보고 |a-bg|>params.THRESHOLD를 잉크로 본다."""
    im = Image.open(png_path).convert("L").resize(params.SCENE_SIZE, Image.LANCZOS)
    a = np.array(im).astype(int)
    bg = int(np.median(a[0:8, 0:8]))
    return np.abs(a - bg) > params.THRESHOLD


def _bbox_mask(ink):
    ys, xs = np.where(ink)
    if len(xs) == 0:
        sys.exit("잉크 픽셀이 0이다 — delay 범위 또는 --at이 어긋났다")
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    mask = np.zeros(ink.shape, dtype=np.uint8)
    mask[y0:y1 + 1, x0:x1 + 1] = 255
    return mask, (int(x0), int(y0), int(x1), int(y1))


def main():
    ranges = derive_ranges()
    os.makedirs(OUT_DIR, exist_ok=True)

    raw_david = os.path.join(OUT_DIR, "_raw_david.png")
    raw_goliath = os.path.join(OUT_DIR, "_raw_goliath.png")
    _raw_capture("david", *ranges["david"], raw_david)
    _raw_capture("goliath", *ranges["goliath"], raw_goliath)

    david_ink = _ink_mask(raw_david)
    goliath_ink = _ink_mask(raw_goliath)
    david_mask, david_bbox = _bbox_mask(david_ink)
    goliath_mask, goliath_bbox = _bbox_mask(goliath_ink)

    overlap_px = int(np.sum((david_mask > 0) & (goliath_mask > 0)))
    person_union = (david_mask > 0) | (goliath_mask > 0)
    background_mask = np.where(person_union, 0, 255).astype(np.uint8)

    # 완료기준 단정 — 겹침 0, 세 마스크의 합집합이 화면을 정확히 한 번씩 덮음.
    assert overlap_px == 0, f"인물 두 마스크가 {overlap_px}px 겹친다"
    coverage = ((david_mask > 0).astype(int) + (goliath_mask > 0).astype(int)
                + (background_mask > 0).astype(int))
    assert np.all(coverage == 1), (
        f"세 마스크가 화면을 정확히 한 번씩 덮지 못한다 — 덮임 횟수 분포 {np.unique(coverage, return_counts=True)}")

    Image.fromarray(david_mask, mode="L").save(os.path.join(OUT_DIR, "david.png"))
    Image.fromarray(goliath_mask, mode="L").save(os.path.join(OUT_DIR, "goliath.png"))
    Image.fromarray(background_mask, mode="L").save(os.path.join(OUT_DIR, "background.png"))

    print(f"delay 범위 — 다윗 {ranges['david']}  골리앗 {ranges['goliath']}")
    print(f"다윗 bbox(x0,y0,x1,y1) = {david_bbox}  잉크 {int(david_ink.sum())}px")
    print(f"골리앗 bbox(x0,y0,x1,y1) = {goliath_bbox}  잉크 {int(goliath_ink.sum())}px")
    print(f"겹침 픽셀 = {overlap_px} (기대 0)")
    print(f"커버리지 = 화면 전체 {coverage.size}px, 모두 정확히 1회 피복 확인")
    print(f"저장: {OUT_DIR}/david.png · goliath.png · background.png ({params.SCENE_SIZE[0]}x{params.SCENE_SIZE[1]})")


if __name__ == "__main__":
    main()
