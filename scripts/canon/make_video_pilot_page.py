#!/usr/bin/env python3
"""task 354 S2 — 영상 파일럿 사람 판정 페이지(한 화면 한 질문, 폰 카드 폭 재생, 기계 수치 숨김).
  python3 make_video_pilot_page.py [출력 HTML]   (기본 ~/.local/biblemap-imggen/pages/video-pilot.html)
모델 이름은 가린다 — 클립은 섞은 순서의 「영상 1~8」, 마지막 화면은 묶음 A/B. 짝은 복사되는 판정 문장에만 나온다.
문항: 화풍(8) → 얼굴(8, 머리 확대 영상 곁들임) → 쓸 만한 모델(1). 기준 = 승인본 정지 그림(움직임 없는 대조)."""
import base64, json, os, random, subprocess, sys, tempfile

import gen_video_pilot as V

HEADS = {"gilgal": {"사무엘": (205, 228), "사울": (1044, 165)},   # 1280×704 입력 좌표의 머리 중심
         "engedi": {"다윗": (470, 290), "사울": (990, 300)}}
BOX = 280
NAME = {"gilgal": "길갈", "engedi": "엔게디"}
STYLE = ["남는다", "사진처럼 변한다", "모르겠음"]
FACE = ["괜찮다", "무너진다", "모르겠음"]


def enc(src, vf):
    with tempfile.NamedTemporaryFile(suffix=".mp4") as t:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vf", vf, "-an", "-c:v", "libx264", "-crf", "27",
                        "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart", t.name], check=True)
        return "data:video/mp4;base64," + base64.b64encode(open(t.name, "rb").read()).decode()


def still(scene):
    with tempfile.NamedTemporaryFile(suffix=".jpg") as t:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", V.input_path(scene), "-vf", "scale=720:-2", "-q:v", "4", t.name], check=True)
        return "data:image/jpeg;base64," + base64.b64encode(open(t.name, "rb").read()).decode()


