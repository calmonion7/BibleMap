#!/usr/bin/env python3
"""task 356 S2 — LoRA 학습 시트 사람 거르기 페이지(인물마다 한 화면 한 문항, 폰용). 353 페이지 틀(CSS)을 그대로 쓴다.
  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV make_lora_sheet_page.py <353 페이지 HTML> <출력 HTML>
화면 = 기준 그림(정본 s11 정면) + 초상 6 + 전신 16. 「같은 사람으로 안 보이거나 정의와 안 맞는 그림」을 눌러 표시한다(없으면 그대로).
답은 판정 문장으로 복사해 대화에 붙인다. 문장의 파일 키(face-s11-front·stand-s42 …)를 gen_lora_sheet.py write --drop이 읽는다."""
import argparse, json, os

from PIL import Image

import gen_face_canon as g
import gen_lora_sheet as L
import params
from make_face_widen_page import uri

NAME = {"saul": "사울", "david": "다윗", "samuel": "사무엘"}
POSE = {"stand": "서기", "walk": "걷기"}
VIEW = {"front": "정면", "34": "3/4"}


def label(key):
    if key.startswith("face-"):
        _, s, v = key.split("-")
        return f"초상 {s} {VIEW[v]}"
    pose, s = key.split("-")
    return f"전신 {POSE[pose]} {s}"


def screen(who):
    ref = Image.open(os.path.join(L.FACE, who, "s11-front.png"))
    figs = "".join(f'<figure class="pick" data-k="{k}"><img src="{uri(Image.open(p), 300)}" alt="{label(k)}">'
                   f"<figcaption>{label(k)}</figcaption></figure>"
                   for k, p, _ in L.portrait_items(who) + L.body_items(who))
    defn = f'<details><summary>정의 문구(전신 프롬프트)</summary><p class="small">{L.body_prompt(who, "stand")}</p></details>'
    body = (f'<figure class="canon"><img src="{uri(ref, 360)}" alt="기준" style="width:180px"><figcaption>기준 — 정본 s11 정면</figcaption></figure>'
            + defn + f'<div class="grid">{figs}</div>')
    return {"id": who, "q": f"{NAME[who]} · 빼야 할 그림을 누르세요",
            "look": f"맨 위 기준 그림과 <b>같은 사람으로 안 보이거나</b>, 정의(나이대·수염·머리·체격·옷)와 <b>안 맞는</b> 그림을 모두 누르세요. "
                    "여러 사람·잘린 몸·대머리도 뺍니다. 다 괜찮으면 아무것도 누르지 말고 「표시 끝」.",
            "body": body}


JS = r"""
const ans = {};
try { Object.assign(ans, JSON.parse(localStorage.getItem("lora-sheet-356") || "{}")) } catch (e) {}
let i = 0;
const m = document.getElementById("m"), o = document.getElementById("o");
function save() { try { localStorage.setItem("lora-sheet-356", JSON.stringify(ans)) } catch (e) {} }
function sentence() {
  return "task 356 사람 판정\n" + SCREENS.map(s => `- ${s.q} → ${ans[s.id] === undefined ? "(미답)" : (ans[s.id].length ? "뺌: " + ans[s.id].join(", ") : "모두 맞음")}`).join("\n") + `\n(보여 준 그림: ${PICKED})`;
}
function step(d) { i = Math.max(0, Math.min(SCREENS.length, i + d)); render() }
function render() { draw(); m.style.paddingBottom = (document.querySelector(".bar").offsetHeight + 16) + "px" }
function draw() {
  window.scrollTo(0, 0);
  const n = SCREENS.length;
  if (i >= n) {
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
  m.innerHTML = `<div class="top"><span>질문</span><span>${i + 1}/${n}</span></div><h1>${s.q}</h1><p class="look">${s.look}</p>${s.body}`;
  const sel = new Set(ans[s.id] || []);
  const done = document.createElement("button");
  const sync = () => { m.querySelectorAll("figure.pick").forEach(f => f.setAttribute("aria-pressed", sel.has(f.dataset.k) ? "true" : "false"));
    done.textContent = sel.size ? `표시 끝 (뺌 ${sel.size})` : "표시 끝 (모두 맞음)" };
  m.querySelectorAll("figure.pick").forEach(f => { f.onclick = () => { const k = f.dataset.k; sel.has(k) ? sel.delete(k) : sel.add(k); sync() } });
  o.innerHTML = ""; o.style.gridTemplateColumns = "1fr";
  done.onclick = () => { ans[s.id] = [...m.querySelectorAll("figure.pick")].map(f => f.dataset.k).filter(k => sel.has(k)); save(); step(1) };
  o.appendChild(done); sync();
}
document.getElementById("back").onclick = () => step(-1);
document.getElementById("next").onclick = () => step(1);
render();
</script>
"""
CSS = """figure.pick[aria-pressed="true"] img { opacity: .45 }
figure.pick[aria-pressed="true"] figcaption::after { content: " ✗ 뺌" }
details { font-size: 14px } summary { cursor: pointer; color: var(--mu) }
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src_html")
    ap.add_argument("dst")
    a = ap.parse_args()
    html = open(a.src_html, encoding="utf-8").read()
    head = html[html.index("<title>"):html.index("<script>")].replace("<title>인물 정의 판정</title>", "<title>LoRA 시트 거르기</title>")
    head = head.replace("</style>", CSS + "</style>")
    sc = [screen(w) for w in params.LORA_SHEET_WHO]
    picked = (f"인물마다 353 정본 초상 시드 {params.LORA_SHEET_PORTRAIT_SEEDS} × 정면·3/4 + 전신 자세 {list(params.LORA_SHEET_POSES)}"
              f" × 시드 {params.LORA_SHEET_BODY_SEEDS} — 거르지 않고 전부")
    page = (head + "<script>\nconst SCREENS = " + json.dumps(sc, ensure_ascii=False) + ";\n"
            + "const PICKED = " + json.dumps(picked, ensure_ascii=False) + ";\n" + JS + "\n</body></html>\n")
    open(a.dst, "w", encoding="utf-8").write(page)
    print(a.dst, f"{len(page) / 1e6:.2f}MB, 화면 {len(sc)}")


if __name__ == "__main__":
    main()
