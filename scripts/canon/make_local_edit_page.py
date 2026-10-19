#!/usr/bin/env python3
"""task#371 — 국소 편집 판정 페이지: 한 화면 한 문항(「틀린 그림을 누르세요」) → 마지막 고르기(편집 후보 하나 또는 없음).

  python3 gen_local_edit.py page 1|2     # samples/local-edit/metrics.json → ~/.local/biblemap-imggen/pages/local-edit-*.html

후보는 「후보 NN」 번호로만 보이고 번호는 LOCAL_EDIT_SHUFFLE_SEED로 섞는다. 처치 없는 바탕(2단계는 1단계 고른 장)을 대조로
섞되 고르기에는 내지 않는다(2단계의 1단계 그림은 「그대로 쓰기」로 고를 수 있다). 고정 절 notes/LOCAL-EDIT.md."""
import json, os, random

from PIL import Image

import params
import derive_scene as D
from make_night_page import NAME, PAGE as NIGHT, fit, uri

HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.expanduser("~/.local/biblemap-imggen/pages")
DST = {1: "local-edit-pick.html", 2: "local-edit-face.html"}
WIDE = os.path.join(HERE, "samples", "whole-wide", "metrics.json")
LIMIT = 15.5e6
SEAM = ("편집 자리가 튀는 그림", "편집한 부위의 색·화풍·경계가 둘레와 어긋나 보이면 누르세요.")


def qs_for(sid, stage, spec):
    """→ 문항 [{id, q, what, src, view}] — view: crop(편집 부위) · full · head:<인물>."""
    if sid == "authored-david-nob-priests":
        f0, f1 = spec["figures"]
        return [{"id": "prop", "q": "칼이 보자기에 싸여 손잡이만 보이지 않는 그림", "what": "칼 전체가 천(보자기)에 싸인 꾸러미이고, 한쪽 끝에 손잡이만 나와야 합니다. 칼날이 드러나면 틀림.",
                 "src": "figures[0].prop · " + f0["verse"], "view": "crop"},
                {"id": "moment", "q": "두 사람이 그 꾸러미를 함께 잡고 있지 않은 그림", "what": spec["moment"]["why"], "src": "moment · " + spec["moment"]["verse"], "view": "full"},
                {"id": "seam", "q": SEAM[0], "what": SEAM[1], "src": "이음새", "view": "crop"},
                {"id": "figures[0].identity", "q": "아히멜렉이 정본과 다른 사람으로 보이는 그림", "what": "얼굴·머리·수염·나이대만 봅니다(옷은 빼고).",
                 "src": "figures[0] 정본", "view": "head:" + f0["cast"], "canon": f0["cast"]},
                {"id": "figures[1].identity", "q": "다윗이 정본과 다른 사람으로 보이는 그림", "what": "얼굴·머리·수염·나이대만 봅니다(옷은 빼고).",
                 "src": "figures[1] 정본", "view": "head:" + f1["cast"], "canon": f1["cast"]}]
    f0 = spec["figures"][0]
    if stage == 1:
        return [{"id": "figures[0].pose", "q": "다윗이 기둥에 기대지 않은 그림", "what": "다윗이 나무 성문 기둥에 어깨를 기대고, 고개가 기울고, 두 팔이 늘어져야 합니다.",
                 "src": "figures[0].pose · " + f0["verse"], "view": "crop"},
                {"id": "figures[0].facing", "q": "다윗이 누군가와 마주 보는 그림", "what": f0["gaze"]["ko"], "src": "figures[0].gaze · " + f0["gaze"]["verse"], "view": "crop"},
                {"id": "figures[0].prop", "q": "다윗 곁에 나무 성문 기둥이 없는 그림", "what": "다윗이 기댄 것이 나무 성문 기둥이어야 합니다(돌벽 모서리·막대 띠는 틀림).",
                 "src": "figures[0].prop · " + f0["verse"], "view": "crop"},
                {"id": "seam", "q": SEAM[0], "what": SEAM[1], "src": "이음새", "view": "crop"},
                {"id": "figures[0].identity", "q": "다윗이 정본과 다른 사람으로 보이는 그림", "what": "얼굴·머리·수염·나이대만 봅니다(옷은 빼고).",
                 "src": "figures[0] 정본", "view": "head:david", "canon": "david"}]
    return [{"id": "spit", "q": "침이 안 보이는 그림", "what": "벌린 입에서 침이 수염으로 흘러내려야 합니다(삼상 21:13 「침을 수염에 흘리매」).", "src": "figures[0] · 21:13", "view": "crop"},
            {"id": "moment", "q": "미친 체하는 얼굴이 아닌 그림", "what": "눈이 초점 없이 풀리고 입이 늘어진, 미친 체하는 얼굴이어야 합니다. " + spec["moment"]["why"],
             "src": "moment · " + spec["moment"]["verse"], "view": "crop"},
            {"id": "figures[0].identity", "q": "다윗이 정본과 다른 사람으로 보이는 그림", "what": "얼굴·머리·수염·나이대만 봅니다(옷은 빼고).",
             "src": "figures[0] 정본", "view": "crop", "canon": "david"},
            {"id": "seam", "q": SEAM[0], "what": SEAM[1], "src": "이음새", "view": "crop"}]


