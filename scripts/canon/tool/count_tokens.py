#!/usr/bin/env python3
"""제안된 문구가 77토큰 안에 드는지 잰다 — **저장하기 전에** (2026-09-05, task 339 후속).

venv 파이썬으로 돈다(CLIP 토크나이저가 거기 있다). GPU는 쓰지 않는다.
`derive_scene`과 **같은 파생 규칙**을 지나므로 `{cast:...}` 확장까지 포함해 잰다 —
확장 전 길이로 재면 판 단계에서 한참 빗나간다.

  echo '{"scene":"<id>","prompt":"...","neg":["..."]}' | python count_tokens.py
  → {"n": 63, "lim": 77, "neg_n": 41, "ok": true, "filled": "<확장된 문구>"}
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import params  # noqa: E402
import derive_scene as ds  # noqa: E402


def main():
    req = json.load(sys.stdin)
    if os.environ.get("SCENE_TOOL_SCENES_DIR"):
        ds.SCENES_DIR = os.environ["SCENE_TOOL_SCENES_DIR"]
    prompt = f"{ds.ST} {ds._fill(req['prompt'])}"
    neg = ds.NEG + ", " + ", ".join(ds._fill(n) for n in (req.get("neg") or []))
    from transformers import CLIPTokenizer
    tok = CLIPTokenizer.from_pretrained(params.SDXL_BASE, subfolder="tokenizer")
    lim = tok.model_max_length
    n = len(tok(prompt).input_ids)
    json.dump({"n": n, "lim": lim, "neg_n": len(tok(neg).input_ids),
               "ok": n <= lim, "filled": prompt}, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
