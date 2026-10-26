#!/usr/bin/env python3
"""task#349 S3 — 사람 판정 페이지(한 화면 한 질문). CSS 틀은 348 판정 페이지를 그대로 쓰고, 여러 개 고르기(그림을 눌러 고른다)를 더했다.
  python3 make_face_hitrate_page.py <348 페이지 HTML> <출력 HTML>
머리 상자는 samples/face-hitrate/metrics.json에서 읽는다. 기계 결과(화질 자)는 페이지에 넣지 않는다 — 사람 답을 이끌지 않게.
(가) 적중 8화면: 머리×조건마다 정본 + klein 크롭 8장 → 같은 사람을 모두 고른다 · (나) 화질 8화면: 승인본 대 R1 원본 화소 · (다) 최종 1화면."""
import json, os, sys

from PIL import Image

import params
from gen_face_hitrate import OUT
from make_face_widen_page import crop, fig, uri

NAME = {"david": "다윗", "saul": "사울", "samuel": "사무엘", "gilgal": "길갈", "engedi": "엔게디"}
COND_LABEL = {"K1": "참조 1명", "K2": "참조 2명"}
NONE = "없음"


def img(name):
    return Image.open(os.path.join(OUT, name)).convert("RGB")


def screens():
    met = json.load(open(os.path.join(OUT, "metrics.json")))
    canon = {w: uri(Image.open(os.path.join(params.FROZEN, f"{w}.png")), 360) for w in ("david", "saul", "samuel")}
    sc = []
    for scene, whos in params.FACE_HITRATE_SCENES.items():
        for who in whos:
            for cond in params.FACE_HITRATE_CONDS:
                body, picks = '<div class="ref1">' + fig(canon[who], "정본(기준)") + '</div><div class="grid">', []
                for h in met["klein"]:
                    if (h["scene"], h["who"], h["cond"]) != (scene, who, cond):
                        continue
                    im, tag = img(h["file"]), f"s{h['seed']}"
                    face = crop(im, h["box"], 1.6) if h["box"] else im   # 머리를 못 찾으면 그림 전체
                    body += f'<figure class="pick" data-pick="{tag}"><img src="{uri(face, 300)}" alt="{tag}"><figcaption>{tag}</figcaption></figure>'
                    picks.append(tag)
                tag = f"{NAME[scene]} {NAME[who]} · {COND_LABEL[cond]}"
                look = ("klein이 이 인물 정본 하나만 보고 이 얼굴만 다시 그렸습니다." if cond == "K1"
                        else "klein이 두 인물 정본을 다 보고 두 얼굴을 함께 다시 그렸습니다.")
                sc.append({"id": f"a-{scene}-{who}-{cond}", "q": f"(가) {tag} · 정본과 같은 사람을 모두 고르세요",
                           "look": look + " 얼굴 구조(눈·코·입 비율, 수염·머리 모양, 나이대)만 보세요. 화풍 차이는 무시합니다. 그림을 눌러 고르고 「고르기 끝」을 누르세요.",
                           "body": body + "</div>", "multi": picks})
    for scene, whos in params.FACE_HITRATE_SCENES.items():
        for seed in params.FACE_HITRATE_R1_SEEDS:
            for who in whos:
                r = next(h for h in met["r1"] if (h["scene"], h["who"], h["seed"]) == (scene, who, seed))
                ap = met["approved"][f"{scene}-{who}"]["box"]
                a = fig(uri(crop(img(f"approved-{scene}.png"), ap, 1.6)), "승인본 머리", native=True)
                b = (fig(uri(crop(img(r["file"]), r["box"], 1.6)), "R1 머리", "a", native=True) if r["box"]
                     else fig(uri(img(r["file"]), 900), "R1 그림 전체(머리 못 찾음)", "a"))
                sc.append({"id": f"b-{scene}-s{seed}-{who}", "q": f"(나) {NAME[scene]} s{seed} {NAME[who]} · R1 머리의 결이 승인본과 어울리는가?",
                           "look": "얼굴이 누구인지는 보지 마세요. 선·명암의 결만 봅니다. R1 머리가 주변 그림보다 거칠거나 지글거리면 「거칠다」. 두 그림 모두 확대하지 않은 원본 화소입니다.",
                           "body": '<div class="ab1">' + a + b + "</div>", "opts": ["어울린다", "거칠다"]})
    body = "".join(f"<h3>{NAME[s]} 승인본</h3>" + fig(uri(img(f"approved-{s}.png"), 900), "승인본") for s in params.FACE_HITRATE_SCENES)
    sc.append({"id": "final", "q": "(다) 「장면·인물마다 klein 여러 장 → 사람이 거름」을 생산 방식으로 계속할 만한가?",
               "look": "앞의 (가)에서 같은 사람이 몇 장에 한 번꼴로 나왔는지, (나)에서 결이 어땠는지를 생각해서 고르세요. 계속한다면 장면·인물마다 이 페이지 같은 거르기를 사람이 하게 됩니다.",
               "body": body, "opts": ["계속", "다른 길 찾기"]})
    return sc