def frac(crop, W, H):
    L, T, side = crop
    return [round(L / W, 4), round(T / H, 4), round(side / W, 4), round(side / H, 4)]


def build(m, stage, q):
    import gen_local_edit as E
    wide = json.load(open(WIDE))["scenes"]
    scenes, data = [], {}
    for sid, sc in m["scenes"].items():
        if stage == 2 and sid != E.GATH:
            continue
        spec = D.load(sid)
        cands = [c for c in sc["candidates"] if c["stage"] == stage]
        if not cands:
            continue
        if stage == 1:
            ctrl = [{"id": f"base-b{b}", "base": int(b), "image": p, "crop": list(E.BOX[(sid, int(b))][0]), "ctrl": True}
                    for b, p in sc["bases"].items()]
        else:
            first = next(c for c in sc["candidates"] if c["id"] == sc["pick1"]["id"])
            ctrl = [{**first, "crop": sc["face"]["crop"], "ctrl": True, "keep": True}]
        allc = cands + ctrl
        random.Random(f"{params.LOCAL_EDIT_SHUFFLE_SEED}:{sid}:{stage}").shuffle(allc)
        labels = {}
        for n, c in enumerate(allc, 1):
            labels[c["id"]] = f"{n:02d}"
        W, H = Image.open(allc[0]["image"]).size
        heads = {}
        for c in allc:
            data[f"{sid}:{c['id']}"] = uri(Image.open(c["image"]), 1000, q)
            bx = next(x for x in wide[sid]["seeds"] if x["seed"] == c["base"])["boxes"]
            for who in bx:
                heads.setdefault(who, {})[c["id"]] = fit(bx[who]["head"], 1, W, H, 0.6)
        scenes.append({"id": sid, "title": spec["title"], "range": spec["verses"]["range"], "stage": stage,
                       "cands": [{"id": c["id"], "label": labels[c["id"]], "ctrl": bool(c.get("ctrl")), "keep": bool(c.get("keep")),
                                  "crop": frac(c["crop"], W, H)} for c in sorted(allc, key=lambda c: labels[c["id"]])],
                       "heads": heads, "qs": qs_for(sid, stage, spec)})
        sc[f"labels{stage}"] = labels   # 번호 ↔ 후보 대응(metrics에만)
    for who in ("david", "ahimelech", "achish"):
        p = os.path.join(HERE, "frozen", f"{who}.png")
        if os.path.exists(p):
            data["canon:" + who] = uri(Image.open(p), 360, 86)
    return scenes, data


