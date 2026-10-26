#!/usr/bin/env python3
"""mflux-generate-qwen-edit 실행용 래퍼 — `--guidance 1`일 때 스텝마다 도는 부정 프롬프트 트랜스포머 계산을 건너뛴다.

mflux 0.22.0 qwen_image_edit.py는 guidance 값과 상관없이 스텝마다 트랜스포머를 2회(긍정·부정) 돈다.
혼합식 neg + g·(pos − neg)는 g = 1이면 pos이므로, 부정 차례에 긍정 결과를 그대로 돌려주면 결과는 같고 계산은 절반이다.
설치된 패키지는 고치지 않는다(이 프로세스 안에서만 바꿔 끼움). 인자는 mflux-generate-qwen-edit와 같다.

  ~/.local/biblemap-imggen/.venv-mflux/bin/python mflux_qwen_edit_cfg1.py --model qwen-image-edit-2511 --guidance 1 ...
"""
import sys

from mflux.models.qwen.cli.qwen_image_edit_generate import main
from mflux.models.qwen.model.qwen_transformer.qwen_transformer import QwenTransformer

g = sys.argv[sys.argv.index("--guidance") + 1] if "--guidance" in sys.argv else None
if g is None or float(g) != 1.0:
    sys.exit("[QwenEditCfg1] --guidance 1 전용 — 다른 값이면 부정 계산을 건너뛸 수 없다")

_orig = QwenTransformer.__call__
_st = {"n": 0, "pos": None}


def _call(self, *a, **k):
    _st["n"] += 1
    if _st["n"] % 2 == 0:   # 부정 프롬프트 차례(qwen_image_edit.py에서 긍정 → 부정 순서로 부름)
        return _st["pos"]
    _st["pos"] = _orig(self, *a, **k)
    return _st["pos"]


QwenTransformer.__call__ = _call
sys.argv[0] = "mflux-generate-qwen-edit"
sys.exit(main())