CSS = """.grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px }
@media (max-width: 520px) { .grid { grid-template-columns: repeat(2, 1fr) } }
figure.pick { cursor: pointer }
figure.pick[aria-pressed="true"] img { border-color: var(--pick); outline: 3px solid var(--r1); outline-offset: -3px }
figure.pick[aria-pressed="true"] figcaption { color: var(--r1); font-weight: 600 }
figure.pick[aria-pressed="true"] figcaption::after { content: " ✓ 같은 사람" }
"""

JS = r"""const ans = {};
try { Object.assign(ans, JSON.parse(localStorage.getItem("face-hitrate-349") || "{}")) } catch (e) {}
let i = 0;
const m = document.getElementById("m"), o = document.getElementById("o");
function save() { try { localStorage.setItem("face-hitrate-349", JSON.stringify(ans)) } catch (e) {} }
function sentence() {
  return "task 349 사람 판정\n" + SCREENS.map(s => `- ${s.q} → ${ans[s.id] || "(미답)"}`).join("\n") + `\n(보여 준 그림: ${PICKED})`;
}
function render() {
  window.scrollTo(0, 0);
  if (i >= SCREENS.length) {
    m.innerHTML = `<div class="top"><span>끝</span><span>${SCREENS.length}/${SCREENS.length}</span></div>
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
  m.innerHTML = `<div class="top"><span>${s.id === "final" ? "마지막" : "질문"}</span><span>${i + 1}/${SCREENS.length}</span></div>
    <h1>${s.q}</h1><p class="look">${s.look}</p>${s.body}`;
  o.innerHTML = "";
  if (s.multi) {
    const sel = new Set((ans[s.id] && ans[s.id] !== "없음") ? ans[s.id].split(", ") : []);
    const done = document.createElement("button"), none = document.createElement("button");
    const sync = () => {
      m.querySelectorAll("figure.pick").forEach(f => f.setAttribute("aria-pressed", sel.has(f.dataset.pick) ? "true" : "false"));
      done.textContent = `고르기 끝 (${sel.size}장)`; done.disabled = sel.size === 0;
      none.setAttribute("aria-pressed", ans[s.id] === "없음" ? "true" : "false");
    };
    m.querySelectorAll("figure.pick").forEach(f => {
      f.setAttribute("role", "button"); f.tabIndex = 0;
      const t = () => { sel.has(f.dataset.pick) ? sel.delete(f.dataset.pick) : sel.add(f.dataset.pick); sync() };
      f.onclick = t; f.onkeydown = e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); t() } };
    });
    none.textContent = "없음 (한 장도 아니다)";
    none.onclick = () => { ans[s.id] = "없음"; save(); i++; render() };
    done.onclick = () => { ans[s.id] = s.multi.filter(p => sel.has(p)).join(", "); save(); i++; render() };
    o.append(none, done); sync(); return;
  }
  s.opts.forEach(t => {
    const b = document.createElement("button");
    b.textContent = t; b.setAttribute("aria-pressed", ans[s.id] === t ? "true" : "false");
    b.onclick = () => { ans[s.id] = t; save(); i++; render() };
    o.appendChild(b);
  });
}
document.getElementById("back").onclick = () => { if (i > 0) { i--; render() } };
document.getElementById("next").onclick = () => { i++; render() };
render();
</script>"""


def main(src, dst):
    html = open(src, encoding="utf-8").read()
    head = html[html.index("<title>"):html.index("<script>")].replace("<title>R1 넓히기 판정</title>", "<title>klein 적중률 판정</title>")
    head = head.replace("</style>", CSS + "</style>")
    picked = "길갈 사울·사무엘 · 엔게디 다윗·사울 · klein 참조 1명/2명 × 시드 8 · 화질 표본 R1(확장 1.6) s42·s23"
    page = (head + "<script>\nconst SCREENS = " + json.dumps(screens(), ensure_ascii=False) + ";\n"
            + "const PICKED = " + json.dumps(picked, ensure_ascii=False) + ";\n" + JS + "\n")
    open(dst, "w", encoding="utf-8").write(page)
    print(dst, f"{len(page) / 1e6:.2f}MB")


if __name__ == "__main__":
    main(*sys.argv[1:3])
