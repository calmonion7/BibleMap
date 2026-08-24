"""task#315 S1 — gen/*.png에서 정본 얼굴을 frozen/에 동결한다. PIL만 쓴다(torch 불필요).

크롭 좌표는 cond-meta.json에서 파생한다(손으로 찍지 않는다). cond_shoot_heads.py의 클립 프레임 정의:
  half_width = D, top_margin = D*1.1, bottom_margin = D*0.75  (D = HEAD_DIAMETER, 머리 원 반지름 D/2)
  => 프레임 폭 = 2D, 높이 = 1.85D, 머리 중심의 분수 좌표 = (0.5, top_margin/(top_margin+bottom_margin))
   = (0.5, 1.1/1.85) = (0.5, 0.5945946...) — D가 약분되어 두 인물이 같은 분수값을 공유한다.

핵심 관찰(파생 결과, 눈대중 아님): 이 프레임 자체가 이미 cond-*-ctrl.png의 전체 캔버스다
(clip_box 비율 800:740 = 840:777 = 2D:1.85D, prep_cond.py는 단순 Image.resize — 크롭/레터박스 없음).
gen_candidates.py는 그 cond-*-ctrl.png(1024x1024)를 동일 크기(1024,1024)로 ControlNet에 그대로 먹여
gen/*.png를 같은 1024x1024 캔버스에 픽셀 1:1로 생성한다. 즉 **gen 캔버스 전체 = 파생된 프레임 그 자체**
— 정사각(1024x1024)이고, 머리 중심은 이미 분수 좌표 (0.5, 0.595)에 와 있다(위쪽 여백 1.1D가
아래쪽 0.75D보다 넉넉한 비대칭이 그 좌표에 이미 내재). 프레임 밖은 애초에 존재하지 않으므로
그보다 타이트한 크롭은 cond-meta.json에 없는 임의의 배율을 손으로 찍는 것이 되어 금지 사항을 어긴다.
따라서 파생된 크롭 박스는 (0, 0, W, H) — 캔버스 전체 — 이고, 아래 SANITY는 그 도출을 실행 가능한
형태로 남긴다(머리 중심 분수 좌표가 david·goliath에서 동일함을 단정).
"""
import hashlib
import json
import os

from PIL import Image

import params

GEN = os.path.join(params.OUT_ROOT, "gen")   # 후보 생성물 — 미추적
# 동결본은 추적 대상이다(scripts/canon/frozen/). 여기 쓰면 작업트리가 더러워지는 것이 정상 —
# 얼굴 정본이 바뀌었다는 뜻이므로 커밋으로 남아야 한다.

# (정본 이름, 동결할 후보, cond-meta.json 키)
TARGETS = [("david", "david-s11.png", "david"), ("goliath", "goliath-s42.png", "goliath")]


def head_center_fraction(meta):
    top, bot = meta["top_margin"], meta["bottom_margin"]
    return (0.5, top / (top + bot))


def main():
    with open(os.path.join(params.NOTES, "cond-meta.json"), encoding="utf-8") as f:
        cond_meta = json.load(f)
    os.makedirs(params.FROZEN, exist_ok=True)

    fractions = {}
    digests = {}
    for name, src_file, meta_key in TARGETS:
        fractions[name] = head_center_fraction(cond_meta[meta_key])

        im = Image.open(os.path.join(GEN, src_file)).convert("RGB")
        w, h = im.size
        assert w == h, f"{src_file}는 정사각이 아니다 ({w}x{h})"
        # 파생된 프레임 = 캔버스 전체이므로 크롭 박스는 (0, 0, w, h) — 위 docstring 참조.
        crop = im.crop((0, 0, w, h))

        out_path = os.path.join(params.FROZEN, f"{name}.png")
        crop.save(out_path)
        digests[name] = hashlib.sha256(open(out_path, "rb").read()).hexdigest()
        print(f"{name}: {src_file} ({w}x{h}) -> {out_path}  sha256={digests[name][:12]}...")

    # SANITY (완료기준의 실행 가능한 형태)
    assert fractions["david"] == fractions["goliath"], "두 인물의 머리 중심 분수 좌표가 달라졌다"
    fx, fy = fractions["david"]
    assert abs(fx - 0.5) < 1e-9
    assert abs(fy - 1.1 / 1.85) < 1e-9
    assert os.path.getsize(os.path.join(params.FROZEN, "david.png")) > 0
    assert os.path.getsize(os.path.join(params.FROZEN, "goliath.png")) > 0
    assert digests["david"] != digests["goliath"], "두 동결본의 sha256이 같다"
    print(f"\n머리 중심 분수 좌표(공통) = ({fx}, {fy:.6f})")
    print("SANITY 통과 — frozen/에 2건, 각 정사각, sha256 상이, 크기 > 0")


if __name__ == "__main__":
    main()
