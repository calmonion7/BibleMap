#!/usr/bin/env python3
"""task 353 S2 — 인물 정의 2/2 파일럿 판정 페이지(한 화면 한 질문, 폰용). 351 페이지 틀(CSS)을 그대로 쓴다.
  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV make_cast_v2_pilot_page.py <351 페이지 HTML> <출력 HTML> [--src ~/.local/biblemap-imggen/cast-v2-pilot]
정본 3문항(시드 8 × 정면·3/4 중 하나 / 없음) → 장면 ① 9문항(같은 시드 번호끼리 두 정차지, 카드 폭 356px, ▼ 대상 머리)
→ ② ①에서 「다른 사람 같다」면 바로 「무엇이 달라 보이나?」(여러 개). 장면 머리는 OWLv2(face_ab_heads)로 찾고, 못 찾으면 명세 구역 위.
답은 판정 문장으로 복사해 대화에 붙인다(351과 같음). 기계 거르기는 없다 — 그린 것 전부를 보인다."""
import argparse, json, os, sys

from PIL import Image, ImageDraw

import derive_scene as ds
import face_ab_heads
import gen_cast_v2_pilot as gp
import gen_face_canon as g
import params
from make_face_widen_page import uri

CARD, DPR = 356, 3      # 351 고정 절: 카드 폭 356 CSS px, 폰 DPR 3
NAME = {"saul": "사울", "david": "다윗", "samuel": "사무엘"}
SC = {"gilgal": "authored-saul-gilgal-coronation", "engedi": "authored-david-en-gedi-saul", "ramah": "authored-david-ramah-samuel"}
SC_NAME = {"gilgal": "길갈", "engedi": "엔게디", "ramah": "라마"}
PAIRS = {"saul": ("gilgal", "engedi"), "david": ("engedi", "ramah"), "samuel": ("gilgal", "ramah")}
SIDE = {"gilgal": {"samuel": (0, 0.5), "saul": (0.5, 1)}, "engedi": {"david": (0, 0.5), "saul": (0.5, 1)},
        "ramah": {"david": (0, 0.5), "samuel": (0.5, 1)}}
WHY = ["수염", "체격", "나이대", "얼굴", "옷", "기타"]
CIRC = "①②③④⑤⑥⑦⑧"


def head(sc, who, path):
    """→ (상자, 출처). OWLv2가 못 찾으면 명세 구역 위쪽 가운데를 쓴다."""
    face_ab_heads.SIDE[sc] = SIDE[sc]
    b = face_ab_heads.heads(sc, path).get(who)
    if b:
        return b, "owl"
    im = Image.open(path)
    r = ds.load(SC[sc])["regions"][who]
    x, y = (r[0] + r[2]) / 2 * im.width, r[1] * im.height
    return (x - 20, y, x + 20, y + 40), "region"


def card(path, box, cap, cls):
    im = Image.open(path).convert("RGB")
    k = CARD * DPR / im.width
    im = im.resize((CARD * DPR, round(im.height * k)), Image.LANCZOS)
    x, y, s = (box[0] + box[2]) / 2 * k, max(box[1] * k - 4 * DPR, 9 * DPR), 5 * DPR
    ImageDraw.Draw(im).polygon([(x - s, y - 1.6 * s), (x + s, y - 1.6 * s), (x, y)], fill="#e0601e", outline="white", width=DPR)
    return (f'<figure class="card {cls}"><img src="{uri(im)}" alt="{cap}" style="width:{CARD}px">'
            f"<figcaption>{cap}</figcaption></figure>")


def canon_screen(src, who):
    figs = []
    for n, s in enumerate(params.FACE_CANON_SEEDS):
        ims = "".join(f'<img src="{uri(Image.open(os.path.join(src, "face", who, f"s{s}-{v}.png")), 360)}" alt="{v}">' for v in g.VIEWS)
        figs.append(f'<figure class="pair">{ims}<figcaption>{CIRC[n]} 시드 {s}</figcaption></figure>')
    defn = f'<details><summary>정의 문구(프롬프트)</summary><p class="small">{g.look(who)}</p></details>'
    return {"id": f"c-{who}", "q": f"정본 {NAME[who]} · 이 정의에 맞는 정본은?",
            "look": f"시드마다 정면·3/4 측면 두 장입니다. {NAME[who]}의 정의(나이대·수염·머리·얼굴)에 가장 맞는 한 시드를 고르세요. 맞는 것이 없으면 「없음」.",
            "body": defn + '<div class="pairs">' + "".join(figs) + "</div>",
            "opts": [f"{CIRC[n]} s{s}" for n, s in enumerate(params.FACE_CANON_SEEDS)] + ["없음"], "cols": 3}


def screens(src):
    sc, log = [], []
    for who in ("saul", "david", "samuel"):
        sc.append(canon_screen(src, who))
    for who, (a, b) in PAIRS.items():
        for n, s in enumerate(params.SCENE_SEEDS, 1):
            body = ""
            for key, cls in ((a, "a"), (b, "b")):
                p = os.path.join(src, "scene", SC[key], f"s{s}.png")
                box, how = head(key, who, p)
                body += card(p, box, f"{SC_NAME[key]} · 시드 {s}", cls)
                log.append(f"{who} {key} s{s} 머리={how} {[round(v) for v in box]}")
            qid = f"s-{who}-{n}"
            sc.append({"id": qid, "q": f"{NAME[who]} {n}/3 · 두 그림의 ▼가 같은 사람으로 읽히나?",
                       "look": f"위는 {SC_NAME[a]}, 아래는 {SC_NAME[b]}입니다. 카드에 실제로 보이는 크기 그대로입니다(확대하지 마세요). "
                               f"▼ 표시된 {NAME[who]}만 보고 답하세요.", "body": body, "opts": ["읽힌다", "다른 사람 같다"]})
            sc.append({"id": qid + "-why", "when": [qid, "다른 사람 같다"], "q": f"{NAME[who]} {n}/3 · 무엇이 달라 보이나?",
                       "look": "해당하는 것을 모두 누르고 「고르기 끝」. (앞 화면과 같은 그림입니다)", "body": body, "multi": WHY})
    return sc, log


