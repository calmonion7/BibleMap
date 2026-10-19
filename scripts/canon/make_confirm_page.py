#!/usr/bin/env python3
"""task#369 S2 — 편집 확인 페이지: 고른 바탕 한 장과 그 장에만 건 정본 편집본을 나란히(정본 초상·머리 크롭 함께), 답은 「편집본」 또는 「바탕」.

  python3 batch/run_night.py confirm-page --set whole-fix   # samples/whole-fix/metrics.json → ~/.local/biblemap-imggen/pages/whole-fix-confirm.html

장면마다 한 화면(한 화면 한 질문). 「없음」이거나 편집본이 없는 장면은 빠진다. 끝 화면의 「판정 문장 복사」를 run_night.py record가 읽는다."""
import json, os

from PIL import Image

import derive_scene as D
from make_night_page import NAME, fit, uri

HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.expanduser("~/.local/biblemap-imggen/pages")
# 과제마다 확인 페이지 파일 이름(task 370 회고 eval: 고정 이름이 369 페이지를 덮어쓸 뻔했다)
CONFIRM_DST = {369: "whole-fix-confirm.html", 370: "whole-wide-confirm.html", 373: "plate-rest-confirm.html"}


def build(m):
    scenes, data = [], {}
    for sid, sc in m["scenes"].items():
        pe = sc.get("pick_edit") or {}
        if not sc.get("pick") or sc["pick"]["seed"] is None or not pe.get("out"):
            continue
        s = sc["pick"]["seed"]
        x = next(x for x in sc["seeds"] if x["seed"] == s)
        W, H = Image.open(x["base"]).size
        data[sid + ":b"] = uri(Image.open(x["base"]), 1216, 84)
        data[sid + ":e"] = uri(Image.open(pe["out"]), 1216, 84)
        for who in sc["who"]:
            if os.path.exists(os.path.join(HERE, "frozen", f"{who}.png")):
                data["canon:" + who] = uri(Image.open(os.path.join(HERE, "frozen", f"{who}.png")), 360, 86)
        spec = D.load(sid)
        scenes.append({"id": sid, "title": spec["title"], "range": spec["verses"]["range"], "seed": s,
                       "who": [{"id": w, "name": NAME[w], "head": fit(x["boxes"][w]["head"], 1, W, H, 0.5)} for w in sc["who"]]})
    return scenes, data


def main(metrics, task):
    m = json.load(open(metrics))
    scenes, data = build(m)
    page = PAGE.replace("/*SCENES*/[]", json.dumps(scenes, ensure_ascii=False)).replace("/*IMGS*/{}", json.dumps(data)).replace("/*TASK*/0", str(task))
    dst = os.path.join(PAGES, CONFIRM_DST[task])   # 등록 안 된 과제는 KeyError — 이전 과제 페이지를 조용히 덮어쓰지 않게
    os.makedirs(PAGES, exist_ok=True)
    open(dst, "w", encoding="utf-8").write(page)
    print(f"[ConfirmPage] {dst} {len(page) / 1e6:.2f}MB · 장면 {len(scenes)}", flush=True)