def main(metrics, stage):
    import gen_local_edit as E
    m = json.load(open(metrics))
    for q in (82, 76, 70, 64):
        scenes, data = build(m, stage, q)
        page = (PAGE.replace("/*SCENES*/[]", json.dumps(scenes, ensure_ascii=False)).replace("/*IMGS*/{}", json.dumps(data))
                .replace("/*STAGE*/1", str(stage)))
        if len(page) <= LIMIT:
            break
    E.save_m(m)
    dst = os.path.join(PAGES, DST[stage])
    os.makedirs(PAGES, exist_ok=True)
    open(dst, "w", encoding="utf-8").write(page)
    n = sum(len(s["qs"]) + 1 for s in scenes)
    print(f"[LocalEditPage] {dst} {len(page) / 1e6:.2f}MB · JPEG q{q} · 장면 {len(scenes)} · 화면 {n}", flush=True)


STYLE = NIGHT.split("<style>", 1)[1].split("</style>", 1)[0]   # 370 페이지와 같은 화면 틀(토큰·다크 모드·폰 여백)
PAGE = r"""<title>국소 편집 판정 371</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>""" + STYLE + r"""
.full2 { display: grid; gap: 6px; }
.ctrl { font: 500 11px/1 var(--mono); color: var(--muted); }
</style>
<main id="app"></main>
<footer><div class="row"><button class="b" id="prev" type="button">이전</button><span class="bar" id="clock"></span><button class="b main" id="next" type="button">다음</button></div></footer>
<div class="ov" id="ov" hidden></div>
<script>
const SCENES = /*SCENES*/[];
const IMGS = /*IMGS*/{};
const STAGE = /*STAGE*/1;
const KEY = "local-edit-371-" + STAGE;
let st = { i: 0, ans: {}, t0: null, sceneT: {}, done: null };
try { const s = JSON.parse(localStorage.getItem(KEY) || "null"); if (s && s.ans) st = s; } catch (e) { console.warn("[LocalEdit] 저장본 읽기 실패", e); }
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) { console.warn("[LocalEdit] 저장 실패", e); } };
const SCREENS = [];
SCENES.forEach((s, k) => { s.qs.forEach((q, j) => SCREENS.push({ s, k, q, j })); SCREENS.push({ s, k, pick: true }); });
SCREENS.push({ end: true });
const $ = (h) => { const d = document.createElement("div"); d.innerHTML = h; return d; };
const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const A = (sid) => (st.ans[sid] = st.ans[sid] || { items: {}, pick: null });
const item = (sid, id) => (A(sid).items[id] = A(sid).items[id] || { wrong: [], unsure: false, memo: "" });

function frame(key, crop, ar) {
  if (!crop) return `<div class="frame" style="aspect-ratio:1216/640"><img src="${IMGS[key]}" alt="" style="width:100%;left:0;top:0"></div>`;
  const [x, y, w, h] = crop;
  return `<div class="frame" style="aspect-ratio:${ar}"><img src="${IMGS[key]}" alt="" style="width:${100 / w}%;left:${-x / w * 100}%;top:${-y / h * 100}%"></div>`;
}
function view(s, c, v) {
  const key = `${s.id}:${c.id}`;
  if (v === "full") return frame(key);
  if (v.startsWith("head:")) return frame(key, s.heads[v.slice(5)][c.id], 1);
  return frame(key, c.crop, 1216 / 640 * c.crop[2] / c.crop[3]);
}
function tick() { const m = st.t0 ? ((st.done || Date.now()) - st.t0) / 60000 : 0; document.getElementById("clock").textContent = `${m.toFixed(1)}분`; }
function render() {
  if (!st.t0) st.t0 = Date.now();
  const sc = SCREENS[st.i], app = document.getElementById("app");
  document.getElementById("prev").disabled = st.i === 0;
  document.getElementById("next").hidden = !!(sc.end || sc.pick);
  if (sc.end) return renderEnd(app);
  const t = st.sceneT[sc.s.id] = st.sceneT[sc.s.id] || { start: Date.now(), end: null };
  const head = `<div class="bar"><span>장면 ${sc.k + 1}/${SCENES.length} · ${STAGE}단계</span><span>${sc.pick ? "고르기" : `문항 ${sc.j + 1}/${sc.s.qs.length}`}</span></div>
    <h1>${esc(sc.s.title)} · ${esc(sc.s.range)}</h1>`;
  if (sc.pick) return renderPick(app, sc, head);
  const q = sc.q, it = item(sc.s.id, q.id);
  const canon = q.canon && IMGS["canon:" + q.canon] ? `<div class="canon"><img src="${IMGS["canon:" + q.canon]}" alt="정본 초상"><p class="hint">왼쪽이 정본 초상입니다.</p></div>` : "";
  const cards = sc.s.cands.map((c) => `<button type="button" class="card${it.wrong.includes(c.id) ? " on" : ""}" data-c="${c.id}">${view(sc.s, c, q.view)}<span class="tag">${c.label}</span><span class="zoom" data-z="${c.id}" role="button" tabindex="0">크게</span></button>`).join("");
  app.innerHTML = "";
  app.append($(`${head}<h2>${esc(q.q)}을 누르세요</h2>
    <div class="what"><p>${esc(q.what)}</p><span class="src">${esc(q.src)}</span></div>${canon}
    <p class="hint">이 항목이 틀린 후보만 누르세요. 기본은 모두 맞음입니다. ${q.view === "full" ? "전체 그림" : q.view.startsWith("head") ? "머리 크롭" : "편집 부위 크롭"}을 보여 주고, 「크게」는 전체 그림입니다.</p>
    <div class="grid${q.view === "full" ? " full" : ""}">${cards}</div>
    <label class="row"><input type="checkbox" id="unsure" ${it.unsure ? "checked" : ""}> 모르겠음</label>
    <input type="text" id="memo" placeholder="한 줄 메모(선택)" value="${esc(it.memo)}">`));
  app.querySelectorAll(".card").forEach((el) => el.addEventListener("click", (ev) => {
    const id = el.dataset.c;
    if (ev.target.dataset.z) return zoom(sc.s, id);
    it.wrong = it.wrong.includes(id) ? it.wrong.filter((x) => x !== id) : [...it.wrong, id];
    el.classList.toggle("on"); save();
  }));
  document.getElementById("unsure").onchange = (e) => { it.unsure = e.target.checked; save(); };
  document.getElementById("memo").oninput = (e) => { it.memo = e.target.value; save(); };
  save(); window.scrollTo(0, 0);
}
function wrongCount(sid, id) { return Object.values(A(sid).items).filter((v) => v.wrong.includes(id)).length; }
function renderPick(app, sc, head) {
  const s = sc.s, cur = A(s.id).pick;
  const opts = s.cands.filter((c) => !c.ctrl || c.keep).sort((a, b) => wrongCount(s.id, a.id) - wrongCount(s.id, b.id));
  app.innerHTML = "";
  app.append($(`${head}<h2>이 장면에 쓸 그림 하나를 고르세요</h2>
    <p class="hint">틀림 표시가 적은 순서입니다. 대조로 섞은 바탕은 고를 수 없습니다${STAGE === 2 ? "(1단계 그림은 「그대로 쓰기」로 고를 수 있습니다)" : ""}.</p>
    ${opts.map((c) => `<div class="pick"><div class="meta"><b>후보 ${c.label}</b><span>틀림 표시 ${wrongCount(s.id, c.id)}개</span>${c.keep ? `<span>1단계 그림(침 편집 없음)</span>` : ""}</div>
      <div class="full2">${view(s, c, "full")}${view(s, c, "crop")}</div>
      <div class="row"><button class="b${cur && cur.id === c.id ? " main" : ""}" data-p="${c.id}" data-l="${c.label}" type="button">${c.keep ? "1단계 그림 그대로 쓰기" : "이 후보로 고르기"}</button></div></div>`).join("")}
    <div class="pick"><p class="hint">쓸 그림이 없으면 이유를 적고 「없음」을 누르세요.</p>
      <input type="text" id="why" placeholder="없음 이유 한 줄" value="${esc(cur && cur.answer === "없음" ? cur.memo : "")}">
      <button class="b no" data-none="1" type="button">없음</button></div>`));
  const done = (p) => { A(s.id).pick = p; st.sceneT[s.id].end = Date.now(); st.i++; save(); render(); };
  app.querySelectorAll("[data-p]").forEach((b) => b.onclick = () => done({ answer: `편집 ${b.dataset.p}`, id: b.dataset.p, label: b.dataset.l }));
  app.querySelector("[data-none]").onclick = () => done({ answer: "없음", id: null, memo: document.getElementById("why").value });
  save(); window.scrollTo(0, 0);
}
function verdict() {
  const now = st.done || Date.now(), out = { task: 371, stage: STAGE, human_minutes: +((now - st.t0) / 60000).toFixed(2), scenes: {} };
  SCENES.forEach((s) => {
    const a = A(s.id), t = st.sceneT[s.id] || {}, items = {};
    s.qs.forEach((q) => { items[q.id] = item(s.id, q.id); });
    out.scenes[s.id] = { minutes: t.start && t.end ? +((t.end - t.start) / 60000).toFixed(2) : null, items, pick: a.pick };
  });
  return out;
}
function renderEnd(app) {
  const missing = SCENES.filter((s) => !A(s.id).pick).map((s) => s.title);
  app.innerHTML = "";
  app.append($(`<div class="bar"><span>끝</span><span>장면 ${SCENES.length - missing.length}/${SCENES.length} 고름</span></div>
    <h2>판정 문장을 복사해 대화에 붙여 주세요</h2>
    ${missing.length ? `<p class="hint">아직 안 고른 장면: ${esc(missing.join(", "))} — 「이전」으로 돌아가 고르세요.</p>` : ""}
    <div class="row"><button class="b main" id="copy" type="button">판정 문장 복사</button><span class="hint" id="ok"></span></div>
    <textarea id="out" readonly></textarea>`));
  const ta = document.getElementById("out"), text = () => `판정 task 371 단계 ${STAGE}\n` + JSON.stringify(verdict());
  ta.value = text();
  document.getElementById("copy").onclick = () => {
    if (!st.done) st.done = Date.now();
    save(); tick(); ta.value = text();
    navigator.clipboard.writeText(ta.value).then(() => { document.getElementById("ok").textContent = "복사됨"; })
      .catch(() => { ta.focus(); ta.select(); document.getElementById("ok").textContent = "자동 복사가 막혀 글을 선택해 두었습니다. 직접 복사하세요."; });
  };
}
function zoom(s, id) {
  const c = s.cands.find((x) => x.id === id), ov = document.getElementById("ov");
  ov.innerHTML = `<div class="row" style="justify-content:space-between"><b>후보 ${c.label}</b><button class="b main" id="close" type="button">닫기</button></div>
    <img src="${IMGS[`${s.id}:${id}`]}" alt="후보 ${c.label} 전체">${view(s, c, "crop")}`;
  document.getElementById("close").onclick = () => { ov.hidden = true; };
  ov.hidden = false;
}
document.getElementById("prev").onclick = () => { st.i = Math.max(0, st.i - 1); save(); render(); };
document.getElementById("next").onclick = () => { st.i = Math.min(SCREENS.length - 1, st.i + 1); save(); render(); };
if (st.i >= SCREENS.length) st.i = 0;
render(); setInterval(tick, 5000); tick();
</script>
"""