JS = r"""
const ans = {};
try { Object.assign(ans, JSON.parse(localStorage.getItem("cast-v2-353") || "{}")) } catch (e) {}
let i = 0;
const m = document.getElementById("m"), o = document.getElementById("o");
function save() { try { localStorage.setItem("cast-v2-353", JSON.stringify(ans)) } catch (e) {} }
const live = s => !s.when || ans[s.when[0]] === s.when[1];
function sentence() {
  return "task 353 사람 판정\n" + SCREENS.filter(live).map(s => `- ${s.q} → ${ans[s.id] || "(미답)"}`).join("\n") + `\n(보여 준 그림: ${PICKED})`;
}
function step(d) { i += d; while (i >= 0 && i < SCREENS.length && !live(SCREENS[i])) i += d; if (i < 0) i = 0; render() }
function render() { draw(); m.style.paddingBottom = (document.querySelector(".bar").offsetHeight + 16) + "px" }
function draw() {
  window.scrollTo(0, 0);
  const n = SCREENS.filter(live).length, k = SCREENS.slice(0, i).filter(live).length + 1;
  if (i >= SCREENS.length) {
    m.innerHTML = `<div class="top"><span>끝</span><span>${n}/${n}</span></div>
      <h1>판정 문장</h1><p class="look">복사해서 대화창에 붙여 주세요.</p><pre id="t"></pre>
      <button id="copy">판정 문장 복사</button><p class="small" id="msg"></p>`;
    document.getElementById("t").textContent = sentence();
    document.getElementById("copy").onclick = () => {
      navigator.clipboard.writeText(sentence()).then(() => { document.getElementById("msg").textContent = "복사했습니다." })
        .catch(() => { const r = document.createRange(); r.selectNodeContents(document.getElementById("t"));
          const s = getSelection(); s.removeAllRanges(); s.addRange(r); document.getElementById("msg").textContent = "선택해 두었습니다. 길게 눌러 복사하세요." });
    };
    o.innerHTML = ""; document.getElementById("next").disabled = true; return;
  }
  const s = SCREENS[i];
  document.getElementById("next").disabled = false;
  m.innerHTML = `<div class="top"><span>질문</span><span>${k}/${n}</span></div><h1>${s.q}</h1><p class="look">${s.look}</p>${s.body}`;
  o.innerHTML = ""; o.style.gridTemplateColumns = `repeat(${s.cols || 2}, 1fr)`;
  if (s.multi) {
    const sel = new Set(ans[s.id] ? ans[s.id].split(", ") : []);
    const done = document.createElement("button");
    const sync = () => { o.querySelectorAll("button[data-w]").forEach(b => b.setAttribute("aria-pressed", sel.has(b.dataset.w) ? "true" : "false"));
      done.textContent = `고르기 끝 (${sel.size})`; done.disabled = sel.size === 0 };
    s.multi.forEach(t => { const b = document.createElement("button"); b.textContent = t; b.dataset.w = t;
      b.onclick = () => { sel.has(t) ? sel.delete(t) : sel.add(t); sync() }; o.appendChild(b) });
    done.onclick = () => { ans[s.id] = s.multi.filter(t => sel.has(t)).join(", "); save(); step(1) };
    o.appendChild(done); sync(); return;
  }
  s.opts.forEach(t => {
    const b = document.createElement("button");
    b.textContent = t; b.setAttribute("aria-pressed", ans[s.id] === t ? "true" : "false");
    b.onclick = () => { ans[s.id] = t; save(); step(1) };
    o.appendChild(b);
  });
}
document.getElementById("back").onclick = () => step(-1);
document.getElementById("next").onclick = () => step(1);
render();
</script>
"""
CSS = """.pairs { display: grid; grid-template-columns: 1fr 1fr; gap: 10px }
figure.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 2px }
figure.pair img { border-width: 1px }
figure.pair figcaption { grid-column: 1 / -1; font-weight: 600; color: var(--fg) }
details { font-size: 14px } summary { cursor: pointer; color: var(--mu) }
.opts button { min-height: 44px }
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src_html")
    ap.add_argument("dst")
    ap.add_argument("--src", default=os.path.expanduser("~/.local/biblemap-imggen/cast-v2-pilot"))
    a = ap.parse_args()
    html = open(a.src_html, encoding="utf-8").read()
    head = html[html.index("<title>"):html.index("<script>")].replace("<title>카드 크기 얼굴 판정</title>", "<title>인물 정의 판정</title>")
    head = head.replace("</style>", CSS + "</style>")
    sc, log = screens(a.src)
    picked = (f"정본 {len(gp.WHO)}명 × 시드 {params.FACE_CANON_SEEDS} × 정면·3/4 · 장면 길갈·엔게디·라마 × 시드 {params.SCENE_SEEDS}"
              " · 카드 폭 356px · 얼굴 참조 없음(정의 문구만)")
    page = (head + "<script>\nconst SCREENS = " + json.dumps(sc, ensure_ascii=False) + ";\n"
            + "const PICKED = " + json.dumps(picked, ensure_ascii=False) + ";\n" + JS + "\n</body></html>\n")
    open(a.dst, "w", encoding="utf-8").write(page)
    print("\n".join(log))
    print(a.dst, f"{len(page) / 1e6:.2f}MB, 화면 {len(sc)}")


if __name__ == "__main__":
    main()
