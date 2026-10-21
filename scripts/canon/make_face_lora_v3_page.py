#!/usr/bin/env python3
"""인물 LoRA v3 사람 판정 화면(notes/FACE-LORA-V3.md 고정 절) — FACE-ANGLES 화면과 같은 꼴.
  ~/.local/biblemap-imggen/.venv314/bin/python make_face_lora_v3_page.py   → pages/face-lora-v3.html + samples/face-lora-v3/heads.json
앞 48문항 = C·V2·V3 머리 크롭 블라인드 「정본과 같은 사람인가」(머리 상자 OWLv2, 고정 시드로 섞음), 뒤 24문항 = 그림 한 장씩 화풍·장면 무너짐."""
import json, os, random

from PIL import Image

import face_ab_heads as fh
import params
from gen_face_angles import pick_path
from gen_lora_v3 import ARMS, SCENE_OUT
from make_face_angles_page import TEMPLATE, uri
from make_night_page import fit

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.expanduser("~/.local/biblemap-imggen/pages/face-lora-v3.html")
HEADS = os.path.join(HERE, "samples", "face-lora-v3", "heads.json")
NAME = {"saul": "사울", "david": "다윗"}
fh.SIDE["gibeah"] = {"david": (0, 0.5), "saul": (0.5, 1)}   # 기브아 창: 다윗 왼쪽(수금)·사울 오른쪽(창)


def head_boxes():
    if os.path.exists(HEADS):
        return json.load(open(HEADS))
    out = {f"{arm}-s{s}": {w: [round(v) for v in b] for w, b in fh.heads("gibeah", os.path.join(SCENE_OUT, f"{arm}-s{s}.png")).items()}
           for arm in ARMS for s in params.LORA_V3_SCENE_SEEDS}
    os.makedirs(os.path.dirname(HEADS), exist_ok=True)
    json.dump(out, open(HEADS, "w"), indent=1)
    return out


def questions():
    boxes = head_boxes()
    canon = {w: uri(Image.open(os.path.join(HERE, "frozen", f"{w}.png"))) for w in params.LORA_V3_WHO}
    angle = {w: uri(Image.open(pick_path(w))) for w in params.LORA_V3_WHO}
    crops, style = [], []
    for arm in ARMS:
        for s in params.LORA_V3_SCENE_SEEDS:
            src = os.path.join(SCENE_OUT, f"{arm}-s{s}.png")
            im = Image.open(src)
            W, H = im.size
            for w in params.LORA_V3_WHO:
                b = boxes[f"{arm}-s{s}"].get(w)
                if not b:   # 못 찾으면 그 문항 없음(기록은 heads.json)
                    continue
                x, y, cw, ch = fit(b, 1, W, H, 0.5)
                crop = im.crop((round(x * W), round(y * H), round((x + cw) * W), round((y + ch) * H))).resize((320, 320), Image.LANCZOS)
                crops.append({"id": f"{arm}:{s}:{w}", "q": f"가운데 머리가 {NAME[w]} 정본과 같은 사람인가요?",
                              "hint": "얼굴·머리·수염·나이대만 봅니다(옷은 빼고). 위 두 장이 정본(정면·3/4 측면)입니다.",
                              "refs": [canon[w], angle[w]], "img": uri(crop)})
            style.append({"id": f"style:{arm}:{s}", "tag": "화풍·장면", "wide": True,
                          "q": "이 그림의 화풍이나 장면이 무너졌나요?",
                          "hint": "장면: 기브아 궁에서 사울은 창을 쥐고 서 있고, 다윗은 앉아 수금을 탑니다.", "yes": "무너지지 않음", "no": "무너짐",
                          "refs": [], "img": uri(im, 900)})
    random.Random(1022).shuffle(crops)
    random.Random(1023).shuffle(style)
    return crops + style


if __name__ == "__main__":
    os.makedirs(os.path.dirname(PAGE), exist_ok=True)
    qs = questions()
    open(PAGE, "w", encoding="utf-8").write(TEMPLATE.replace("<title>얼굴 각도 판정</title>", "<title>인물 LoRA v3 판정</title>")
                                           .replace("판정 face-angles", "판정 face-lora-v3").replace("__QS__", json.dumps(qs, ensure_ascii=False)))
    print(PAGE, len(qs), "문항", round(os.path.getsize(PAGE) / 1e6, 2), "MB")
