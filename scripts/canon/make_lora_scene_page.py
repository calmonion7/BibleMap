#!/usr/bin/env python3
"""task 357 S4 — 인물 LoRA 장면 판정 페이지(폰용, 한 화면 한 문항). 353 페이지 틀(CSS)을 그대로 쓴다.
  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV make_lora_scene_page.py <353 페이지 HTML> <출력 HTML>
화면 A 6(인물 3 × L1/L2, 같은 시드 8쌍 + 353 음성 대조 3쌍을 고정 시드로 섞음) · B 3(L2 섞임) · C 3(화풍·뜻).
카드 폭 356 CSS px(DPR 3 화소), 확대·크롭 없음, 대상 머리 위 ▼. 그림은 한 번만 싣고 ▼는 CSS로 겹친다(16MB 한도).
머리 상자는 samples/lora-scene/metrics.json(S3)에서 읽는다. 쌍의 정체(시드·대조 여부)는 metrics의 `screens`에 적고 페이지에는 번호만."""
import argparse, base64, io, json, os, random

from PIL import Image

import params

CARD, DPR = 356, 3
HERE = os.path.dirname(os.path.abspath(__file__))
METRICS = os.path.join(HERE, "samples", "lora-scene", "metrics.json")
NAME = {"saul": "사울", "david": "다윗", "samuel": "사무엘"}
SC_NAME = {"gilgal": "길갈", "engedi": "엔게디", "ramah": "라마"}


def uri(im, w):
    """make_face_widen_page.uri와 같되 JPEG 품질 80 — 그림 83장(카드 1068px)이 16MB 한도에 들게(86이면 16.3MB)."""
    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "JPEG", quality=80)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def screens(m):
    """→ (화면 목록, 그림 id→경로, 화면 정체표). 쌍 순서는 params.LORA_SCENE_SHUFFLE_SEED로 섞는다."""
    imgs, ident, sc = {}, {}, []
    rnd = random.Random(params.LORA_SCENE_SHUFFLE_SEED)
    heads = m["heads"]   # 경로 → {인물: [x0,y0,x1,y1] 비율}

    def img(path):
        k = f"i{len(imgs)}" if path not in imgs.values() else next(a for a, b in imgs.items() if b == path)
        imgs[k] = path
        return k

    def card(path, who, cap):
        return {"img": img(path), "marks": [heads[path][w] for w in ([who] if isinstance(who, str) else who) if w in heads[path]], "cap": cap}

    for who, (a, b) in params.LORA_SCENE_PAIRS.items():
        for cond in ("L1", "L2"):
            f = (lambda k, s: m["scene_path"][cond][k][who if cond == "L1" else "both"][str(s)])
            pairs = [{"kind": "lora", "seed": s, "a": f(a, s), "b": f(b, s)} for s in params.LORA_SCENE_SEEDS]
            pairs += [{"kind": "control", "seed": c["seed"], "a": c["a"], "b": c["b"]} for c in m["controls"] if c["who"] == who]
            rnd.shuffle(pairs)
            sid = f"A-{who}-{cond}"
            ident[sid] = [{"n": n + 1, "kind": p["kind"], "seed": p["seed"]} for n, p in enumerate(pairs)]
            sc.append({"id": sid, "q": f"{NAME[who]} · 두 ▼가 같은 사람으로 읽히는 쌍을 누르세요",
                       "look": f"쌍마다 위는 {SC_NAME[a]}, 아래는 {SC_NAME[b]}입니다. 카드에 실제로 보이는 크기 그대로입니다(확대하지 마세요). "
                               f"▼ 표시된 {NAME[who]}만 보고, 같은 사람으로 읽히는 쌍을 모두 누르세요. 없으면 그대로 「표시 끝」.",
                       "items": [{"key": str(n + 1), "label": f"쌍 {n + 1}", "cards": [card(p["a"], who, SC_NAME[a]), card(p["b"], who, SC_NAME[b])]}
                                 for n, p in enumerate(pairs)], "mark": "✓ 같은 사람"})
    for key, (_, whos) in params.LORA_SCENE_SCENES.items():
        items = [{"key": f"s{s}", "label": f"시드 {s}", "cards": [card(m["scene_path"]["L2"][key]["both"][str(s)], whos, SC_NAME[key])]}
                 for s in params.LORA_SCENE_SEEDS]
        sc.append({"id": f"B-{key}", "q": f"{SC_NAME[key]} · 두 ▼ 인물이 서로 닮아 구별이 안 되는 그림을 누르세요",
                   "look": f"두 사람({' · '.join(NAME[w] for w in whos)})이 모두 나오는 그림입니다. 둘이 서로 닮아서 누가 누구인지 구별이 안 되면 누르세요.",
                   "items": items, "mark": "✓ 구별 안 됨"})
    for key, (_, whos) in params.LORA_SCENE_SCENES.items():
        items = [{"key": f"L1-{w}-s{s}", "label": f"{NAME[w]} 걸기 · {s}", "cards": [card(m["scene_path"]["L1"][key][w][str(s)], [], "")]}
                 for w in whos for s in params.LORA_SCENE_SEEDS]
        items += [{"key": f"L2-s{s}", "label": f"둘 다 걸기 · {s}", "cards": [card(m["scene_path"]["L2"][key]["both"][str(s)], [], "")]}
                  for s in params.LORA_SCENE_SEEDS]
        ref = {"img": img(m["refs"][key]), "marks": [], "cap": "기준"}
        sc.append({"id": f"C-{key}", "q": f"{SC_NAME[key]} · 연필 화풍이나 장면 뜻이 기준보다 크게 무너진 그림을 누르세요",
                   "look": "맨 위가 기준 그림입니다. 연필·수채 화풍이 크게 달라졌거나, 장면이 말하는 일이 안 보이게 된 그림을 누르세요. 얼굴은 보지 않아도 됩니다.",
                   "ref": ref, "items": items, "mark": "✗ 무너짐"})
    return sc, imgs, ident


