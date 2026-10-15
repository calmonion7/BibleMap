#!/usr/bin/env python3
"""task#348 S4 — 사람 판정 페이지(한 화면 한 질문)를 만든다. 틀(CSS·문항 넘기기·판정 문장 복사)은 347 판정 페이지를 그대로 쓴다.
  python3 make_face_widen_page.py <347 페이지 HTML> <출력 HTML>
머리 상자는 samples/face-widen/metrics.json(B-e에서 찾은 상자 — R1도 같은 자리에 붙였다)에서 읽는다. 기계 결과와 상관없이 6머리 전부 넣는다."""
import base64, io, json, os, sys

from PIL import Image

import params

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "samples", "face-widen")
FROZEN = os.path.join(HERE, "frozen")
G = params.FACE_WIDEN_R1_GROW
NAME = {"david": "다윗", "saul": "사울", "samuel": "사무엘", "goliath": "골리앗", "gilgal": "길갈"}
SAME = ["같은 사람", "다른 사람"]


def uri(im, w=None):
    if w and im.width != w:
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    b = io.BytesIO()
    im.convert("RGB").save(b, "JPEG", quality=86)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def fig(src, cap, cls="", native=False):
    style = ' style="width:auto;max-width:100%"' if native else ""
    return f'<figure class="{cls}"><img src="{src}" alt="{cap}"{style}><figcaption>{cap}</figcaption></figure>'


def crop(im, box, scale):
    x0, y0, x1, y1 = box
    cx, cy, s = (x0 + x1) / 2, (y0 + y1) / 2, max(x1 - x0, y1 - y0) * scale / 2
    s = min(s, im.width / 2, im.height / 2)
    cx, cy = min(max(cx, s), im.width - s), min(max(cy, s), im.height - s)   # 그림 밖(검은 띠)으로 나가지 않게 안쪽으로 민다
    return im.crop((round(cx - s), round(cy - s), round(cx + s), round(cy + s)))


def img(name):
    return Image.open(os.path.join(OUT, name + ".png")).convert("RGB")


