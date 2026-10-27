#!/usr/bin/env python3
"""규칙 spec.cast-canon-face 수리 — 인물마다 카드 파생 정본 얼굴 후보를 고르는 사람 판정 화면(2026-10-27).

  python3 batch/make_canon_face_page.py <out.html> [--dir ~/.local/biblemap-imggen/face-canon-v3] [--who id ...]

인물 한 사람 = 한 질문. 후보는 gen_face_canon.py(정면·3/4)와 judge_face_canon.py(judge-<id>.json) 산출을 읽는다.
답은 「판정 task canon-faces」 + JSON 한 줄({"<id>": "s7" | "keep" | "none"}, 메모는 "_memo")로 대화에 붙인다.
"""
import argparse, base64, glob, io, json, os, sys

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import derive_scene as ds


def uri(path, size):
    im = Image.open(path).convert("RGB")
    im.thumbnail((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=78)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def person(cid, d):
    j = json.load(open(os.path.join(d, f"judge-{cid}.json"), encoding="utf-8"))
    pick = ((j.get("pair") or {}).get(cid) or {}).get("pick", "")
    cands = []   # 기계 1위가 3/4여도 같은 시드 정면을 1위로 — 정본은 정면
    for p in sorted(glob.glob(os.path.join(d, cid, "s*-front.png"))):
        s = os.path.basename(p).split("-")[0]
        r = j["cands"].get(p) or {}
        cands.append({"seed": s, "score": r.get("score"), "vocab": r.get("vocab"), "reason": r.get("reason", "판정 없음"),
                      "top": bool(pick) and pick.split("-")[0] == s, "front": uri(p, 400), "side": uri(p.replace("-front", "-34"), 400)})
    cands.sort(key=lambda c: (not c["top"], -(c["score"] or 0)))
    c = ds.load_cast(cid)
    card = c["card"]
    old = os.path.join(HERE, "frozen", f"{cid}.png")
    cf = c.get("canon_face") or {}
    old_tag = f"task {cf['task']}" if cf.get("task") else "2026-09-04"
    return {"old_tag": old_tag, "id": cid, "name": c["names"][0], "age": card["ageBand"]["text"], "head": card["headOutline"]["text"],
            "beard": card["beardVolume"]["text"], "dress": card["costumeColor"]["text"],
            "old": uri(old, 300) if os.path.exists(old) else None, "cands": cands}


PAGE = r"""<title>인물 정본 얼굴</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gowun+Batang:wght@400;700&family=IBM+Plex+Sans+KR:wght@400;600&display=swap">
<style>
/* 판정 틀(inset_judge_page)과 같은 토큰 · 인물 한 사람 = 한 질문 묶음, 위에서 아래로 */
:root {
  --bg: #e9ecee; --panel: #f7f8f9; --ink: #1f2a30; --muted: #5b6870; --line: #c9d0d4;
  --accent: #2f5d50; --accent-ink: #ffffff; --ok: #2f6b3a; --bad: #9a3b2c;
  --serif: "Gowun Batang", "Noto Serif KR", "AppleMyungjo", serif;
  --sans: "IBM Plex Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", system-ui, sans-serif;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #161b1e; --panel: #20272b; --ink: #e4e9ec; --muted: #9aa7ae; --line: #36414a;
  --accent: #7fb8a6; --accent-ink: #10201b; --ok: #8fcf98; --bad: #f0a091; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #161b1e; --panel: #20272b; --ink: #e4e9ec; --muted: #9aa7ae; --line: #36414a;
  --accent: #7fb8a6; --accent-ink: #10201b; --ok: #8fcf98; --bad: #f0a091; color-scheme: dark }
body { background: var(--bg); color: var(--ink); font-family: var(--sans); line-height: 1.55; }
main { max-width: 1080px; margin: 0 auto; padding-block: 20px 48px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: grid; gap: 28px; }
h1 { font-family: var(--serif); font-size: 1.6rem; margin: 0; text-wrap: balance; }
h2 { font-family: var(--serif); font-size: 1.25rem; margin: 0; text-wrap: balance; }
.lede { color: var(--muted); margin: 4px 0 0; max-width: 65ch; }
.who { display: grid; gap: 12px; border-top: 1px solid var(--line); padding-top: 20px; }
.card-def { font-size: .88rem; color: var(--muted); margin: 0; max-width: 65ch; }
.row { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 150px), 1fr)); gap: 12px; }
.c { background: var(--panel); border: 2px solid var(--line); border-radius: 10px; padding: 8px; display: grid; gap: 6px; min-width: 0; }
.c.sel { border-color: var(--accent); }
.c img { width: 100%; height: auto; display: block; border-radius: 4px; cursor: zoom-in; }
.meta { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; justify-content: space-between; }
.chip { font-size: .78rem; padding: 1px 8px; border-radius: 999px; border: 1px solid currentColor; font-variant-numeric: tabular-nums; }
.chip.ok { color: var(--ok); } .chip.bad { color: var(--bad); }
.why { font-size: .8rem; color: var(--muted); margin: 0; }
.pick { display: flex; gap: 8px; align-items: center; font-weight: 600; cursor: pointer; }
.pick input { width: 20px; height: 20px; accent-color: var(--accent); }
.alt { display: flex; flex-wrap: wrap; gap: 16px; }
button { font: inherit; cursor: pointer; border-radius: 8px; }
button.sub { background: none; border: 1px solid var(--line); color: var(--ink); padding: 4px 10px; font-size: .85rem; }
button.main { justify-self: start; background: var(--accent); color: var(--accent-ink); border: 0; padding: 12px 18px; font-weight: 600; }
textarea { width: 100%; box-sizing: border-box; min-height: 80px; font: inherit; color: var(--ink); background: var(--panel);
  border: 1px solid var(--line); border-radius: 8px; padding: 10px; }
.send { display: grid; gap: 10px; }
.send pre { white-space: pre-wrap; word-break: break-all; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 10px; margin: 0; font-size: .85rem; }
:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
.zoom { position: fixed; inset: 0; background: var(--bg); z-index: 20; display: grid; grid-template-rows: auto 1fr;
  padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
.zoom[hidden] { display: none; }
.zoom .bar { display: flex; gap: 8px; align-items: center; border-bottom: 1px solid var(--line);
  padding: 10px max(16px, env(safe-area-inset-right, 0px)) 10px max(16px, env(safe-area-inset-left, 0px)); }
.zoom .bar span { margin-right: auto; font-weight: 600; }
.zoom .view { overflow: auto; display: grid; place-items: center; }
.zoom .view img { max-width: min(100%, 640px); }
</style>
<main>
  <header>
    <h1>인물 정본 얼굴 고르기</h1>
    <p class="lede">장면 그림이 기준으로 삼을 인물 얼굴입니다. 지금 정본은 대부분 인물 카드 정의를 쓰기 전(2026-09-04)에 고른 그림이라 카드와 어긋날 수 있습니다. 새 후보는 카드 정의(나이·머리·수염·옷·얼굴)로 사람마다 4장씩 그렸고, 기계가 카드와 맞는 정도를 채점했습니다. 얼굴 생김새는 성경에 없어 [저작]입니다.</p>
  </header>
  <p class="lede" style="margin:0">사람마다 한 장을 고르세요. 후보끼리 차이가 거의 없으면 아래 단추로 전부 기계 추천(점수 상위 3장 중 다른 인물과 가장 구별되는 장)을 고른 뒤, 틀린 사람만 바꾸면 됩니다. 그림을 누르면 크게 보고, 「3/4」로 옆얼굴을 봅니다.</p>
  <button type="button" class="main" id="alltop">전부 기계 추천으로</button>
  <div id="people" style="display:grid;gap:28px"></div>
  <label for="memo">메모 (무엇이 이상한지)</label>
  <textarea id="memo" placeholder="예: 요압이 너무 젊어 보임"></textarea>
  <section class="send">
    <button type="button" class="main" id="copy">답 복사</button>
    <pre id="out" aria-live="polite"></pre>
    <p class="lede">복사한 글을 대화창에 붙여 넣어 주세요. 고르지 않은 사람은 답에 「미답」으로 들어갑니다.</p>
  </section>
</main>
<div class="zoom" id="zoom" hidden>
  <div class="bar"><span id="ztitle"></span><button type="button" class="sub" id="zclose">닫기</button></div>
  <div class="view"><img id="zimg" alt=""></div>
</div>
<script>
const P = /*PEOPLE*/[];
const box = document.getElementById("people");
const esc = s => String(s).replace(/[&<>"]/g, m => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m]));
for (const p of P) {
  const sec = document.createElement("section");
  sec.className = "who"; sec.id = "who-" + p.id;
  const cands = p.cands.map(c => `<article class="c" id="c-${p.id}-${c.seed}">
      <img src="${c.front}" alt="${esc(p.name)} ${c.seed} 정면" data-z="${c.front}">
      <div class="meta"><b>${c.seed}</b><span class="chip ${c.vocab >= 7 ? "ok" : "bad"}">${c.top ? "기계 추천 · " : ""}${c.score ?? "-"}점</span></div>
      <p class="why">${esc(c.reason)}</p>
      <div class="meta"><label class="pick" for="p-${p.id}-${c.seed}"><input type="radio" name="${p.id}" id="p-${p.id}-${c.seed}" value="${c.seed}"> 이 얼굴</label>
        <button type="button" class="sub" data-z="${c.side}" data-t="${esc(p.name)} ${c.seed} 3/4">3/4</button></div></article>`).join("");
  const old = p.old ? `<article class="c" id="c-${p.id}-keep"><img src="${p.old}" alt="${esc(p.name)} 지금 정본" data-z="${p.old}">
      <div class="meta"><b>지금 정본</b><span class="chip bad">${esc(p.old_tag)}</span></div>
      <div class="meta"><label class="pick" for="p-${p.id}-keep"><input type="radio" name="${p.id}" id="p-${p.id}-keep" value="keep"> 그대로 둠</label></div></article>` : "";
  sec.innerHTML = `<h2>${esc(p.name)} <small style="font-family:var(--sans);font-size:.8rem;color:var(--muted)">${p.id}</small></h2>
    <p class="card-def">카드: ${esc(p.age)} · ${esc(p.head)} · 수염 ${esc(p.beard)} · ${esc(p.dress)}</p>
    <div class="row">${cands}${old}</div>
    <div class="alt"><label class="pick" for="p-${p.id}-none"><input type="radio" name="${p.id}" id="p-${p.id}-none" value="none"> 모두 아님 — 다시 그려야 함</label></div>`;
  box.appendChild(sec);
}
const zoom = document.getElementById("zoom"), zimg = document.getElementById("zimg");
document.addEventListener("click", e => {
  const t = e.target.closest("[data-z]");
  if (t) { zimg.src = t.dataset.z; document.getElementById("ztitle").textContent = t.dataset.t || t.alt || ""; zoom.hidden = false; }
  if (e.target.id === "zclose") zoom.hidden = true;
});
document.addEventListener("keydown", e => { if (e.key === "Escape") zoom.hidden = true; });
document.addEventListener("change", e => {
  if (e.target.type !== "radio") return;
  document.querySelectorAll(`#who-${e.target.name} .c`).forEach(c => c.classList.toggle("sel", c.id === `c-${e.target.name}-${e.target.value}`));
});
document.getElementById("alltop").addEventListener("click", () => {
  for (const p of P) {
    const top = p.cands.find(c => c.top) || p.cands[0];
    const r = document.getElementById(`p-${p.id}-${top.seed}`);
    if (r) { r.checked = true; r.dispatchEvent(new Event("change", { bubbles: true })); }
  }
});
document.getElementById("copy").addEventListener("click", () => {
  const v = {};
  for (const p of P) { const r = document.querySelector(`input[name="${p.id}"]:checked`); v[p.id] = r ? r.value : "미답"; }
  const memo = document.getElementById("memo").value.trim();
  if (memo) v._memo = memo;
  const text = "판정 task canon-faces\n" + JSON.stringify(v);
  const out = document.getElementById("out");
  out.textContent = text;
  const sel = () => { const rg = document.createRange(); rg.selectNodeContents(out); const s = getSelection(); s.removeAllRanges(); s.addRange(rg); };
  try { navigator.clipboard.writeText(text).then(() => { out.textContent = text + "\n(복사됨)"; }, sel); } catch (_) { sel(); }
});
</script>
"""


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--dir", default=os.path.expanduser("~/.local/biblemap-imggen/face-canon-v3"))
    ap.add_argument("--who", nargs="+")
    a = ap.parse_args()
    who = a.who or sorted(os.path.basename(p)[6:-5] for p in glob.glob(os.path.join(a.dir, "judge-*.json")))
    people = [person(cid, a.dir) for cid in who]
    page = PAGE.replace("/*PEOPLE*/[]", json.dumps(people, ensure_ascii=False))
    open(a.out, "w", encoding="utf-8").write(page)
    print(f"[CanonFace] 화면 {a.out} {len(page) / 1e6:.2f}MB · {len(people)}명")
