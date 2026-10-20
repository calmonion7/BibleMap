#!/usr/bin/env python3
"""task#376 — 후보 화면(용어집 「장면 고르기」의 후보 화면): 기계(J1)가 먼저 고른 후보 한 장을 사람이 확인·뒤집는다.

  python3 make_cand_page.py 376     # samples/verse-regen/metrics.json + J1 답 → ~/.local/biblemap-imggen/pages/verse-regen-cand.html

장면마다 후보 화면(후보 큰 그림 + 요소 문항 + 나머지 시드 작은 그림 — 누르면 후보가 바뀜)과 블라인드 표본 화면(표본 그림 + 요소 문항),
되돌림 장면은 한 화면(동의 / 살릴 시드). 문항은 J1이 읽은 문항 페이지(TASKS의 *-pick.html) 그대로(.identity 제외), 기계 표시는 없다.
규칙은 batch/judge_learn.pick_candidates(notes/VERSE-REGEN.md 고정 절). 「판정 문장 복사」 = `판정 task N` + JSON 한 줄(2/2의 record가 읽음)."""
import json, os, sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "batch"))
import judge_items as J
import judge_learn as JL
import make_night_page as P

STYLE = P.PAGE[P.PAGE.index("<style>"):P.PAGE.index("</style>")]   # 판정 페이지와 같은 토큰·카드·단추
SIZES = ((1216, 84), (1216, 72), (1216, 62), (1024, 66), (1024, 58), (880, 56))


def dst(task):
    return J.TASKS[task][1].replace("-pick.html", "-cand.html")


def build(task, w, q):
    d, fn, _ = J.TASKS[task]
    m = json.load(open(os.path.join(HERE, "samples", d, "metrics.json")))
    rule = JL.candidates(task)
    scenes, data = [], {}
    for s in J.page_scenes(fn):
        sc, c = m["scenes"][s["id"]], rule[s["id"]]
        for x in sc["seeds"]:
            data[f"{s['id']}:{x['seed']}"] = P.uri(Image.open(x["base"]), w, q)
        scenes.append({"id": s["id"], "title": s["title"], "range": s["range"], "seeds": s["seeds"],
                       "qs": [x for x in s["qs"] if not x["id"].endswith(".identity") and x.get("grp") != "plate"],   # J1과 같은 문항
                       "cand": c["cand"], "sample": c["sample"], "reject": c["reject"],
                       "order": JL.sample_order(s["id"], s["seeds"])})
    return scenes, data


def main(task=376):
    for w, q in SIZES:
        scenes, data = build(task, w, q)
        page = (PAGE.replace("/*STYLE*/", STYLE).replace("/*SCENES*/[]", json.dumps(scenes, ensure_ascii=False))
                .replace("/*IMGS*/{}", json.dumps(data)).replace("/*TASK*/0", str(task)))
        if len(page) <= P.LIMIT:
            break
    out = os.path.join(P.PAGES, dst(task))
    os.makedirs(P.PAGES, exist_ok=True)
    open(out, "w", encoding="utf-8").write(page)
    rej = [s["id"] for s in scenes if s["reject"]]
    print(f"[CandPage] {out} {len(page) / 1e6:.2f}MB · {w}px q{q} · 장면 {len(scenes)} · 되돌림 {len(rej)} {rej or ''} · 화면 {JL.screens(scenes)}", flush=True)