def screens():
    met = json.load(open(os.path.join(OUT, "metrics.json")))
    canon = {w: uri(Image.open(os.path.join(FROZEN, f"{w}.png")), 360) for w in ("david", "saul", "samuel")}
    sc = []
    vocab = json.load(open(os.path.join(HERE, "cast", "samuel.json"), encoding="utf-8"))
    sc.append({"id": "q0-samuel-canon", "q": "⓪ 새 사무엘 정본이 사무엘다운가?",
               "look": f"정본 어휘: 노선지자 · 백발 · 긴 흰 수염 · 마름({vocab['age']}, {vocab['hair']}, {vocab['beard']}, {vocab['build']}). "
                       "이 얼굴을 앞으로 사무엘의 기준으로 써도 되는지 보세요.",
               "body": '<div class="ref1">' + fig(canon["samuel"], "새 사무엘 정본(Z-Image)") + "</div>",
               "opts": ["사무엘답다", "아니다"]})
    heads = [(s, seed, w) for s, (_, ws) in params.FACE_WIDEN_SCENES.items() for w in ws for seed in params.FACE_WIDEN_SEEDS]
    for scene, seed, who in heads:
        box = met[f"B-e-{scene}-s{seed}"]["heads"][who]["box"]
        tag = f"{NAME[scene]} s{seed} {NAME[who]}"
        age = (" 정본은 20대 청년입니다. 승인본 장면의 다윗은 수염 없는 소년이었습니다. 여기서는 정본과 같은 사람인지만 보세요."
               if scene == "goliath" else "")
        be = uri(crop(img(f"B-e-{scene}-s{seed}"), box, 1.6), 360)
        r1 = uri(crop(img(f"R1-g{G}-{scene}-s{seed}"), box, 1.6), 360)
        sc.append({"id": f"q1-{scene}-s{seed}-{who}", "q": f"① {tag} · klein 원본 얼굴이 정본과 같은 사람인가?",
                   "look": "얼굴 구조(눈·코·입 비율, 수염·머리 모양, 나이대)만 보세요. 화풍 차이는 무시합니다." + age,
                   "body": '<div class="ref">' + fig(canon[who], "정본(기준)") + fig(be, "klein 원본(B-e)", "b") + "</div>",
                   "opts": SAME})
        sc.append({"id": f"q2-{scene}-s{seed}-{who}", "q": f"② {tag} · R1 머리가 정본과 같은 사람인가?",
                   "look": "R1은 klein 머리를 승인본 위에 색을 맞춰 붙인 것입니다. 얼굴 구조만 보세요." + age,
                   "body": '<div class="ref">' + fig(canon[who], "정본(기준)") + fig(r1, "R1 머리", "a") + "</div>",
                   "opts": SAME})
    for scene, (_, ws) in params.FACE_WIDEN_SCENES.items():
        s42, s23 = (f"R1-g{G}-{scene}-s{seed}" for seed in params.FACE_WIDEN_SEEDS)
        sc.append({"id": f"q3-{scene}-style", "q": f"③ {NAME[scene]} · 연필 화풍이 승인본과 같은가?",
                   "look": "색·잉크 진하기·선 질감을 보세요. 맨 위 승인본(345)이 목표입니다. 맨 아래는 화풍을 잃은 klein 원본(참고).",
                   "body": '<div class="ref1">' + fig(uri(img(f"approved-{scene}"), 900), "승인본(목표 화풍)") + "</div>"
                           + '<div class="ab1">' + fig(uri(img(s42), 900), "R1 s42", "a") + fig(uri(img(s23), 900), "R1 s23", "a") + "</div>"
                           + '<div class="ref1">' + fig(uri(img(f"B-e-{scene}-s42"), 900), "klein 원본 s42(화풍 잃음)") + "</div>",
                   "opts": ["둘 다 같다", "s42만 같다", "s23만 같다", "둘 다 아니다"]})
        body = ""
        for who in ws:
            body += f"<h3>{NAME[who]} 머리 둘레 · 원본 화소 크기</h3><div class=\"ab1\">"
            for seed in params.FACE_WIDEN_SEEDS:
                box = met[f"B-e-{scene}-s{seed}"]["heads"][who]["box"]
                body += fig(uri(crop(img(f"R1-g{G}-{scene}-s{seed}"), box, 2.6)), f"R1 s{seed}", "a", native=True)
            body += "</div>"
        sc.append({"id": f"q4-{scene}-seam", "q": f"④ {NAME[scene]} · 붙인 티·이음새가 보이는가?",
                   "look": "머리 둘레를 보세요. 얼룩진 테두리, 밝거나 색이 다른 둥근 띠, 질감이 갑자기 바뀌는 선이 있는지. 그림은 확대하지 않은 원본 화소입니다.",
                   "body": body, "opts": ["s42에 보인다", "s23에 보인다", "둘 다 보인다", "둘 다 안 보인다"]})
    body = ""
    for scene in params.FACE_WIDEN_SCENES:
        body += f"<h3>{NAME[scene]}</h3><div class=\"ab1\">" + fig(uri(img(f"approved-{scene}"), 900), "승인본") \
                + "".join(fig(uri(img(f"R1-g{G}-{scene}-s{seed}"), 900), f"R1 s{seed}", "a") for seed in params.FACE_WIDEN_SEEDS) + "</div>"
    sc.append({"id": "final", "q": "⑤ 조건부 R1이 새 장면·새 인물에서도 유지되는가?",
               "look": "조건부 R1 = klein 원본 얼굴을 사람이 먼저 거르고, 통과한 머리만 승인본에 붙인다. 앞의 답을 모두 생각해서 고르세요.",
               "body": body, "opts": ["유지된다", "장면·인물에 따라 다르다", "깨진다"]})
    return sc


def main(src, dst):
    html = open(src, encoding="utf-8").read()
    head = html[html.index("<title>"):html.index("<script>")].replace("<title>화풍 되찾기 판정</title>", "<title>R1 넓히기 판정</title>")
    tail = html[html.index("const PICKED"):html.rindex("</script>") + len("</script>")]
    tail = tail[tail.index("\n") + 1:]   # 347의 PICKED 줄을 버리고 아래에서 새로 쓴다
    tail = tail.replace("face-style-347", "face-widen-348").replace("task 347 사람 판정", "task 348 사람 판정")
    picked = f"골리앗 다윗 · 길갈 사울+사무엘 · klein s42·s23 · R1 확장 {G}"
    page = (head + "<script>\nconst SCREENS = " + json.dumps(screens(), ensure_ascii=False) + ";\n"
            + "const PICKED = " + json.dumps(picked, ensure_ascii=False) + ";\n" + tail + "\n")
    open(dst, "w", encoding="utf-8").write(page)
    print(dst, f"{len(page) / 1e6:.2f}MB")


if __name__ == "__main__":
    main(*sys.argv[1:3])
