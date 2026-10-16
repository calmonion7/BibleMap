#!/usr/bin/env python3
"""task#358 S2·S4 — 정본 참조 편집 페이지(폰용, 한 화면 한 문항). 357 페이지 틀(make_lora_scene_page의 CSS·JS)을 그대로 쓴다.
  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV make_ref_edit_page.py preview <353 페이지 HTML> <출력 HTML>   # 세기 미리보기 한 화면(사용자가 하나 고름)
  $VENV make_ref_edit_page.py judge <353 페이지 HTML> <출력 HTML>     # 판정: A 2(같은 인물) · B 1(섞임) · C 3(화풍·뜻)
  $VENV make_ref_edit_page.py judge2511 <353 페이지 HTML> <출력 HTML> # task#359 — 같은 판정, metrics·산출 경로·섞기 시드만 2511 것
카드 폭 356 CSS px(DPR 3), 확대·크롭 없음, 대상 머리 위 ▼(OWLv2, 못 찾으면 명세 구역 위). 그림은 한 번만 싣고 ▼는 CSS.
쌍·그림의 정체(처치/대조·시드)는 게시 전에 samples/ref-edit/metrics.json `screens`에 적고 페이지에는 번호만."""
import json, os, random, sys

from PIL import Image

import params
import make_lora_scene_page as L
from make_cast_v2_pilot_page import head
from metrics_lora_scene import REFS
import gen_ref_edit as G

NAME, SC_NAME = L.NAME, L.SC_NAME
PAIRS = {"saul": ("gilgal", "engedi"), "david": ("engedi", "ramah")}


def ratio_heads(m, path, scene):
    if path not in m["heads"]:
        im = Image.open(path)
        m["heads"][path] = {w: [v / d for v, d in zip(head(scene, w, path)[0], (im.width, im.height) * 2)]
                            for w in params.LORA_SCENE_SCENES[scene][1]}
    return m["heads"][path]


def build(m, mode, out=G.OUT, shuffle=params.REF_EDIT_SHUFFLE_SEED):
    imgs, ident, sc = {}, {}, []
    m.setdefault("heads", {})

    def img(path):
        for k, v in imgs.items():
            if v == path:
                return k
        k = f"i{len(imgs)}"
        imgs[k] = path
        return k

    def card(path, scene, who, cap):
        h = ratio_heads(m, path, scene) if who else {}
        ws = [who] if isinstance(who, str) else (who or [])
        return {"img": img(path), "marks": [h[w] for w in ws if w in h], "cap": cap}

    if mode == "preview":
        p0 = {e["seed"]: e["base"] for e in m["preview"]}
        ref = {"img": img(os.path.join(G.HERE, "frozen", "saul.png")), "marks": [], "cap": "사울 정본"}
        items = []
        for v in params.REF_EDIT_AXIS_VALUES:
            cards = []
            for s in params.REF_EDIT_PREVIEW_SEEDS:
                e = next(x for x in m["preview"] if x["seed"] == s and x["strength"] == v)
                cards.append(card(e["out"], "gilgal", "saul", f"시드 {s}"))
            items.append({"key": str(v), "label": f"세기 {v}", "cards": cards})
        items.append({"key": "base", "label": "참고: 편집 전 바탕(고르지 마세요)",
                      "cards": [card(p0[s], "gilgal", "saul", f"시드 {s}") for s in params.REF_EDIT_PREVIEW_SEEDS]})
        sc.append({"id": "P-strength", "q": "길갈 사울 · 편집 세기를 하나만 고르세요",
                   "look": "맨 위가 사울 정본입니다. 세기마다 같은 두 바탕(시드 404·505)의 ▼ 사울을 편집한 결과입니다. "
                           "정본과 같은 사람으로 보이면서 연필 화풍이 덜 무너진 것 하나를 누르세요. 맨 아래는 편집 전 바탕입니다.",
                   "ref": ref, "items": items, "mark": "✓ 고름"})
        return sc, imgs, ident

    E = lambda k, s: os.path.join(out, "edit", k, f"s{s}.png")
    rnd = random.Random(shuffle)
    for who, (a, b) in PAIRS.items():
        pairs = [{"kind": "edit", "seed": s, "a": E(a, s), "b": E(b, s)} for s in params.REF_EDIT_SEEDS]
        pairs += [{"kind": "control", "seed": s, "a": G.base_path(a, s), "b": G.base_path(b, s)} for s in params.LORA_SCENE_CONTROL_SEEDS]
        rnd.shuffle(pairs)
        sid = f"A-{who}"
        ident[sid] = [{"n": n + 1, "kind": p["kind"], "seed": p["seed"]} for n, p in enumerate(pairs)]
        sc.append({"id": sid, "q": f"{NAME[who]} · 두 ▼가 같은 사람으로 읽히는 쌍을 누르세요",
                   "look": f"쌍마다 위는 {SC_NAME[a]}, 아래는 {SC_NAME[b]}입니다. 카드에 실제로 보이는 크기 그대로입니다(확대하지 마세요). "
                           f"▼ 표시된 {NAME[who]}만 보고, 같은 사람으로 읽히는 쌍을 모두 누르세요. 없으면 그대로 「표시 끝」.",
                   "items": [{"key": str(n + 1), "label": f"쌍 {n + 1}",
                              "cards": [card(p["a"], a, who, SC_NAME[a]), card(p["b"], b, who, SC_NAME[b])]} for n, p in enumerate(pairs)],
                   "mark": "✓ 같은 사람"})
    whos = params.LORA_SCENE_SCENES["engedi"][1]
    sc.append({"id": "B-engedi", "q": "엔게디 · 두 ▼ 인물이 서로 닮아 구별이 안 되는 그림을 누르세요",
               "look": "다윗·사울이 모두 나오는 그림입니다. 둘이 서로 닮아서 누가 누구인지 구별이 안 되면 누르세요.",
               "items": [{"key": f"s{s}", "label": f"그림 {n + 1}", "cards": [card(E("engedi", s), "engedi", whos, "엔게디")]}
                         for n, s in enumerate(params.REF_EDIT_SEEDS)], "mark": "✓ 구별 안 됨"})
    ident["B-engedi"] = [{"key": f"s{s}", "kind": "edit", "seed": s} for s in params.REF_EDIT_SEEDS]
    for key in params.REF_EDIT_SCENES:
        its = [{"kind": "edit", "seed": s, "path": E(key, s)} for s in params.REF_EDIT_SEEDS]
        its += [{"kind": "control", "seed": s, "path": G.base_path(key, s)} for s in params.LORA_SCENE_CONTROL_SEEDS]
        rnd.shuffle(its)
        sid = f"C-{key}"
        ident[sid] = [{"n": n + 1, "kind": t["kind"], "seed": t["seed"]} for n, t in enumerate(its)]
        sc.append({"id": sid, "q": f"{SC_NAME[key]} · 연필 화풍이나 장면 뜻이 기준보다 크게 무너진 그림을 누르세요",
                   "look": "맨 위가 기준 그림입니다. 연필·수채 화풍이 크게 달라졌거나, 장면이 말하는 일이 안 보이게 된 그림을 누르세요. 얼굴은 보지 않아도 됩니다.",
                   "ref": {"img": img(REFS[key]), "marks": [], "cap": "기준"},
                   "items": [{"key": str(n + 1), "label": f"그림 {n + 1}", "cards": [card(t["path"], key, None, "")]} for n, t in enumerate(its)],
                   "mark": "✗ 무너짐"})
    return sc, imgs, ident


