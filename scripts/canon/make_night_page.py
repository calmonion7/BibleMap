#!/usr/bin/env python3
"""task#368 S2 — 밤샘 후보 검증 페이지: 장면마다 명세 칸별 문항(한 화면 한 문항, 「이 항목이 틀린 시드를 누르세요」) → 마지막 고르기.

  python3 make_night_page.py     # samples/night-pilot/metrics.json → ~/.local/biblemap-imggen/pages/night-pick.html
  (task 369: run_night.py page --set whole-fix → main(metrics, 장면, 369) — 후보 편집이 없으면 바탕만 싣고 「바탕으로 고르기」만)

문항 id = 명세 칸 경로(moment · background[i] · crowds · figures[i].identity|pose|prop|facing · guard, notes/NIGHT-PILOT.md 고정 절).
그림은 시드마다 편집본·바탕을 한 번씩만 싣고 크롭은 CSS로 자른다(16MB 안). 「판정 문장 복사」는 JSON 한 덩이."""
import base64, io, json, os, random

from PIL import Image

import params
import derive_scene as D

HERE = os.path.dirname(os.path.abspath(__file__))
METRICS = os.path.join(HERE, "samples", "night-pilot", "metrics.json")
PAGES = os.path.expanduser("~/.local/biblemap-imggen/pages")
DST = {368: "night-pick.html", 369: "whole-fix-pick.html", 370: "whole-wide-pick.html", 372: "jabesh-crowd-pick.html"}
# 고르기 화면 덧말(과제별) — task 372: 암몬 무리는 다음 단계 편집 대상이라 「무리 말고 다 맞는 바탕」을 고른다(계획 결정 6)
PICK_NOTE = {372: "암몬 무리(crowds[1])는 다음 단계에서 고른 장에만 편집합니다. 암몬 무리 말고 다 맞는 바탕을 고르세요."}
LIMIT = 15.5e6
PROP_KO = {"a spear": "창", "a small harp": "작은 수금", "a robe corner": "겉옷자락", "a plain traveling cloak": "수수한 나그네 겉옷",
           "a torn robe corner": "찢어진 겉옷자락", "a wooden staff": "나무 지팡이", "a sword": "칼",
           "a cloth-wrapped sword": "보자기에 싼 칼", "a wooden gate post": "나무 성문 기둥", "a fold of his robe": "겉옷 자락",
           "a siege spear": "공성 창", "the hem of his ephod": "에봇 자락"}
FACING_KO = {"left": "화면 왼쪽을 향한다", "right": "화면 오른쪽을 향한다"}
NAME = {"saul": "사울", "david": "다윗", "samuel": "사무엘", "david-boy": "소년 다윗", "ahimelech": "아히멜렉", "achish": "아기스",
        "nahash": "나하스", "doeg": "도엑"}
# task 370(whole-wide): 방향 문항은 사람이 본 축 「누구와 마주 보는가(얼굴·상체)」로, 설명은 한 장 모드 gaze에서(계획 결정 4)
SCREEN_KO = {"right": "화면 오른쪽을 향함", "left": "화면 왼쪽을 향함", "viewer": "화면 앞을 향함", "away": "등을 보임"}
TREAT = ("moment", ".pose", ".facing")   # 처치 칸 — 판 묶음(대조)은 이 문항만 묻는다
GUARD = "위에서 묻지 않은 결함 — 손가락 수, 두 겹·덧붙은 인물, 종이 테두리·액자, 글자"


