#!/usr/bin/env python3
"""얼굴 각도 정본 시험 사람 판정 화면(notes/FACE-ANGLES.md 고정 절) — 한 화면 한 질문, 폰용.
  python3 make_face_angles_page.py   → ~/.local/biblemap-imggen/pages/face-angles.html
앞 4문항 = 각도 정본 승인(인물 × 각도), 뒤 32문항 = A·B 머리 크롭 블라인드 「정본과 같은 사람인가」(순서는 고정 시드로 섞음).
답은 「판정 문장 복사」 JSON 한 덩이 → samples/face-angles/verdict.txt."""
import base64, io, json, os, random

from PIL import Image

import params
from gen_face_angles import OUT, pick_path
from make_night_page import fit

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.expanduser("~/.local/biblemap-imggen/pages/face-angles.html")
NAME = {"saul": "사울", "david": "다윗"}
VIEW_KO = {"three-quarter": "3/4 측면", "profile": "옆얼굴"}


def uri(im, side=320):
    im = im.convert("RGB")
    im.thumbnail((side, side), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "JPEG", quality=86)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def head_crop(path, box):
    im = Image.open(path)
    W, H = im.size
    x, y, w, h = fit(box, 1, W, H, 0.5)
    return im.crop((round(x * W), round(y * H), round((x + w) * W), round((y + h) * H))).resize((320, 320), Image.LANCZOS)


def questions():
    canon = {w: uri(Image.open(os.path.join(HERE, "frozen", f"{w}.png"))) for w in params.FACE_ANGLE_PEOPLE}
    qs = []
    for w in params.FACE_ANGLE_PEOPLE:
        for v in params.FACE_ANGLE_VIEWS:
            p = pick_path(w) if v == "three-quarter" else os.path.join(OUT, "views", f"pick-{w}-profile.png")
            qs.append({"id": f"view:{w}:{v}", "q": f"오른쪽 그림이 왼쪽 {NAME[w]} 정본과 같은 사람인가요?",
                       "hint": f"{VIEW_KO[v]}으로 다시 그린 정본입니다. 얼굴·머리·수염·나이대만 봅니다(옷은 빼고).",
                       "refs": [canon[w]], "img": uri(Image.open(p))})
    m = json.load(open(os.path.join(HERE, "samples", params.FACE_ANGLE_SCENE_SET, "metrics.json")))
    boxes = {x["seed"]: x["boxes"] for x in m["scenes"][params.FACE_ANGLE_SCENE]["seeds"]}
    crops = []
    for seed in params.FACE_ANGLE_REDRAW_SEEDS:
        for arm in ("A", "B"):
            src = os.path.join(OUT, "redraw", f"{arm}-s{seed}.png")
            for w in params.FACE_ANGLE_PEOPLE:
                crops.append({"id": f"{arm}:{seed}:{w}", "q": f"가운데 머리가 {NAME[w]} 정본과 같은 사람인가요?",
                              "hint": "얼굴·머리·수염·나이대만 봅니다(옷은 빼고). 위 두 장이 정본(정면·3/4 측면)입니다.",
                              "refs": [canon[w], uri(Image.open(pick_path(w)))], "img": uri(head_crop(src, boxes[seed][w]["head"]))})
    random.Random(1022).shuffle(crops)
    return qs + crops


