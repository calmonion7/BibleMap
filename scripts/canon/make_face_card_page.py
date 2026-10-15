#!/usr/bin/env python3
"""task#351 S1 — 카드 크기 얼굴 구별 판정 페이지(한 화면 한 질문). CSS 틀은 349 판정 페이지를 그대로 쓴다.
  VENV=~/.local/biblemap-imggen/.venv314/bin/python; $VENV make_face_card_page.py <349 페이지 HTML> <출력 HTML>
정본 머리는 OWLv2(face_ab_heads)로 찾으므로 venv 파이썬으로 돈다. 장면 머리 상자는 samples/face-hitrate/metrics.json.
장면 그림은 카드 폭(356 CSS px, notes/FACE-CARD.md 고정 절)으로, 정본은 카드에서의 머리 폭으로 줄여 보여 준다. 크롭은 없다.
(가) 구별 6화면 · (나) 장면 사이 1화면 · (다) 최종 1화면. 적중 위치는 페이지에 보이지 않는다."""
import json, os, random, sys

from PIL import Image, ImageDraw

import face_ab_heads
from gen_face_hitrate import OUT
from make_face_hitrate_page import NAME, COND
from make_face_widen_page import FROZEN, uri

CARD = 356          # CSS px — dev 투어 카드 장면 폭(390 뷰포트 실측)
DPR = 3             # 폰 화소 배율 — 실제 카드가 받는 화소만큼만 넣는다
# (머리, 인물, 조건, 적중 시드, 빗나감 시드) — 349 적중 6개와 시드가 가장 가까운 빗나감(같으면 작은 시드)
PAIRS = [("gilgal", "samuel", "K1", 101, 42), ("engedi", "david", "K1", 42, 23), ("engedi", "david", "K2", 42, 23),
         ("engedi", "saul", "K1", 42, 23), ("engedi", "saul", "K1", 202, 101), ("engedi", "saul", "K2", 303, 202)]
OPTS = ["A", "B", "구별 안 됨"]


def fname(scene, who, cond, seed):
    return f"K1-{scene}-{who}-s{seed}.png" if cond == "K1" else f"K2-{scene}-s{seed}.png"


def marked(im, box):
    """카드 화소(CARD*DPR)로 줄이고 대상 머리 위에 ▼를 그린다(얼굴은 가리지 않는다)."""
    k = CARD * DPR / im.width
    im = im.resize((CARD * DPR, round(im.height * k)), Image.LANCZOS)
    x, y, s = (box[0] + box[2]) / 2 * k, box[1] * k - 4 * DPR, 5 * DPR
    ImageDraw.Draw(im).polygon([(x - s, y - 1.6 * s), (x + s, y - 1.6 * s), (x, y)], fill="#e0601e", outline="white", width=DPR)
    return im


def card(im, cap, cls):
    return (f'<figure class="card {cls}"><img src="{uri(im)}" alt="{cap}" style="width:{CARD}px">'
            f"<figcaption>{cap}</figcaption></figure>")


def canon_fig(who, head_css):
    """정본 전체를 그 머리 폭이 head_css(CSS px)가 되도록 줄인다."""
    path = os.path.join(FROZEN, f"{who}.png")
    face_ab_heads.SIDE["canon"] = {who: (0, 1)}
    x0, _, x1, _ = face_ab_heads.heads("canon", path)[who]
    im = Image.open(path).convert("RGB")
    w = max(1, round(im.width * head_css / (x1 - x0)))
    return (f'<figure class="canon"><img src="{uri(im, w * DPR)}" alt="정본" style="width:{w}px">'
            f"<figcaption>정본(카드에서의 머리 크기)</figcaption></figure>"), w