def build():
    clips = [c for c in V.clips() if os.path.exists(V.clip_path(*c))]
    rng = random.Random(354)
    rng.shuffle(clips)
    models = ["wan", "ltx"]
    rng.shuffle(models)
    group = dict(zip(models, "AB"))
    media, items = {}, []
    for scene in V.SCENES:
        media[f"still-{scene}"] = still(scene)
    for n, (m, sc, sd) in enumerate(clips, 1):
        src, key = V.clip_path(m, sc, sd), f"{m}-{sc}-s{sd}"
        media[f"v{n}"] = enc(src, "scale=720:-2")
        for who, (x, y) in HEADS[sc].items():
            x0 = min(max(x - BOX // 2, 0), V.W - BOX)
            y0 = min(max(y - BOX // 2, 0), V.H - BOX)
            media[f"v{n}-{who}"] = enc(src, f"crop={BOX}:{BOX}:{x0}:{y0}")
        items.append({"n": n, "key": key, "scene": sc, "group": group[m], "heads": list(HEADS[sc])})
    screens = []
    for it in items:
        screens.append({"id": f"style-{it['n']}", "kind": "style", "n": it["n"], "scene": it["scene"],
                        "q": f"영상 {it['n']} · 연필 화풍이 끝까지 남나?",
                        "look": f"{NAME[it['scene']]} 승인본(위, 정지 그림)이 목표 화풍입니다. 영상 끝까지 연필 선·종이 질감이 남는지, "
                                "아니면 매끈한 사진·3D처럼 변하는지 보세요. 영상은 반복 재생됩니다.",
                        "opts": STYLE})
    for it in items:
        screens.append({"id": f"face-{it['n']}", "kind": "face", "n": it["n"], "scene": it["scene"], "heads": it["heads"],
                        "q": f"영상 {it['n']} · 얼굴이 무너지나?",
                        "look": "아래 머리 확대 영상을 보세요. 눈·코·입이 녹거나 뒤틀리거나, 다른 사람 얼굴로 바뀌면 「무너진다」입니다. "
                                "움직이면서 표정이 조금 바뀌는 것은 괜찮습니다.",
                        "opts": FACE})
    screens.append({"id": "final", "kind": "final",
                    "q": "투어 카드 영상으로 쓸 만한 묶음은?",
                    "look": "묶음 A와 B는 서로 다른 모델입니다(각 4개 — 두 장면 × 시드 2). 지금 카드의 애니메이션을 이 영상으로 바꾼다면 어느 쪽을 쓰겠는지 고르세요.",
                    "groups": {g: [it["n"] for it in items if it["group"] == g] for g in "AB"},
                    "opts": ["A", "B", "둘 다 아님", "모르겠음"]})
    key = {it["n"]: it["key"] for it in items}
    return screens, media, key, {v: k for k, v in group.items()}


PAGE = """<title>영상 파일럿 판정</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;600&display=swap">
<style>
/* 한 화면 한 질문: 질문 → 볼 것 한 줄 → 기준(정지 그림) → 영상(카드 폭) → 고정 답 단추. 폰 세로 기준 */
:root { --bg: #f6f5f2; --fg: #22201c; --mu: #6b665d; --line: #d9d5cc; --a: #b4532a; --b: #2c6e8f;
  --pick: #22201c; --pick-fg: #f6f5f2; --card: #ffffff; --sans: "IBM Plex Sans KR", system-ui, sans-serif }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg: #1a1916; --fg: #ece8e0; --mu: #a39d92;
  --line: #3a3732; --a: #e0875f; --b: #6fb3d4; --pick: #ece8e0; --pick-fg: #1a1916; --card: #24221e; color-scheme: dark } }
:root[data-theme="dark"] { --bg: #1a1916; --fg: #ece8e0; --mu: #a39d92; --line: #3a3732; --a: #e0875f; --b: #6fb3d4;
  --pick: #ece8e0; --pick-fg: #1a1916; --card: #24221e; color-scheme: dark }
* { box-sizing: border-box }
body { background: var(--bg); color: var(--fg); font: 16px/1.5 var(--sans); margin: 0 }
main { max-width: 760px; margin-inline: auto; padding-block: 16px 150px; padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px)); display: grid; gap: 12px }
.top { display: flex; justify-content: space-between; color: var(--mu); font-size: 14px; font-variant-numeric: tabular-nums }
h1 { font-size: 21px; line-height: 1.3; margin: 0; text-wrap: balance }
h3 { font-size: 15px; margin: 4px 0 0; color: var(--mu); font-weight: 600 }
.look { margin: 0; color: var(--mu) }
figure { margin: 0; min-width: 0; width: min(100%, 360px) }
figure img, figure video { width: 100%; height: auto; display: block; border-radius: 4px; border: 3px solid var(--line); background: var(--card) }
figure.clip video { border-color: var(--fg) }
figure.a video { border-color: var(--a) } figure.b video { border-color: var(--b) }
figcaption { font-size: 13px; color: var(--mu); padding-top: 2px }
.heads { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; width: min(100%, 360px) }
.heads figure { width: 100% }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px }
.grid figure { width: 100% }
.bar { position: fixed; left: 0; right: 0; bottom: 0; background: var(--bg); border-top: 1px solid var(--line);
  padding-block: 10px calc(10px + env(safe-area-inset-bottom, 0px)); padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px)) }
.opts { max-width: 760px; margin-inline: auto; display: grid; grid-template-columns: 1fr 1fr; gap: 8px }
button { font: inherit; min-height: 48px; border-radius: 8px; border: 1px solid var(--line); background: var(--card); color: var(--fg); cursor: pointer; padding: 6px 10px }
button[aria-pressed="true"] { background: var(--pick); color: var(--pick-fg); border-color: var(--pick) }
button:focus-visible { outline: 3px solid var(--b); outline-offset: 2px }
.nav { max-width: 760px; margin: 8px auto 0; display: flex; justify-content: space-between }
.nav button { min-height: 40px; background: transparent }
pre { white-space: pre-wrap; background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 12px; margin: 0; font-size: 14px }
</style>
<main id="m"></main>
<div class="bar"><div class="opts" id="o"></div><div class="nav"><button id="back">← 이전</button><button id="next">다음 →</button></div></div>
<script>
const SCREENS = __SCREENS__;
const MEDIA = __MEDIA__;
const KEY = __KEY__;
const GROUP = __GROUP__;
const NAME = {gilgal: "길갈", engedi: "엔게디"};
const STORE = "video-pilot-354";
let ans = {}, i = 0;
try { ans = JSON.parse(localStorage.getItem(STORE) || "{}") } catch (e) { console.warn("[VideoPilot] 저장값 읽기 실패", e) }
const save = () => { try { localStorage.setItem(STORE, JSON.stringify(ans)) } catch (e) { console.warn("[VideoPilot] 저장 실패", e) } };
const vid = (k, cap, cls = "clip") => `<figure class="${cls}"><video src="${MEDIA[k]}" autoplay muted loop playsinline></video><figcaption>${cap}</figcaption></figure>`;
const img = (k, cap) => `<figure><img src="${MEDIA[k]}" alt="${cap}"><figcaption>${cap}</figcaption></figure>`;
function body(s) {
  if (s.kind === "style") return img("still-" + s.scene, "승인본 정지 그림(목표 화풍)") + vid("v" + s.n, "영상 " + s.n);
  if (s.kind === "face") return vid("v" + s.n, "영상 " + s.n) + "<h3>머리 확대(같은 영상)</h3><div class=heads>"
    + s.heads.map(h => vid(`v${s.n}-${h}`, h)).join("") + "</div>";
  if (s.kind === "final") return "AB".split("").map(g => `<h3>묶음 ${g}</h3><div class=grid>`
    + s.groups[g].map(n => vid("v" + n, "영상 " + n, g.toLowerCase())).join("") + "</div>").join("");
  return "";
}
function summary() {
  const lines = ["task 354 사람 판정"];
  for (const s of SCREENS) {
    const a = ans[s.id] || "미답";
    if (s.kind === "final") lines.push(`쓸 만한 모델: ${a}${a === "A" || a === "B" ? " (" + GROUP[a] + ")" : ""} · A=${GROUP.A} B=${GROUP.B}`);
    else lines.push(`${KEY[s.n]} ${s.kind === "style" ? "화풍" : "얼굴"}: ${a}`);
  }
  return lines.join("\\n");
}
function render() {
  const m = document.getElementById("m"), o = document.getElementById("o");
  if (i >= SCREENS.length) {
    m.innerHTML = `<div class=top><span>끝</span><span>${Object.keys(ans).length}/${SCREENS.length} 답함</span></div>
      <h1>판정 문장</h1><p class=look>아래 문장을 복사해 채팅에 붙여 주세요.</p><pre id=t>${summary()}</pre>`;
    o.innerHTML = `<button id=copy style="grid-column:1/-1">판정 문장 복사</button>`;
    document.getElementById("copy").onclick = async () => {
      try { await navigator.clipboard.writeText(summary()); document.getElementById("copy").textContent = "복사됨" }
      catch (e) { console.warn("[VideoPilot] 복사 실패", e); getSelection().selectAllChildren(document.getElementById("t")) }
    };
  } else {
    const s = SCREENS[i];
    m.innerHTML = `<div class=top><span>${i + 1} / ${SCREENS.length}</span><span>${s.scene ? NAME[s.scene] : ""}</span></div>
      <h1>${s.q}</h1><p class=look>${s.look}</p>${body(s)}`;
    o.innerHTML = s.opts.map(x => `<button aria-pressed="${ans[s.id] === x}">${x}</button>`).join("");
    o.querySelectorAll("button").forEach(b => b.onclick = () => { ans[s.id] = b.textContent; save(); i++; render(); scrollTo(0, 0) });
  }
  document.getElementById("back").disabled = i === 0;
  document.getElementById("next").disabled = i >= SCREENS.length;
}
document.getElementById("back").onclick = () => { i = Math.max(0, i - 1); render(); scrollTo(0, 0) };
document.getElementById("next").onclick = () => { i = Math.min(SCREENS.length, i + 1); render(); scrollTo(0, 0) };
render();
</script>
"""


def main(dst):
    screens, media, key, group = build()
    page = (PAGE.replace("__SCREENS__", json.dumps(screens, ensure_ascii=False)).replace("__KEY__", json.dumps(key))
            .replace("__GROUP__", json.dumps(group)).replace("__MEDIA__", json.dumps(media)))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "w", encoding="utf-8").write(page)
    print(f"[VideoPilot] {dst} {len(page) / 1e6:.2f}MB · 클립 {len(key)} · 문항 {len(screens)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(V.RT, "pages", "video-pilot.html"))