JS = r"""
const ans = {};
try { Object.assign(ans, JSON.parse(localStorage.getItem("lora-scene-357") || "{}")) } catch (e) {}
let i = 0;
const m = document.getElementById("m"), o = document.getElementById("o");
function save() { try { localStorage.setItem("lora-scene-357", JSON.stringify(ans)) } catch (e) {} }
function sentence() {
  return "task 357 사람 판정\n" + SCREENS.map(s => `- [${s.id}] ${s.q} → ${ans[s.id] === undefined ? "(미답)" : (ans[s.id].length ? ans[s.id].join(", ") : "없음")}`).join("\n") + `\n(보여 준 그림: ${PICKED})`;
}
function cardHTML(c) {
  const mk = c.marks.map(b => `<span class="tri" style="left:${(b[0] + b[2]) / 2 * 100}%;top:${Math.max(b[1] * 100 - 1, 4)}%"></span>`).join("");
  return `<figure class="card"><div class="cw"><img src="${IMGS[c.img]}" alt="${c.cap}" style="width:356px">${mk}</div>${c.cap ? `<figcaption>${c.cap}</figcaption>` : ""}</figure>`;
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
  const ref = s.ref ? `<div class="refbox">${cardHTML(s.ref)}</div>` : "";
  m.innerHTML = `<div class="top"><span>질문</span><span>${i + 1}/${n}</span></div><h1>${s.q}</h1><p class="look">${s.look}</p>${ref}` +
    s.items.map(it => `<div class="item" data-k="${it.key}" role="button" tabindex="0"><div class="lab">${it.label}</div>${it.cards.map(cardHTML).join("")}</div>`).join("");
  const sel = new Set(ans[s.id] || []);
  const done = document.createElement("button");
  const sync = () => { m.querySelectorAll(".item").forEach(f => { const on = sel.has(f.dataset.k); f.setAttribute("aria-pressed", on); f.querySelector(".lab").textContent = f.querySelector(".lab").textContent.split(" ✓")[0].split(" ✗")[0] + (on ? " " + s.mark : "") });
    done.textContent = sel.size ? `표시 끝 (${sel.size})` : "표시 끝 (없음)" };
  m.querySelectorAll(".item").forEach(f => { f.onclick = () => { const k = f.dataset.k; sel.has(k) ? sel.delete(k) : sel.add(k); sync() } });
  o.innerHTML = ""; o.style.gridTemplateColumns = "1fr";
  done.onclick = () => { ans[s.id] = s.items.map(it => it.key).filter(k => sel.has(k)); save(); step(1) };
  o.appendChild(done); sync();
}
document.getElementById("back").onclick = () => step(-1);
document.getElementById("next").onclick = () => step(1);
render();
</script>
"""
CSS = """.item { border: 2px solid var(--line); border-radius: 8px; padding: 6px; display: grid; gap: 4px; justify-items: center; cursor: pointer }
.item[aria-pressed="true"] { border-color: var(--r1); background: color-mix(in srgb, var(--r1) 10%, transparent) }
.lab { justify-self: start; font-weight: 600; font-size: 14px }
.item[aria-pressed="true"] .lab { color: var(--r1) }
.cw { position: relative; width: 356px }
.cw img { display: block; max-width: none; outline: 1px solid var(--line) }
.tri { position: absolute; width: 0; height: 0; transform: translate(-50%, -100%);
  border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 8px solid #e0601e; filter: drop-shadow(0 0 1px #fff) }
.refbox { border: 2px dashed var(--line); border-radius: 8px; padding: 6px; display: grid; justify-items: center }
figure.card figcaption { text-align: left }
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src_html")
    ap.add_argument("dst")
    a = ap.parse_args()
    m = json.load(open(METRICS))
    html = open(a.src_html, encoding="utf-8").read()
    head = html[html.index("<title>"):html.index("<script>")].replace("<title>인물 정의 판정</title>", "<title>인물 LoRA 장면 판정</title>")
    head = head.replace("</style>", CSS + "</style>")
    sc, imgs, ident = screens(m)
    data = {k: uri(Image.open(p).convert("RGB"), CARD * DPR) for k, p in imgs.items()}
    picked = (f"LoRA v2 세기 {params.LORA_SCENE_SCALE} · L1 48 + L2 24 · 시드 {params.LORA_SCENE_SEEDS} · 음성 대조 353 시드 "
              f"{params.LORA_SCENE_CONTROL_SEEDS} · 카드 폭 356px · 기계 거르기 없음")
    page = (head + "<script>\nconst SCREENS = " + json.dumps(sc, ensure_ascii=False) + ";\nconst IMGS = " + json.dumps(data)
            + ";\nconst PICKED = " + json.dumps(picked, ensure_ascii=False) + ";\n" + JS + "\n</body></html>\n")
    open(a.dst, "w", encoding="utf-8").write(page)
    m["screens"] = ident
    json.dump(m, open(METRICS, "w"), ensure_ascii=False, indent=1)
    print(a.dst, f"{len(page) / 1e6:.2f}MB, 화면 {len(sc)}, 그림 {len(imgs)}")


if __name__ == "__main__":
    main()