def uri(im, w, q):
    if im.width != w:
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    b = io.BytesIO()
    im.convert("RGB").save(b, "JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def fit(box, ar, W, H, pad):
    """상자를 pad만큼 넓히고 가로/세로 = ar로 맞춘 뒤 그림 안으로 민다 → 비율 [x, y, w, h]."""
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w, h = (x1 - x0) * (1 + pad), (y1 - y0) * (1 + pad)
    w, h = (h * ar, h) if w / h < ar else (w, w / ar)
    w, h = min(w, W), min(h, H)
    x, y = min(max(0, cx - w / 2), W - w), min(max(0, cy - h / 2), H - h)
    return [round(x / W, 4), round(y / H, 4), round(w / W, 4), round(h / H, 4)]


def josa(word, pair):
    """받침 유무로 조사 고르기 — pair = ("이", "가") · ("과", "와")."""
    c = ord(word[-1]) - 0xAC00
    return word + (pair[0] if 0 <= c < 11172 and c % 28 else pair[1])


def treat(qid):
    return qid == "moment" or qid.endswith(TREAT[1:])


def plate_label(sid):
    """장면마다 판 묶음이 「묶음 가」인지 「묶음 나」인지 — WHOLE_WIDE_SHUFFLE_SEED와 장면 id로 정해진다(metrics plate.label)."""
    return random.Random(f"{params.WHOLE_WIDE_SHUFFLE_SEED}:{sid}").choice(["가", "나"])


def facing_q(f):
    """→ (질문, 설명) — 한 장 모드 gaze가 대상 인물이면 「{대상}과 마주 봄 · 화면 방향」, 문구 객체면 그 ko."""
    nm, g = NAME.get(f["cast"], f["cast"]), f["gaze"]
    what = g["ko"] if isinstance(g, dict) else f"{josa(NAME.get(g, g), ('과', '와'))} 마주 봄 · {SCREEN_KO[f['screen_facing']]}"
    return f"{josa(nm, ('이', '가'))} 누구와 마주 보는가(얼굴·상체)가 틀린 그림", what


def pair_plate(qs, pqs, label):
    """칸 묶음 문항 qs + 판 묶음 문항 pqs → 처치 칸 문항마다 두 묶음을 잇달아(판이 label 쪽). 나머지 문항은 칸 묶음만."""
    by = {q["id"]: q for q in pqs}
    other = "나" if label == "가" else "가"
    out = []
    for q in qs:
        if not treat(q["id"]):
            out.append(q)
            continue
        pair = [{**q, "grp": "whole", "lab": f"묶음 {other}"}, {**by[q["id"]], "grp": "plate", "lab": f"묶음 {label}"}]
        out += pair[::-1] if label == "가" else pair
    return out


def questions(spec, sc, wide=False):
    W, H = Image.open(sc["seeds"][0]["base"]).size
    full = lambda: {"kind": "full"}
    qs = [{"id": "moment", "field": "moment", "q": "장면 뜻이 틀린 그림", "what": spec["moment"]["why"], "verse": spec["moment"]["verse"], **full()}]
    for i, b in enumerate(spec.get("background") or []):
        qs.append({"id": f"background[{i}]", "field": f"background[{i}]", "q": "배경이 틀린 그림", "what": b["what"], "verse": b["verse"], **full()})
    cs = spec.get("crowds") or []
    for i, c in enumerate(cs):   # 무리가 둘 이상이면 문항 id도 칸 경로 crowds[i](task 372) — 하나면 368~370 그대로 「crowds」
        cid = f"crowds[{i}]" if len(cs) > 1 else "crowds"
        qs.append({"id": cid, "field": cid, "q": "무리가 틀린 그림", "what": c["what"], "verse": c["verse"], **full()})
    for i, f in enumerate(spec["figures"]):
        who, nm = f["cast"], NAME.get(f["cast"], f["cast"])
        head = {str(x["seed"]): fit(x["boxes"][who]["head"], 1, W, H, 0.5) for x in sc["seeds"]}
        body = {str(x["seed"]): fit(x["boxes"][who]["body"], 0.75, W, H, 0.15) for x in sc["seeds"]}
        crop = {"kind": "crop", "crop": body, "ar": 0.75}
        if os.path.exists(os.path.join(HERE, "frozen", f"{who}.png")):
            qs.append({"id": f"figures[{i}].identity", "field": f"figures[{i}] 정본", "who": who, "q": f"{josa(nm, ('이', '가')) if wide else nm + '가'} 정본과 다른 사람으로 보이는 그림",
                       "what": "얼굴·머리·수염·나이대만 봅니다(옷은 빼고).", "verse": f["role"], "kind": "crop", "crop": head, "ar": 1, "canon": who})
        qs.append({"id": f"figures[{i}].pose", "field": f"figures[{i}].pose", "who": who, "q": f"{nm}의 자세가 틀린 그림",
                   "what": f["pose"], "verse": f["verse"], **crop})
        qs.append({"id": f"figures[{i}].prop", "field": f"figures[{i}].prop", "who": who, "q": f"{nm}의 지물이 틀린 그림",
                   "what": f"{PROP_KO[f['prop']]} ({f['prop']})", "verse": f["verse"], **crop})
        fq, fw = facing_q(f) if wide else (f"{nm}의 방향이 틀린 그림", f"{FACING_KO[f['facing']]} ({f['facing']})")
        qs.append({"id": f"figures[{i}].facing", "field": f"figures[{i}].facing", "who": who, "q": fq,
                   "what": fw, "verse": f["verse"], **crop})
    qs.append({"id": "guard", "field": "가드", "q": "그 밖에 깨진 곳이 있는 그림", "what": GUARD, "verse": "", **full()})
    return qs


def build(m, q, sids, task=None):
    data, scenes = {}, []
    for sid in sids:
        sc = m["scenes"].get(sid)
        if not sc or not sc["seeds"]:
            continue
        spec = D.load(sid)
        edited = any(x["edits"] for x in sc["seeds"])   # task 369: 후보 편집 없음 → 바탕을 「:e」 자리에 싣는다
        seeds = [x for x in sc["seeds"] if not edited or len(x["edits"]) == len(sc["who"])]
        for x in seeds:
            k = f"{sid}:{x['seed']}"
            data[k + ":e"] = uri(Image.open(x["edits"][sc["who"][-1]] if edited else x["base"]), 1216, q)
            if edited:
                data[k + ":b"] = uri(Image.open(x["base"]), 800, q - 6)
        wide = "plate" in sc   # task 370: 판 묶음(대조) — 처치 칸 문항만 같은 문구로 잇달아
        qs = questions(spec, {**sc, "seeds": seeds}, wide)
        if wide:
            for x in sc["plate"]["seeds"]:
                data[f"{sid}:{x['seed']}:p"] = uri(Image.open(x["base"]), 1216, q)
            qs = pair_plate(qs, [p for p in questions(spec, {**sc, "seeds": sc["plate"]["seeds"]}, wide) if treat(p["id"])],
                            sc["plate"]["label"])
        scenes.append({"id": sid, "title": spec["title"], "range": spec["verses"]["range"], "note": PICK_NOTE.get(task, ""),
                       "edited": [NAME[w] for w in sc["who"]] if edited else [], "seeds": [x["seed"] for x in seeds], "qs": qs})
    for who in NAME:
        p = os.path.join(HERE, "frozen", f"{who}.png")
        if os.path.exists(p):
            data["canon:" + who] = uri(Image.open(p), 360, 86)
    return scenes, data


def main(metrics=METRICS, sids=None, task=368):
    m = json.load(open(metrics))
    sids = sids or list(params.NIGHT_SCENES)
    title = "밤샘 장면 고르기" if task == 368 else f"장면 고르기 {task}"
    for q in (84, 78, 72, 66, 60):
        scenes, data = build(m, q, sids, task)
        page = (PAGE.replace("/*SCENES*/[]", json.dumps(scenes, ensure_ascii=False)).replace("/*IMGS*/{}", json.dumps(data))
                .replace("/*TASK*/368", str(task)).replace("<title>밤샘 장면 고르기</title>", f"<title>{title}</title>"))
        if len(page) <= LIMIT:
            break
    dst = os.path.join(PAGES, DST[task])
    os.makedirs(PAGES, exist_ok=True)
    open(dst, "w", encoding="utf-8").write(page)
    n = sum(len(s["qs"]) + 1 for s in scenes)
    print(f"[NightPage] {dst} {len(page) / 1e6:.2f}MB · JPEG q{q} · 장면 {len(scenes)} · 화면 {n}", flush=True)


PAGE = r"""<title>밤샘 장면 고르기</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* 레이아웃: 폰 한 화면 = 문항 하나. 위 진행 띠 · 질문 · 시드 바둑판(2열) · 아래 고정 단추 줄 */
:root {
  --bg: #f3f4f2; --panel: #ffffff; --fg: #1d2421; --muted: #5d6a64; --line: #d5dad6;
  --wrong: #c2372b; --wrong-bg: #fbe4e1; --pick: #24508a; --pick-bg: #e1eaf6;
  --sans: "IBM Plex Sans KR", "Apple SD Gothic Neo", "Noto Sans KR", system-ui, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #161a18; --panel: #202623; --fg: #e6ebe8; --muted: #9aa7a1; --line: #343c38;
  --wrong: #ff7a6b; --wrong-bg: #4a221e; --pick: #8db4ea; --pick-bg: #1f3048; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #161a18; --panel: #202623; --fg: #e6ebe8; --muted: #9aa7a1; --line: #343c38;
  --wrong: #ff7a6b; --wrong-bg: #4a221e; --pick: #8db4ea; --pick-bg: #1f3048; color-scheme: dark }
body { background: var(--bg); color: var(--fg); font: 15px/1.5 var(--sans); }
[hidden] { display: none !important; }
main { max-width: 720px; margin: 0 auto; padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 12px 96px; display: grid; gap: 12px; }
.bar { font: 500 12px/1.4 var(--mono); color: var(--muted); display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap;
  letter-spacing: .02em; font-variant-numeric: tabular-nums; }
h1 { font-size: 15px; margin: 0; font-weight: 600; color: var(--muted); }
h2 { font-size: 21px; line-height: 1.3; margin: 0; text-wrap: balance; }
.what { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 10px 12px; display: grid; gap: 4px; }
.what p { margin: 0; }
.src { font: 12px/1.4 var(--mono); color: var(--muted); }
.hint { font-size: 13px; color: var(--muted); margin: 0; }
.grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.grid.full { grid-template-columns: minmax(0, 1fr); }
.card { position: relative; border: 2px solid var(--line); border-radius: 6px; overflow: hidden; background: var(--panel);
  padding: 0; cursor: pointer; display: block; width: 100%; color: inherit; font: inherit; text-align: left; }
.card:focus-visible { outline: 3px solid var(--pick); outline-offset: 2px; }
.card.on { border-color: var(--wrong); }
.frame { position: relative; overflow: hidden; width: 100%; }
.frame img { position: absolute; max-width: none; display: block; }
.tag { position: absolute; left: 6px; top: 6px; font: 500 12px/1 var(--mono); background: var(--panel); color: var(--fg);
  padding: 4px 6px; border-radius: 4px; }
.card.on .tag { background: var(--wrong); color: var(--panel); }
.card.on::after { content: "틀림"; position: absolute; right: 6px; top: 6px; font-size: 12px; font-weight: 600; color: var(--wrong);
  background: var(--wrong-bg); padding: 3px 6px; border-radius: 4px; }
.zoom { position: absolute; right: 6px; bottom: 6px; font-size: 12px; border: 1px solid var(--line); background: var(--panel);
  color: var(--fg); border-radius: 4px; padding: 3px 8px; cursor: pointer; }
.canon { display: flex; gap: 12px; align-items: center; }
.canon img { width: 96px; border-radius: 6px; border: 1px solid var(--line); }
.row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
input[type=text], textarea { width: 100%; font: inherit; color: var(--fg); background: var(--panel); border: 1px solid var(--line);
  border-radius: 6px; padding: 8px 10px; box-sizing: border-box; }
textarea { min-height: 160px; font: 12px/1.4 var(--mono); }
button.b { font: 600 15px var(--sans); border-radius: 8px; padding: 10px 14px; border: 1px solid var(--line); background: var(--panel);
  color: var(--fg); cursor: pointer; }
button.b.main { background: var(--pick); border-color: var(--pick); color: var(--panel); }
button.b.no { color: var(--wrong); border-color: var(--wrong); }
button.b:focus-visible, .zoom:focus-visible { outline: 3px solid var(--pick); outline-offset: 2px; }
footer { position: fixed; left: 0; right: 0; bottom: 0; background: var(--panel); border-top: 1px solid var(--line);
  padding-block: 10px calc(10px + env(safe-area-inset-bottom, 0px));
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
footer .row { max-width: 720px; margin: 0 auto; justify-content: space-between; }
.pick { display: grid; gap: 8px; border: 1px solid var(--line); border-radius: 8px; padding: 8px; background: var(--panel); }
.pick .meta { display: flex; justify-content: space-between; gap: 8px; font: 13px var(--mono); color: var(--muted); flex-wrap: wrap; }
.pick .meta b { color: var(--fg); }
.ov { position: fixed; inset: 0; background: var(--bg); z-index: 20; overflow: auto; display: grid; gap: 10px; align-content: start;
  padding-block: calc(12px + env(safe-area-inset-top, 0px)) 24px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
.ov img { width: 100%; border-radius: 6px; }
@media (prefers-reduced-motion: no-preference) { .card { transition: border-color .12s; } }
</style>
<main id="app"></main>
<footer><div class="row"><button class="b" id="prev" type="button">이전</button><span class="bar" id="clock"></span><button class="b main" id="next" type="button">다음</button></div></footer>
<div class="ov" id="ov" hidden></div>
<script>
const SCENES = /*SCENES*/[];
const IMGS = /*IMGS*/{};
const TASK = /*TASK*/368;
const KEY = "night-pick-" + TASK;
let st = { i: 0, ans: {}, t0: null, sceneT: {}, done: null };
try { const s = JSON.parse(localStorage.getItem(KEY) || "null"); if (s && s.ans) st = s; } catch (e) { console.warn("[NightPick] 저장본 읽기 실패", e); }
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) { console.warn("[NightPick] 저장 실패", e); } };
const SCREENS = [];
SCENES.forEach((s, k) => { s.qs.forEach((q, j) => SCREENS.push({ s, k, q, j })); SCREENS.push({ s, k, pick: true }); });
SCREENS.push({ end: true });
const $ = (h) => { const d = document.createElement("div"); d.innerHTML = h; return d; };
const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const A = (sid) => (st.ans[sid] = st.ans[sid] || { items: {}, pick: null });
const item = (sid, id) => (A(sid).items[id] = A(sid).items[id] || { wrong: [], unsure: false, memo: "" });
const ik = (q) => (q.grp === "plate" ? "plate:" : "") + q.id;   // task 370: 판 묶음 답은 따로(고르기 틀림 수에 안 섞음)
const ims = (q) => (q && q.grp === "plate" ? "p" : "e");

function img(key, crop, ar) {
  if (!crop) return `<div class="frame" style="aspect-ratio:1216/640"><img src="${IMGS[key]}" alt="" style="width:100%;left:0;top:0"></div>`;
  const [x, y, w, h] = crop;
  return `<div class="frame" style="aspect-ratio:${ar}"><img src="${IMGS[key]}" alt="" style="width:${100 / w}%;left:${-x / w * 100}%;top:${-y / h * 100}%"></div>`;
}
function tick() {
  const now = Date.now(), m = st.t0 ? ((st.done || now) - st.t0) / 60000 : 0;
  document.getElementById("clock").textContent = `${m.toFixed(1)}분`;
}
function enterScene(sid) { const t = st.sceneT[sid] = st.sceneT[sid] || { start: null, end: null }; if (!t.start) t.start = Date.now(); }
function render() {
  if (!st.t0) st.t0 = Date.now();
  const sc = SCREENS[st.i], app = document.getElementById("app");
  document.getElementById("prev").disabled = st.i === 0;
  document.getElementById("next").hidden = !!(sc.end || sc.pick);
  if (sc.end) return renderEnd(app);
  enterScene(sc.s.id);
  const head = `<div class="bar"><span>장면 ${sc.k + 1}/${SCENES.length}</span><span>${sc.pick ? "고르기" : `문항 ${sc.j + 1}/${sc.s.qs.length}${sc.q.lab ? " · " + sc.q.lab : ""}`}</span></div>
    <h1>${esc(sc.s.title)} · ${esc(sc.s.range)}</h1>`;
  if (sc.pick) return renderPick(app, sc, head);
  const q = sc.q, it = item(sc.s.id, ik(q));
  const canon = q.canon ? `<div class="canon"><img src="${IMGS["canon:" + q.canon]}" alt="정본 초상"><p class="hint">왼쪽이 정본 초상입니다. 같은 사람으로 안 보이는 시드를 누르세요.</p></div>` : "";
  const cards = sc.s.seeds.map((s) => {
    const k = `${sc.s.id}:${s}:${ims(q)}`;
    return `<button type="button" class="card${it.wrong.includes(s) ? " on" : ""}" data-s="${s}">${img(k, q.crop && q.crop[s], q.ar)}<span class="tag">s${s}</span><span class="zoom" data-z="${s}" role="button" tabindex="0">크게</span></button>`;
  }).join("");
  app.innerHTML = "";
  app.append($(`${head}<h2>${esc(q.q)}을 누르세요</h2>
    <div class="what"><p>${esc(q.what)}</p><span class="src">${esc(q.field)}${q.verse ? " · " + esc(q.verse) : ""}</span></div>
    ${q.lab ? `<p class="hint"><b>${esc(q.lab)}</b> — 같은 질문을 다른 묶음 그림 8장으로 한 번 더 묻습니다.</p>` : ""}${canon}<p class="hint">이 항목이 틀린 시드만 누르세요. 기본은 모두 맞음이고, ${sc.s.edited.length ? "편집본" : "바탕"}을 보여 줍니다.</p>
    <div class="grid${q.kind === "full" ? " full" : ""}">${cards}</div>
    <label class="row"><input type="checkbox" id="unsure" ${it.unsure ? "checked" : ""}> 모르겠음</label>
    <input type="text" id="memo" placeholder="한 줄 메모(선택)" value="${esc(it.memo)}">`));
  app.querySelectorAll(".card").forEach((c) => c.addEventListener("click", (ev) => {
    const s = +c.dataset.s;
    if (ev.target.dataset.z) return zoom(sc.s.id, s, ims(q));
    it.wrong = it.wrong.includes(s) ? it.wrong.filter((x) => x !== s) : [...it.wrong, s].sort((a, b) => a - b);
    c.classList.toggle("on"); save();
  }));
  document.getElementById("unsure").onchange = (e) => { it.unsure = e.target.checked; save(); };
  document.getElementById("memo").oninput = (e) => { it.memo = e.target.value; save(); };
  save(); window.scrollTo(0, 0);
}
function wrongCount(sid, s) { return Object.entries(A(sid).items).filter(([k, v]) => !k.startsWith("plate:") && v.wrong.includes(s)).length; }
function renderPick(app, sc, head) {
  const sid = sc.s.id, ed = sc.s.edited.length > 0, seeds = [...sc.s.seeds].sort((a, b) => wrongCount(sid, a) - wrongCount(sid, b));
  const cur = A(sid).pick;
  app.innerHTML = "";
  app.append($(`${head}<h2>이 장면에 쓸 그림 하나를 고르세요</h2>
    ${sc.s.note ? `<p class="hint"><b>${esc(sc.s.note)}</b></p>` : ""}<p class="hint">틀림 표시가 적은 순서입니다. ${ed ? `그림을 누르면 편집본(${esc(sc.s.edited.join("·"))} 정본 편집)과 바탕이 바뀝니다.` : "바탕 그림입니다. 고른 장에만 정본 편집을 건 뒤 따로 확인합니다."}</p>
    ${seeds.map((s) => `<div class="pick"><div class="meta"><b>s${s}</b><span>틀림 표시 ${wrongCount(sid, s)}개</span><span id="lab${s}">${ed ? "편집본" : "바탕"}</span></div>
      <button type="button" class="card" ${ed ? `data-flip="${s}"` : ""}>${img(`${sid}:${s}:e`)}</button>
      <div class="row">${ed ? `<button class="b${cur && cur.seed === s && cur.kind === "edit" ? " main" : ""}" data-p="${s}" data-k="edit" type="button">편집본으로 고르기</button>` : ""}
      <button class="b${cur && cur.seed === s && cur.kind === "base" ? " main" : ""}" data-p="${s}" data-k="base" type="button">바탕으로 고르기</button></div></div>`).join("")}
    <div class="pick"><p class="hint">쓸 그림이 없으면 이유를 적고 「없음」을 누르세요.</p>
      <input type="text" id="why" placeholder="없음 이유 한 줄" value="${esc(cur && cur.answer === "없음" ? cur.memo : "")}">
      <button class="b no" data-none="1" type="button">없음</button></div>`));
  app.querySelectorAll("[data-flip]").forEach((b) => b.onclick = () => {
    const s = b.dataset.flip, im = b.querySelector("img"), lab = document.getElementById("lab" + s), base = lab.textContent === "편집본";
    im.src = IMGS[`${sid}:${s}:${base ? "b" : "e"}`]; lab.textContent = base ? "바탕" : "편집본";
  });
  const done = (p) => { A(sid).pick = p; st.sceneT[sid].end = Date.now(); st.i++; save(); render(); };
  app.querySelectorAll("[data-p]").forEach((b) => b.onclick = () => {
    const s = +b.dataset.p, k = b.dataset.k;
    done({ answer: `s${s} ${k === "edit" ? "편집본" : "바탕"}`, seed: s, kind: k });
  });
  app.querySelector("[data-none]").onclick = () => done({ answer: "없음", seed: null, kind: null, memo: document.getElementById("why").value });
  save(); window.scrollTo(0, 0);
}
function verdict() {
  const now = st.done || Date.now(), out = { task: TASK, human_minutes: +((now - st.t0) / 60000).toFixed(2), scenes: {} };
  SCENES.forEach((s) => {
    const a = A(s.id), t = st.sceneT[s.id] || {};
    const items = {};
    const plate = {};
    s.qs.forEach((q) => { (q.grp === "plate" ? plate : items)[q.id] = item(s.id, ik(q)); });
    out.scenes[s.id] = { minutes: t.start && t.end ? +((t.end - t.start) / 60000).toFixed(2) : null, items, pick: a.pick };
    if (Object.keys(plate).length) out.scenes[s.id].plate_items = plate;
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
  const ta = document.getElementById("out");
  ta.value = `판정 task ${TASK}\n` + JSON.stringify(verdict());
  document.getElementById("copy").onclick = () => {
    if (!st.done) st.done = Date.now();
    save(); tick();
    ta.value = `판정 task ${TASK}\n` + JSON.stringify(verdict());
    navigator.clipboard.writeText(ta.value).then(() => { document.getElementById("ok").textContent = "복사됨"; })
      .catch(() => { ta.focus(); ta.select(); document.getElementById("ok").textContent = "자동 복사가 막혀 글을 선택해 두었습니다. 직접 복사하세요."; });
  };
}
function zoom(sid, s, g) {
  const ov = document.getElementById("ov");
  let base = false;
  const ed = g !== "p" && !!IMGS[`${sid}:${s}:b`];   // 후보 편집이 없으면(task 369) 「:e」 자리가 바탕이고 전환이 없다
  const draw = () => {
    ov.innerHTML = `<div class="row" style="justify-content:space-between"><b>s${s} · ${base || !ed ? "바탕" : "편집본"}</b>
      <span class="row">${ed ? `<button class="b" id="flip" type="button">${base ? "편집본 보기" : "바탕 보기"}</button>` : ""}<button class="b main" id="close" type="button">닫기</button></span></div>
      <img src="${IMGS[`${sid}:${s}:${base ? "b" : g || "e"}`]}" alt="s${s}">`;
    if (ed) document.getElementById("flip").onclick = () => { base = !base; draw(); };
    document.getElementById("close").onclick = () => { ov.hidden = true; };
  };
  draw(); ov.hidden = false;
}
document.getElementById("prev").onclick = () => { st.i = Math.max(0, st.i - 1); save(); render(); };
document.getElementById("next").onclick = () => { st.i = Math.min(SCREENS.length - 1, st.i + 1); save(); render(); };
if (st.i >= SCREENS.length) st.i = 0;
render(); setInterval(tick, 5000); tick();
</script>
"""

if __name__ == "__main__":
    main()