PAGE = r"""<title>장면 후보 고르기 /*TASK*/0</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
/*STYLE*/
/* 후보 화면: 큰 그림 한 장 + 요소 문항 줄(눌러 틀림) + 다른 시드 작은 그림 */
.big { border: 1px solid var(--line); border-radius: 6px; overflow: hidden; position: relative; }
.qs { display: grid; gap: 6px; }
.q { display: grid; grid-template-columns: 1fr auto; gap: 8px; align-items: center; text-align: left; width: 100%;
  border: 2px solid var(--line); border-radius: 8px; background: var(--panel); color: inherit; font: inherit; padding: 8px 10px; cursor: pointer; }
.q:focus-visible { outline: 3px solid var(--pick); outline-offset: 2px; }
.q b { font-weight: 600; }
.q small { display: block; color: var(--muted); font-size: 13px; }
.q .st { font-size: 12px; font-weight: 600; color: var(--muted); }
.q.on { border-color: var(--wrong); background: var(--wrong-bg); }
.q.on .st { color: var(--wrong); }
.q .thumb { width: 54px; border-radius: 4px; overflow: hidden; border: 1px solid var(--line); }
.q .body { display: flex; gap: 8px; align-items: center; min-width: 0; }
.alts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; }
.alts .card { border-width: 1px; }
.alts.eight { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.answer { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
</style>
<main id="app"></main>
<footer><div class="row"><button class="b" id="prev" type="button">이전</button><span class="bar" id="clock"></span><button class="b main" id="next" type="button">다음</button></div></footer>
<div class="ov" id="ov" hidden></div>
<script>
const SCENES = /*SCENES*/[];
const IMGS = /*IMGS*/{};
const TASK = /*TASK*/0;
const KEY = "cand-page-" + TASK;
let st = { i: 0, t0: null, done: null, sc: {} };
try { const s = JSON.parse(localStorage.getItem(KEY) || "null"); if (s && s.sc) st = s; } catch (e) { console.warn("[CandPage] 저장본 읽기 실패", e); }
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) { console.warn("[CandPage] 저장 실패", e); } };
const SCREENS = [];
SCENES.forEach((s, k) => { if (s.reject) SCREENS.push({ s, k, t: "reject" }); else { SCREENS.push({ s, k, t: "cand" }); SCREENS.push({ s, k, t: "sample" }); } });
SCREENS.push({ t: "end" });
const $ = (h) => { const d = document.createElement("div"); d.innerHTML = h; return d; };
const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
// 장면 상태: cand = 지금 후보(기계 후보에서 시작) · marks[시드] = 틀림 문항 · switched = 바꾸기 전 후보와 그때 표시
const S = (s) => (st.sc[s.id] = st.sc[s.id] || { cand: s.cand, marks: {}, switched: [], answer: null, revived: null, sampleDone: false, memo: "", start: null, end: null });
const marks = (a, seed) => (a.marks[seed] = a.marks[seed] || []);
const label = (q) => q.q.replace(/(이|가) 틀린 그림$/, "").replace(/ 그림$/, "");
const sampleOf = (s, a) => s.sample === a.cand ? s.order.find((x) => x !== a.cand) : s.sample;

function img(key, crop, ar) {
  if (!crop) return `<div class="frame" style="aspect-ratio:1216/640"><img src="${IMGS[key]}" alt="" style="width:100%;left:0;top:0"></div>`;
  const [x, y, w, h] = crop;
  return `<div class="frame" style="aspect-ratio:${ar}"><img src="${IMGS[key]}" alt="" style="width:${100 / w}%;left:${-x / w * 100}%;top:${-y / h * 100}%"></div>`;
}
function tick() { const m = st.t0 ? ((st.done || Date.now()) - st.t0) / 60000 : 0; document.getElementById("clock").textContent = `${m.toFixed(1)}분`; }
function qrows(s, a, seed) {
  const on = marks(a, seed);
  return s.qs.map((q) => `<button type="button" class="q${on.includes(q.id) ? " on" : ""}" data-q="${esc(q.id)}">
    <span class="body">${q.crop ? `<span class="thumb">${img(`${s.id}:${seed}`, q.crop[seed], q.ar)}</span>` : ""}<span><b>${esc(label(q))}</b><small>${esc(q.what)}</small></span></span>
    <span class="st">${on.includes(q.id) ? "틀림" : "맞음"}</span></button>`).join("");
}
function bindQ(app, a, seed) {
  app.querySelectorAll(".q").forEach((b) => b.onclick = () => {
    const id = b.dataset.q, on = marks(a, seed);
    a.marks[seed] = on.includes(id) ? on.filter((x) => x !== id) : [...on, id];
    b.classList.toggle("on"); b.querySelector(".st").textContent = b.classList.contains("on") ? "틀림" : "맞음"; save();
  });
}
function bigImg(s, seed) { return `<button type="button" class="card big" data-z="${seed}">${img(`${s.id}:${seed}`)}<span class="tag">s${seed}</span><span class="zoom">크게</span></button>`; }
function head(sc, what) {
  return `<div class="bar"><span>장면 ${sc.k + 1}/${SCENES.length}</span><span>${what}</span></div><h1>${esc(sc.s.title)} · ${esc(sc.s.range)}</h1>`;
}
function next() { st.i = Math.min(SCREENS.length - 1, st.i + 1); save(); render(); }
function render() {
  if (!st.t0) st.t0 = Date.now();
  const sc = SCREENS[st.i], app = document.getElementById("app");
  document.getElementById("prev").disabled = st.i === 0;
  document.getElementById("next").hidden = sc.t !== "sample";
  app.innerHTML = "";
  if (sc.t === "end") return renderEnd(app);
  const a = S(sc.s);
  if (!a.start) a.start = Date.now();
  if (sc.t === "reject" && a.revived == null) return renderReject(app, sc, a);
  if (sc.t === "sample") return renderSample(app, sc, a);
  renderCand(app, sc, a);
}
function renderCand(app, sc, a) {
  const s = sc.s, seed = a.cand;
  const alts = s.seeds.filter((x) => x !== seed);
  app.append($(`${head(sc, sc.t === "reject" ? "살린 시드" : "후보")}
    <h2>이 그림을 이 장면에 쓸 수 있나요?</h2>
    <p class="hint">${sc.t === "reject" ? "기계가 되돌리려던 장면에서 살린 그림입니다." : "기계가 8장 중 고른 후보입니다."} 틀린 항목만 누르세요(기본은 모두 맞음).</p>
    ${bigImg(s, seed)}
    <div class="qs">${qrows(s, a, seed)}</div>
    <input type="text" id="memo" placeholder="한 줄 메모(선택)" value="${esc(a.memo)}">
    <div class="answer"><button class="b main" id="ok" type="button">쓸 만함</button><button class="b no" id="none" type="button">없음</button></div>
    ${sc.t === "reject" ? `<div class="row"><button class="b" id="back" type="button">되돌림 화면으로(살리지 않음)</button></div>` : ""}
    <p class="hint">다른 그림이 더 낫다면 눌러 후보를 바꾸세요 — 그 그림으로 다시 묻습니다.</p>
    <div class="alts">${alts.map((x) => `<button type="button" class="card" data-alt="${x}">${img(`${s.id}:${x}`)}<span class="tag">s${x}</span></button>`).join("")}</div>`));
  bindQ(app, a, seed);
  app.querySelector("[data-z]").onclick = () => zoom(s.id, seed);
  app.querySelectorAll("[data-alt]").forEach((b) => b.onclick = () => {
    a.switched.push({ seed, wrong: [...marks(a, seed)] }); a.cand = +b.dataset.alt; a.answer = null; save(); render();
  });
  document.getElementById("memo").oninput = (e) => { a.memo = e.target.value; save(); };
  const back = document.getElementById("back");
  if (back) back.onclick = () => { a.revived = null; a.cand = s.cand; a.answer = null; save(); render(); };
  const done = (ans) => { a.answer = ans; a.end = Date.now(); next(); };
  document.getElementById("ok").onclick = () => done("쓸 만함");
  document.getElementById("none").onclick = () => done("없음");
  save(); window.scrollTo(0, 0);
}
function renderSample(app, sc, a) {
  const s = sc.s, seed = sampleOf(s, a);
  app.append($(`${head(sc, "블라인드 표본")}
    <h2>이 그림에서 틀린 항목을 누르세요</h2>
    <p class="hint">후보가 아닌 그림 하나를 기계 표시 없이 묻습니다(기계 성적을 재는 화면). 끝나면 「다음」.</p>
    ${bigImg(s, seed)}<div class="qs">${qrows(s, a, seed)}</div>`));
  bindQ(app, a, seed);
  app.querySelector("[data-z]").onclick = () => zoom(s.id, seed);
  a.sampleShown = seed; a.sampleDone = true; save(); window.scrollTo(0, 0);
}
function renderReject(app, sc, a) {
  const s = sc.s;
  app.append($(`${head(sc, "되돌림")}
    <div class="machine"><p><b>기계: 8장 모두 장면 뜻이 틀렸다고 봤습니다 → 명세로 돌려보냄.</b></p>
    <p class="hint">동의하면 「동의」. 쓸 만한 그림이 있으면 그 그림을 누르세요 — 그 그림으로 후보 화면을 엽니다.</p></div>
    <div class="alts eight">${s.seeds.map((x) => `<button type="button" class="card" data-rev="${x}">${img(`${s.id}:${x}`)}<span class="tag">s${x}</span></button>`).join("")}</div>
    <div class="row"><button class="b main" id="agree" type="button">동의</button></div>`));
  app.querySelectorAll("[data-rev]").forEach((b) => b.onclick = () => { a.revived = a.cand = +b.dataset.rev; save(); render(); });
  document.getElementById("agree").onclick = () => { a.answer = "동의"; a.end = Date.now(); next(); };
  save(); window.scrollTo(0, 0);
}
function verdict() {
  const now = st.done || Date.now(), out = { task: TASK, kind: "cand", human_minutes: +((now - st.t0) / 60000).toFixed(2), screens: SCREENS.length - 1, scenes: {} };
  SCENES.forEach((s) => {
    const a = S(s), agree = a.answer === "동의";
    const shown = agree ? [] : [a.answer ? a.cand : null, a.sampleDone ? a.sampleShown : null].filter((x) => x != null);
    const items = {};
    s.qs.forEach((q) => {
      items[q.id] = agree ? { wrong: [], seeds: [], skipped: true, unsure: false, memo: "" }
        : { wrong: shown.filter((x) => marks(a, x).includes(q.id)), seeds: shown, blind: true, machine: null, unsure: false, memo: "" };
    });
    const pick = a.answer === "쓸 만함" ? { answer: `s${a.cand} 바탕`, seed: a.cand, kind: "base" }
      : { answer: "없음", seed: null, kind: null, memo: agree ? "기계 되돌림에 동의 — 장면 뜻 8장 모두 틀림" : a.memo, ...(agree ? { machine_reject: true } : {}) };
    out.scenes[s.id] = { minutes: a.start && a.end ? +((a.end - a.start) / 60000).toFixed(2) : null, machine_cand: s.cand, reject: s.reject,
      revived: a.revived, cand: agree ? null : a.cand, sample: a.sampleDone ? a.sampleShown : null, answer: a.answer,
      switched: a.switched, memo: a.memo, items, pick, ...(agree ? { skipped: true } : {}) };
  });
  return out;
}
function renderEnd(app) {
  const missing = SCENES.filter((s) => !S(s).answer).map((s) => s.title);
  app.append($(`<div class="bar"><span>끝</span><span>장면 ${SCENES.length - missing.length}/${SCENES.length} 답함</span></div>
    <h2>판정 문장을 복사해 대화에 붙여 주세요</h2>
    ${missing.length ? `<p class="hint">아직 답하지 않은 장면: ${esc(missing.join(", "))} — 「이전」으로 돌아가 답하세요.</p>` : ""}
    <div class="row"><button class="b main" id="copy" type="button">판정 문장 복사</button><span class="hint" id="okc"></span></div>
    <textarea id="out" readonly></textarea>`));
  const ta = document.getElementById("out");
  ta.value = `판정 task ${TASK}\n` + JSON.stringify(verdict());
  document.getElementById("copy").onclick = () => {
    if (!st.done) st.done = Date.now();
    save(); tick();
    ta.value = `판정 task ${TASK}\n` + JSON.stringify(verdict());
    navigator.clipboard.writeText(ta.value).then(() => { document.getElementById("okc").textContent = "복사됨"; })
      .catch(() => { ta.focus(); ta.select(); document.getElementById("okc").textContent = "자동 복사가 막혀 글을 선택해 두었습니다. 직접 복사하세요."; });
  };
}
function zoom(sid, s) {
  const ov = document.getElementById("ov");
  ov.innerHTML = `<div class="row" style="justify-content:space-between"><b>s${s}</b><button class="b main" id="close" type="button">닫기</button></div><img src="${IMGS[`${sid}:${s}`]}" alt="s${s}">`;
  document.getElementById("close").onclick = () => { ov.hidden = true; };
  ov.hidden = false;
}
document.getElementById("prev").onclick = () => { st.i = Math.max(0, st.i - 1); save(); render(); };
document.getElementById("next").onclick = next;
if (st.i >= SCREENS.length) st.i = 0;
render(); setInterval(tick, 5000); tick();
</script>
"""

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 376)