TEMPLATE = r"""<title>얼굴 각도 판정</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
/* 한 화면 한 질문: 위 정본 띠 → 가운데 판정 그림 → 아래 답 단추 */
:root { --bg: #f3f1ec; --panel: #fbfaf7; --fg: #23211d; --muted: #6b665c; --line: #d9d4c8; --accent: #3d5a73; --yes: #2f6b45; --no: #9a3b2e;
  --sans: "Noto Sans KR", system-ui, sans-serif; --mono: ui-monospace, Menlo, monospace }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg: #1b1a18; --panel: #24221f; --fg: #ebe7df; --muted: #a39d91; --line: #3a3732; --accent: #8fb0cc; --yes: #7cc196; --no: #e08b7c; color-scheme: dark } }
:root[data-theme="dark"] { --bg: #1b1a18; --panel: #24221f; --fg: #ebe7df; --muted: #a39d91; --line: #3a3732; --accent: #8fb0cc; --yes: #7cc196; --no: #e08b7c; color-scheme: dark }
body { background: var(--bg); color: var(--fg); font: 15px/1.5 var(--sans); padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)) }
main { max-width: 520px; margin: 0 auto; padding-block: 16px 32px; display: grid; gap: 14px }
.bar { display: flex; justify-content: space-between; color: var(--muted); font-size: 13px; font-variant-numeric: tabular-nums }
h2 { font-size: 18px; margin: 0; text-wrap: balance }
.hint { color: var(--muted); font-size: 13px; margin: 0 }
.refs { display: flex; gap: 8px }
.refs figure { margin: 0; flex: 1; min-width: 0 }
.refs img, .main img { width: 100%; border-radius: 6px; border: 1px solid var(--line); display: block }
figcaption { font-size: 12px; color: var(--muted); text-align: center }
.main { max-width: 320px; width: 100%; margin: 0 auto }
.btns { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px }
button { font: inherit; padding: 12px 8px; border-radius: 8px; border: 1px solid var(--line); background: var(--panel); color: var(--fg); cursor: pointer }
button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px }
button.yes { border-color: var(--yes); color: var(--yes) } button.no { border-color: var(--no); color: var(--no) }
button.on { background: var(--accent); color: var(--bg); border-color: var(--accent) }
.nav { display: flex; justify-content: space-between }
textarea { width: 100%; min-height: 140px; font: 12px/1.4 var(--mono); color: var(--fg); background: var(--panel); border: 1px solid var(--line); border-radius: 6px; box-sizing: border-box }
</style>
<main id="app"></main>
<script>
const QS = __QS__;
const ans = {};
let i = 0;
const app = document.getElementById("app");
function el(h) { const d = document.createElement("div"); d.innerHTML = h; return d; }
function render() {
  app.innerHTML = "";
  if (i >= QS.length) return done();
  const q = QS[i];
  const cap = q.refs.length > 1 ? ["정본 정면", "정본 3/4 측면"] : ["정본"];
  app.append(el(`<div class="bar"><span>${i + 1} / ${QS.length}</span><span>${q.id.startsWith("view") ? "각도 정본 승인" : "다시 그린 머리"}</span></div>
    <h2>${q.q}</h2><p class="hint">${q.hint}</p>
    <div class="refs">${q.refs.map((r, k) => `<figure><img src="${r}" alt="${cap[k]}"><figcaption>${cap[k]}</figcaption></figure>`).join("")}
    ${q.id.startsWith("view") ? `<figure><img src="${q.img}" alt="다시 그린 정본"><figcaption>다시 그린 정본</figcaption></figure>` : ""}</div>
    ${q.id.startsWith("view") ? "" : `<div class="main"><img src="${q.img}" alt="판정할 머리"></div>`}
    <div class="btns"><button class="yes" id="y" type="button">같은 사람</button><button class="no" id="n" type="button">다른 사람</button><button id="u" type="button">모르겠음</button></div>
    <div class="nav"><button id="back" type="button" ${i ? "" : "disabled"}>이전</button><button id="end" type="button">끝으로</button></div>`));
  const pick = a => { ans[q.id] = a; i++; render(); };
  document.getElementById("y").onclick = () => pick("yes");
  document.getElementById("n").onclick = () => pick("no");
  document.getElementById("u").onclick = () => pick("unsure");
  document.getElementById("back").onclick = () => { i--; render(); };
  document.getElementById("end").onclick = () => { i = QS.length; render(); };
  const cur = ans[q.id]; if (cur) document.getElementById({yes: "y", no: "n", unsure: "u"}[cur]).classList.add("on");
}
function done() {
  const n = Object.keys(ans).length;
  app.append(el(`<h2>판정 문장을 복사해 대화에 붙여 주세요</h2><p class="hint">${n} / ${QS.length}문항 답함</p>
    <div class="nav"><button id="back" type="button">이전 문항</button><button id="copy" type="button">판정 문장 복사</button></div>
    <span class="hint" id="ok"></span><textarea id="out" readonly></textarea>`));
  const ta = document.getElementById("out");
  ta.value = "판정 face-angles\n" + JSON.stringify(ans);
  document.getElementById("back").onclick = () => { i = QS.length - 1; render(); };
  document.getElementById("copy").onclick = () => navigator.clipboard.writeText(ta.value)
    .then(() => { document.getElementById("ok").textContent = "복사됨"; })
    .catch(() => { ta.focus(); ta.select(); document.getElementById("ok").textContent = "자동 복사가 막혀 글을 선택해 두었습니다. 직접 복사하세요."; });
}
render();
</script>
"""


if __name__ == "__main__":
    os.makedirs(os.path.dirname(PAGE), exist_ok=True)
    qs = questions()
    open(PAGE, "w", encoding="utf-8").write(TEMPLATE.replace("__QS__", json.dumps(qs, ensure_ascii=False)))
    print(PAGE, len(qs), "문항", round(os.path.getsize(PAGE) / 1e6, 2), "MB")
