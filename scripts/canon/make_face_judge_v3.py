#!/usr/bin/env python3
"""C 장면 + V3 얼굴 보정 되붙임 판정 화면(task 395, notes/FACE-DETAIL-V3.md 고정 절).
  python3 make_face_judge_v3.py   → ~/.local/biblemap-imggen/pages/face-detail-v3.html

  문항 A(32) 정본과 같은 사람인가: V3 보정 머리 16 + 대조군 393 C 보정 머리(LoRA 없음) 16을 갈래 이름 없이 섞음 —
             화질·크기 맞춤은 393 v2 규칙(make_face_judge_v2) 그대로.
  문항 B1(8) C 원본과 같은 화풍인가: C 원본(기준)과 완성 그림.
  문항 B2(8) 머리 둘레가 깨끗한가: 완성 그림의 두 머리 둘레(보정 정사각 영역) 확대.
모든 화면 위에 삼상 18:6-11 원문(18:10 굵게)."""
import json, os, random

from PIL import Image

import gen_face_detail as G
import make_face_judge_v2 as V
import params

PAGE = os.path.join(V.IMG, "pages", "face-detail-v3.html")
HEADS_V3 = os.path.join(G.V3_OUT, "heads")
PASTE = os.path.join(G.V3_OUT, "paste")
ARMS = {"V3": HEADS_V3, "C": V.DETAIL}   # 판정 갈래 · 대조군(393 C 보정 머리)
NAME = V.NAME


def scene(s):
    return Image.open(os.path.join(V.SCENE, f"C-s{s}.png"))


def head(arm, s, w, box):
    return V.up(V.detail_crop(f"C-s{s}-{w}", scene(s), box, ARMS[arm])[0])


def questions():
    boxes = json.load(open(V.HEADS))
    canon = {w: (Image.open(os.path.join(V.HERE, "frozen", f"{w}.png")), Image.open(os.path.join(V.IMG, "face-angles", "views", f"pick-{w}.png")))
             for w in params.LORA_V3_WHO}
    a, b1, b2 = [], [], []
    for s in params.LORA_V3_SCENE_SEEDS:
        bx = boxes[f"C-s{s}"]
        for arm in ARMS:
            for w in params.LORA_V3_WHO:
                h = head(arm, s, w, bx[w])
                (front, _), (three, _) = (V.matched_to(x, V.hf(h)) for x in canon[w])
                a.append({"id": f"A:{arm}:{s}:{w}", "tag": "정본과 같은 사람인가", "q": f"가운데 머리가 {NAME[w]} 정본과 같은 사람인가요?",
                          "hint": "정본 두 장을 이 머리와 같은 선명도로 맞췄습니다. 얼굴·머리·수염·나이대만 봅니다(옷은 빼고).",
                          "refs": [V.uri(front), V.uri(three)], "caps": ["정본 정면(화질 맞춤)", "정본 3/4 측면(화질 맞춤)"], "img": V.uri(h),
                          "hf": [round(V.hf(h), 2), round(V.hf(front), 2), round(V.hf(three), 2)]})
        orig, done = scene(s), Image.open(os.path.join(PASTE, f"C-s{s}.png"))
        b1.append({"id": f"B1:{s}", "tag": "화풍", "wide": True, "q": "완성 그림이 기준(C 원본)과 같은 화풍인가요?",
                   "hint": "얼굴만 다시 그려 붙인 그림입니다. 연필·색연필 동화 그림체가 원본과 같은지만 봅니다.", "yes": "같은 화풍", "no": "크게 다름",
                   "refs": [V.uri(orig, 1024)], "caps": ["기준 — C 원본"], "img": V.uri(done, 1024)})
        crops = [V.up(done.convert("RGB").crop(tuple(G.region(bx[w], *done.size)))) for w in params.LORA_V3_WHO]
        b2.append({"id": f"B2:{s}", "tag": "머리 둘레", "wide": True, "q": "두 머리 둘레가 깨끗한가요?",
                   "hint": "위는 머리 둘레 확대, 아래는 완성 그림 전체입니다. 머리 경계에 이음새·색 차이·결(선 굵기·질감) 차이가 보이면 「이음새 보임」.",
                   "yes": "깨끗함", "no": "이음새 보임", "refs": [V.uri(c) for c in crops], "caps": [f"{NAME[w]} 머리 둘레" for w in params.LORA_V3_WHO],
                   "img": V.uri(done, 1024)})
    random.Random(1395).shuffle(a)
    random.Random(1396).shuffle(b1)
    random.Random(1397).shuffle(b2)
    return a + b1 + b2


def page(qs, verses):
    return (V.page(qs, verses).replace("<title>얼굴 판정 v2</title>", "<title>얼굴 보정 판정</title>")
            .replace("판정 face-judge-v2", "판정 face-detail-v3"))


if __name__ == "__main__":
    os.makedirs(os.path.dirname(PAGE), exist_ok=True)
    qs = questions()
    open(PAGE, "w", encoding="utf-8").write(page(qs, V.scripture()))
    print(PAGE, len(qs), "문항", round(os.path.getsize(PAGE) / 1e6, 2), "MB")