def main():
    mode, src, dst = sys.argv[1:4]
    v2511 = mode == "judge2511"
    if v2511:
        import gen_ref_edit_2511 as R
    metrics = R.METRICS if v2511 else G.METRICS
    m = json.load(open(metrics))
    html = open(src, encoding="utf-8").read()
    title = "편집 세기 고르기" if mode == "preview" else "정본 참조 편집 판정"
    hd = html[html.index("<title>"):html.index("<script>")].replace("<title>인물 정의 판정</title>", f"<title>{title}</title>")
    hd = hd.replace("</style>", L.CSS + "</style>")
    sc, imgs, ident = build(m, mode, R.OUT, params.REF_EDIT_2511_SHUFFLE_SEED) if v2511 else build(m, mode)
    data = {k: L.uri(Image.open(p).convert("RGB"), L.CARD * L.DPR) for k, p in imgs.items()}
    if v2511:
        picked = f"{R.NAME} 참조 편집 · q{m['quantize']} · 전체 편집 → 몸 상자 되붙임 · 시드 {params.REF_EDIT_SEEDS} · 카드 폭 356px · 기계 거르기 없음"
        js = L.JS.replace("lora-scene-357", "ref-edit-359-judge").replace("task 357 사람 판정", "task 359 사람 판정")
    else:
        model = params.REF_EDIT_MODELS[m["model_i"]][0]
        picked = (f"{model} 참조 편집 · {params.REF_EDIT_AXIS} " + (f"{params.REF_EDIT_AXIS_VALUES}" if mode == "preview" else f"{m['preview_choice']}")
                  + f" · 시드 {params.REF_EDIT_PREVIEW_SEEDS if mode == 'preview' else params.REF_EDIT_SEEDS} · 카드 폭 356px · 기계 거르기 없음")
        js = L.JS.replace("lora-scene-357", f"ref-edit-358-{mode}").replace("task 357 사람 판정", f"task 358 {'세기 고르기' if mode == 'preview' else '사람 판정'}")
    page = (hd + "<script>\nconst SCREENS = " + json.dumps(sc, ensure_ascii=False) + ";\nconst IMGS = " + json.dumps(data)
            + ";\nconst PICKED = " + json.dumps(picked, ensure_ascii=False) + ";\n" + js + "\n</body></html>\n")
    open(dst, "w", encoding="utf-8").write(page)
    if mode != "preview":
        m["screens"] = ident
    json.dump(m, open(metrics, "w"), ensure_ascii=False, indent=1)
    print(dst, f"{len(page) / 1e6:.2f}MB, 화면 {len(sc)}, 그림 {len(imgs)}")


if __name__ == "__main__":
    main()
