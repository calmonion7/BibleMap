#!/usr/bin/env python3
"""얼굴 판정 화면 표시 규칙 v2(task 393, notes/FACE-LORA-V3.md 「다시 판정」) — 그림은 그대로, 화면만 바꿔 기브아 C·V2·V3 24장을 다시 묻는다.
  python3 make_face_judge_v2.py   → ~/.local/biblemap-imggen/pages/face-judge-v2.html

v1(face-lora-v3)의 편향: 정본(768px 선명) 대 장면 머리(100px 남짓을 320px로 키움) — 화질 차가 「다른 사람」 쪽으로 기울였다.
  문항 A(48) 정본 화질 맞춤: 정본 정면·3/4를 그 크롭의 원래 화소 크기로 줄였다가 크롭과 같은 LANCZOS로 320px.
  문항 B(48) 장면 대 장면: 같은 갈래 기브아 머리 대 다른 장면 승인 그림의 같은 인물 머리, 둘 다 같은 방식으로 320px.
  화풍(24): 그림 한 장 + 기준(368 승인 바탕 s5) — 「같은 화풍인가」만, 장면 뜻은 묻지 않음.
모든 화면 위에 장면 구절 원문(삼상 18:6-11 개역한글, 순간 절 굵게). 갈래 이름은 숨기고 고정 시드로 섞는다."""
import json, os, random

from PIL import Image, ImageFilter, ImageStat

import check_scenes as CS
import params
from make_face_angles_page import TEMPLATE, uri
from make_night_page import fit

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.expanduser("~/.local/biblemap-imggen")
PAGE = os.path.join(IMG, "pages", "face-judge-v2.html")
HEADS = os.path.join(HERE, "samples", "face-lora-v3", "heads.json")   # v1 화면과 같은 머리 상자(OWLv2)
SCENE = os.path.join(IMG, "lora-v3-scene")
ARMS = ("C", "V2", "V3")
NAME = {"saul": "사울", "david": "다윗"}
SIDE = 320
RANGE, MOMENT = "18:6-11", {"18:10"}   # 기브아 창 장면 구절 · 지금 명세 moment.verse
# 문항 B 기준 머리: 다른 장면 승인 그림(고정 절) — 몸 상자는 그 묶음 metrics의 같은 시드 기록
OTHER = {"saul": ("whole-fix", "authored-saul-gilgal-amalek", 11, "saul", "base/s11.png", "길갈 아말렉 승인 그림의 사울"),
         "david": ("whole-wide", "authored-david-gibeah-harp", 11, "david-boy", "edit/s11.png", "기브아 수금 승인 그림의 다윗")}
STYLE_REF = os.path.join(IMG, "night-pilot", "authored-saul-gibeah-spear", "base", "s5.png")


def crop(im, box):
    """머리 상자 → (크롭 원본, 원래 변 길이 px) — v1 화면과 같은 fit(…, 1, W, H, 0.5)."""
    W, H = im.size
    x, y, w, h = fit(box, 1, W, H, 0.5)
    c = im.convert("RGB").crop((round(x * W), round(y * H), round((x + w) * W), round((y + h) * H)))
    return c, max(c.size)


def up(im):
    """크롭과 같은 방식으로 320px."""
    return im.resize((SIDE, round(SIDE * im.height / im.width)), Image.LANCZOS)


def matched(canon, side):
    """정본을 크롭의 원래 화소 크기(긴 변 side px)로 줄였다가 크롭과 같은 방식으로 320px — 화질 맞춤."""
    im = canon.convert("RGB")
    k = side / max(im.size)
    return up(im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS))


def hf(im):
    """고주파 에너지 = 회색조 라플라시안 절댓값 평균(흐림 정도 비교용)."""
    g = im.convert("L").filter(ImageFilter.Kernel((3, 3), (0, 1, 0, 1, -4, 1, 0, 1, 0), 1, 128))
    return sum(abs(v - 128) * n for v, n in enumerate(g.histogram())) / (g.width * g.height)


def scripture():
    vs = json.load(open(CS.VERSES, encoding="utf-8"))
    return [[f"{int(v[2:5])}:{int(v[5:])}", vs[v]["textKo"].strip(), f"{int(v[2:5])}:{int(v[5:])}" in MOMENT]
            for v in CS.verse_ids(CS.BOOK["삼상"], RANGE)]


def other_head(who):
    d, sid, seed, cast, rel, cap = OTHER[who]
    m = json.load(open(os.path.join(HERE, "samples", d, "metrics.json")))
    box = next(x["boxes"][cast]["head"] for x in m["scenes"][sid]["seeds"] if str(x["seed"]) == str(seed))
    return up(crop(Image.open(os.path.join(IMG, d, sid, rel)), box)[0]), cap