PAGE = r"""<title>편집 확인 /*TASK*/0</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* 폰 한 화면 = 장면 하나: 질문 · 정본 초상 + 머리 크롭(바탕|편집본) · 전체 두 장 · 답 단추 둘 */
:root {
  --bg: #f3f4f2; --panel: #ffffff; --fg: #1d2421; --muted: #5d6a64; --line: #d5dad6; --pick: #24508a;
  --sans: "IBM Plex Sans KR", "Apple SD Gothic Neo", "Noto Sans KR", system-ui, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #161a18; --panel: #202623; --fg: #e6ebe8; --muted: #9aa7a1; --line: #343c38; --pick: #8db4ea; color-scheme: dark } }
:root[data-theme="dark"] { --bg: #161a18; --panel: #202623; --fg: #e6ebe8; --muted: #9aa7a1; --line: #343c38; --pick: #8db4ea; color-scheme: dark }
body { background: var(--bg); color: var(--fg); font: 15px/1.5 var(--sans); margin: 0; }
main { max-width: 720px; margin: 0 auto; padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 12px 32px; display: grid; gap: 12px; }
.bar { font: 500 12px/1.4 var(--mono); color: var(--muted); display: flex; justify-content: space-between; }
h1 { font-size: 15px; margin: 0; font-weight: 600; color: var(--muted); }
h2 { font-size: 21px; line-height: 1.3; margin: 0; text-wrap: balance; }
.hint { font-size: 13px; color: var(--muted); margin: 0; }
.heads { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; align-items: end; }
.heads figure, .full figure { margin: 0; display: grid; gap: 4px; }
figcaption { font: 500 12px/1.3 var(--mono); color: var(--muted); }
.heads img.canon { width: 100%; border-radius: 6px; border: 1px solid var(--line); }
.frame { position: relative; overflow: hidden; width: 100%; border-radius: 6px; border: 1px solid var(--line); background: var(--panel); }
.frame img { position: absolute; max-width: none; display: block; }
.full { display: grid; gap: 8px; }
.full img { width: 100%; border-radius: 6px; border: 1px solid var(--line); display: block; }
.row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
button.b { font: 600 15px var(--sans); border-radius: 8px; padding: 12px 16px; border: 1px solid var(--line); background: var(--panel); color: var(--fg); cursor: pointer; flex: 1; }
button.b.on { background: var(--pick); border-color: var(--pick); color: var(--panel); }
button.b:focus-visible { outline: 3px solid var(--pick); outline-offset: 2px; }
textarea { width: 100%; min-height: 120px; font: 12px/1.4 var(--mono); color: var(--fg); background: var(--panel); border: 1px solid var(--line); border-radius: 6px; padding: 8px; box-sizing: border-box; }
</style>
<main id="app"></main>
<script>
const SCENES = /*SCENES*/[];
const IMGS = /*IMGS*/{};
const TASK = /*TASK*/0;
const KEY = "whole-fix-confirm-" + TASK;
let st = { i: 0, ans: {}, t: {} };
try { const s = JSON.parse(localStorage.getItem(KEY) || "null"); if (s && s.ans) st = s; } catch (e) { console.warn("[Confirm] 저장본 읽기 실패", e); }
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) { console.warn("[Confirm] 저장 실패", e); } };
const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
function crop(key, c) {
  const [x, y, w, h] = c;
  return `<div class="frame" style="aspect-ratio:1"><img src="${IMGS[key]}" alt="" style="width:${100 / w}%;left:${-x / w * 100}%;top:${-y / h * 100}%"></div>`;
}
function render() {
  const app = document.getElementById("app");
  if (st.i >= SCENES.length) return renderEnd(app);
  const s = SCENES[st.i], cur = st.ans[s.id];
  st.t[s.id] = st.t[s.id] || { start: Date.now(), end: null };
  app.innerHTML = `<div class="bar"><span>장면 ${st.i + 1}/${SCENES.length}</span><span>s${s.seed}</span></div>
    <h1>${esc(s.title)} · ${esc(s.range)}</h1>
    <h2>고른 그림을 어느 쪽으로 쓸까요?</h2>
    <p class="hint">편집본은 고른 바탕에 ${esc(s.who.map((w) => w.name).join("·"))} 정본 얼굴 편집을 건 것입니다. 장면 전체가 더 나은 쪽을 고르세요.</p>
    ${s.who.map((w) => `<div class="heads"><figure><img class="canon" src="${IMGS["canon:" + w.id] || ""}" alt="${esc(w.name)} 정본 초상"><figcaption>${esc(w.name)} 정본</figcaption></figure>
      <figure>${crop(s.id + ":b", w.head)}<figcaption>바탕</figcaption></figure><figure>${crop(s.id + ":e", w.head)}<figcaption>편집본</figcaption></figure></div>`).join("")}
    <div class="full"><figure><img src="${IMGS[s.id + ":b"]}" alt="바탕 s${s.seed}"><figcaption>바탕</figcaption></figure>
      <figure><img src="${IMGS[s.id + ":e"]}" alt="편집본 s${s.seed}"><figcaption>편집본</figcaption></figure></div>
    <div class="row"><button class="b${cur === "편집본" ? " on" : ""}" data-a="편집본" type="button">편집본</button><button class="b${cur === "바탕" ? " on" : ""}" data-a="바탕" type="button">바탕</button></div>
    ${st.i ? `<div class="row"><button class="b" id="prev" type="button">이전</button></div>` : ""}`;
  app.querySelectorAll("[data-a]").forEach((b) => b.onclick = () => { st.ans[s.id] = b.dataset.a; st.t[s.id].end = Date.now(); st.i++; save(); render(); });
  const p = document.getElementById("prev"); if (p) p.onclick = () => { st.i--; save(); render(); };
  save(); window.scrollTo(0, 0);
}
function verdict() {
  const out = { task: TASK, kind: "confirm", scenes: {} };
  SCENES.forEach((s) => { const t = st.t[s.id] || {}; out.scenes[s.id] = { confirm: { answer: st.ans[s.id] || null, seed: s.seed },
    minutes: t.start && t.end ? +((t.end - t.start) / 60000).toFixed(2) : null }; });
  return out;
}
function renderEnd(app) {
  const text = `판정 task ${TASK} 확인\n` + JSON.stringify(verdict());
  app.innerHTML = `<div class="bar"><span>끝</span><span>${Object.keys(st.ans).length}/${SCENES.length}</span></div>
    <h2>판정 문장을 복사해 대화에 붙여 주세요</h2>
    <div class="row"><button class="b on" id="copy" type="button">판정 문장 복사</button><button class="b" id="prev" type="button">이전</button></div>
    <p class="hint" id="ok"></p><textarea id="out" readonly></textarea>`;
  const ta = document.getElementById("out"); ta.value = text;
  document.getElementById("prev").onclick = () => { st.i = SCENES.length - 1; save(); render(); };
  document.getElementById("copy").onclick = () => navigator.clipboard.writeText(text)
    .then(() => { document.getElementById("ok").textContent = "복사됨"; })
    .catch(() => { ta.focus(); ta.select(); document.getElementById("ok").textContent = "자동 복사가 막혀 글을 선택해 두었습니다. 직접 복사하세요."; });
}
render();
</script>
"""