def screens():
    met = json.load(open(os.path.join(OUT, "metrics.json")))
    box = {(h["file"], h["who"]): h["box"] for h in met["klein"]}
    # 위아래는 notes 고정 절과 같은 순서로 뽑는다(짝마다 random() 한 번, <0.5면 적중이 위 A)
    order = random.Random(351)
    sc, log = [], []
    for n, (scene, who, cond, hit, miss) in enumerate(PAIRS, 1):
        hit_low = order.random() >= 0.5
        top, low = (miss, hit) if hit_low else (hit, miss)
        f = {s: fname(scene, who, cond, s) for s in (top, low)}
        ims = {s: marked(Image.open(os.path.join(OUT, f[s])).convert("RGB"), box[(f[s], who)]) for s in (top, low)}
        head_css = sum((box[(f[s], who)][2] - box[(f[s], who)][0]) * CARD / 1216 for s in (top, low)) / 2
        cfig, cw = canon_fig(who, head_css)
        body = cfig + card(ims[top], "A", "a") + card(ims[low], "B", "b")
        sc.append({"id": f"a{n}", "q": f"(가) {n}/6 {NAME[scene]} {NAME[who]} · 정본과 같은 사람은?",
                   "look": f"▼ 표시된 {NAME[who]}의 얼굴만 보세요. 카드에 실제로 보이는 크기 그대로입니다(확대하지 마세요). "
                           "얼굴 생김새(수염·머리 모양·나이대·얼굴 윤곽)가 정본과 더 닮은 쪽을 고르고, 차이를 모르겠으면 「구별 안 됨」.",
                   "body": body, "opts": OPTS})
        log.append(f"{n} {f[top]}(A) {f[low]}(B) 적중={'B' if hit_low else 'A'} 정본폭={cw}px 머리={head_css:.1f}px")
    ap = {s: met["approved"][f"{s}-saul"]["box"] for s in ("gilgal", "engedi")}
    body = "".join(card(marked(Image.open(os.path.join(OUT, f"approved-{s}.png")).convert("RGB"), ap[s]), f"{NAME[s]} 승인본", c)
                   for s, c in (("gilgal", "a"), ("engedi", "b")))
    sc.append({"id": "b", "q": "(나) 두 장면의 ▼ 사울이 같은 사울로 읽히나?",
               "look": "두 정차지 카드에 나오는 사울입니다(어휘 정본 — 머리·수염·옷 색 — 만 맞춘 그림). 카드 크기 그대로 보고 답하세요.",
               "body": body, "opts": ["읽힌다", "다른 사람 같다"]})
    sc.append({"id": "final", "q": "(다) 카드 영상에서 장면마다 얼굴이 조금씩 다른 것이 문제 되나?",
               "look": "최종 산출물은 투어 카드의 짧은 영상입니다. 한 장면 안에서는 얼굴이 유지되고, 정차지가 바뀔 때 얼굴이 조금씩 다를 수 있습니다. "
                       "앞에서 본 카드 크기를 떠올려 답하세요. 「문제 된다」면 얼굴을 고르는 단계(기계 판정자)를 만듭니다.",
               "body": "", "opts": ["문제 된다", "안 된다"]})
    return sc, log


CSS = """figure.card img { max-width: none; border: 0; border-radius: 0; outline: 3px solid var(--line); touch-action: pan-y; -webkit-user-select: none; user-select: none }
figure.card.a img { outline-color: var(--r1) } figure.card.b img { outline-color: var(--r2) }
figure.canon img { max-width: none; border: 0; border-radius: 0; outline: 1px solid var(--line) }
html, body { touch-action: pan-y }
"""


def main(src, dst):
    html = open(src, encoding="utf-8").read()
    head = html[html.index("<title>"):html.index("<script>")].replace("<title>klein 적중률 판정</title>", "<title>카드 크기 얼굴 판정</title>")
    head = head.replace("</style>", CSS + "</style>")
    js = html[html.index("const ans = {};"):html.rindex("</script>") + len("</script>")]
    js = js.replace("face-hitrate-349", "face-card-351").replace("task 349 사람 판정", "task 351 사람 판정")
    sc, log = screens()
    picked = "카드 폭 356px · 349 적중/빗나감 6짝(길갈 사무엘·엔게디 다윗·사울) · 345 승인본 길갈·엔게디 사울"
    page = (head + "<script>\nconst SCREENS = " + json.dumps(sc, ensure_ascii=False) + ";\n"
            + "const PICKED = " + json.dumps(picked, ensure_ascii=False) + ";\n" + js + "\n")
    open(dst, "w", encoding="utf-8").write(page)
    print("\n".join(log))
    print(dst, f"{len(page) / 1e6:.2f}MB")


if __name__ == "__main__":
    main(*sys.argv[1:3])