def questions():
    boxes = json.load(open(HEADS))
    canon = {w: (Image.open(os.path.join(HERE, "frozen", f"{w}.png")), Image.open(os.path.join(IMG, "face-angles", "views", f"pick-{w}.png")))
             for w in params.LORA_V3_WHO}
    other = {w: other_head(w) for w in params.LORA_V3_WHO}
    style_ref = uri(Image.open(STYLE_REF), 900)
    a, b, st = [], [], []
    for arm in ARMS:
        for s in params.LORA_V3_SCENE_SEEDS:
            im = Image.open(os.path.join(SCENE, f"{arm}-s{s}.png"))
            for w in params.LORA_V3_WHO:
                if w not in boxes[f"{arm}-s{s}"]:
                    continue
                c, side = crop(im, boxes[f"{arm}-s{s}"][w])
                head = up(c)
                front, three = (matched(x, side) for x in canon[w])
                a.append({"id": f"A:{arm}:{s}:{w}", "tag": "정본과 같은 사람인가", "q": f"가운데 머리가 {NAME[w]} 정본과 같은 사람인가요?",
                          "hint": f"정본 두 장을 이 머리와 같은 화질({side}px)로 줄였다 키웠습니다. 얼굴·머리·수염·나이대만 봅니다(옷은 빼고).",
                          "refs": [uri(front), uri(three)], "caps": ["정본 정면(화질 맞춤)", "정본 3/4 측면(화질 맞춤)"], "img": uri(head),
                          "hf": [round(hf(head), 2), round(hf(front), 2), round(hf(three), 2)]})
                b.append({"id": f"B:{arm}:{s}:{w}", "tag": "두 장면의 같은 사람인가", "q": f"두 머리가 같은 사람({NAME[w]})인가요?",
                          "hint": "위는 다른 장면의 승인 그림, 아래는 판정할 그림입니다. 둘 다 같은 방식으로 키웠습니다. "
                                  + ("위 다윗은 소년 때라 나이·수염은 빼고 얼굴 생김새·머리털로 봅니다." if w == "david" else "얼굴·머리·수염·나이대만 봅니다."),
                          "refs": [uri(other[w][0])], "caps": [other[w][1]], "img": uri(head)})
            st.append({"id": f"style:{arm}:{s}", "tag": "화풍", "wide": True, "q": "이 그림이 기준 그림과 같은 화풍인가요?",
                       "hint": "연필·색연필 동화 그림체만 봅니다. 장면 뜻·인물은 묻지 않습니다.", "yes": "같은 화풍", "no": "크게 다름",
                       "refs": [style_ref], "caps": ["기준(승인된 기브아 창 그림)"], "img": uri(im, 900)})
    random.Random(1022).shuffle(a)
    random.Random(1024).shuffle(b)
    random.Random(1023).shuffle(st)
    return a + b + st


def page(qs, verses):
    t = TEMPLATE.replace("<title>얼굴 각도 판정</title>", "<title>얼굴 판정 v2</title>").replace("판정 face-angles", "판정 face-judge-v2")
    t = t.replace("textarea {", ".verse { max-height: 9.5em; overflow-y: auto; background: var(--panel); border: 1px solid var(--line); border-radius: 6px; padding: 8px 10px; font-size: 13.5px; line-height: 1.55 }\n"
                  ".verse p { margin: 0 0 4px } .verse b { color: var(--accent) } .verse .r { color: var(--muted); font: 12px var(--mono); margin-right: 4px }\n"
                  ".refs figure.one { max-width: 320px; margin: 0 auto }\ntextarea {")
    t = t.replace('const cap = q.refs.length > 1 ? ["정본 정면", "정본 3/4 측면"] : ["정본"];', "const cap = q.caps;")
    t = t.replace("<h2>${q.q}</h2>", "<div class=\"verse\" aria-label=\"장면 구절 삼상 18:6-11\">${VERSE}</div>\n    <h2>${q.q}</h2>")
    t = t.replace('`<figure><img src="${r}"', '`<figure${q.refs.length === 1 ? \' class="one"\' : ""}><img src="${r}"')
    t = t.replace("const ans = {};", "const VERSE = __VERSE__;\nconst ans = {};")
    html = "<p class=\"r\">삼상 18:6-11 (개역한글)</p>" + "".join(
        f"<p>{'<b>' if now else ''}<span class=\"r\">{ref}</span>{txt}{'</b>' if now else ''}</p>" for ref, txt, now in verses)
    return t.replace("__VERSE__", json.dumps(html, ensure_ascii=False)).replace("__QS__", json.dumps(qs, ensure_ascii=False))


if __name__ == "__main__":
    os.makedirs(os.path.dirname(PAGE), exist_ok=True)
    qs = questions()
    open(PAGE, "w", encoding="utf-8").write(page(qs, scripture()))
    print(PAGE, len(qs), "문항", round(os.path.getsize(PAGE) / 1e6, 2), "MB")
