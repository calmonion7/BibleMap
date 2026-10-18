#!/usr/bin/env python3
"""task#358 S2·S4 — 정본 참조 편집 페이지(폰용, 한 화면 한 문항). 357 페이지 틀(make_lora_scene_page의 CSS·JS)을 그대로 쓴다.
  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV make_ref_edit_page.py preview <353 페이지 HTML> <출력 HTML>   # 세기 미리보기 한 화면(사용자가 하나 고름)
  $VENV make_ref_edit_page.py judge <353 페이지 HTML> <출력 HTML>     # 판정: A 2(같은 인물) · B 1(섞임) · C 3(화풍·뜻)
  $VENV make_ref_edit_page.py judge2511 <353 페이지 HTML> <출력 HTML> # task#359 — 같은 판정, metrics·산출 경로·섞기 시드만 2511 것
  $VENV make_ref_edit_page.py judge-lightning <353 페이지 HTML> <출력 HTML> # task#360 — 같은 판정, 2511 + Lightning 4스텝 것
  $VENV make_ref_edit_page.py judge-costume <353 페이지 HTML> <출력 HTML>   # task#361 — 엔게디 차림 편집: C(+누른 그림마다 이유) · A 2 · B 1
  $VENV make_ref_edit_page.py judge-text <353 페이지 HTML> <출력 HTML>      # task#362 — 엔게디 문구 수리: C(새 문구 바탕 8 + 353 바탕 8, +이유)만
  $VENV make_ref_edit_page.py judge-512 <353 페이지 HTML> <출력 HTML>       # task#363 — 512토큰 수리: 엔게디·길갈·라마 C(새 8 + 이전 8, +이유)
  $VENV make_ref_edit_page.py judge-dark <353 페이지 HTML> <출력 HTML>      # task#364 — 엔게디 굴 어둠·빛: C(r2 8 + A 8 + B 8, +이유)
  $VENV make_ref_edit_page.py judge-gaze <353 페이지 HTML> <출력 HTML>      # task#365 — 엔게디 시선 축: 4화면(마주 봄·다윗 시선·손·칼·가드), 기준+r2+A+B 25장
  $VENV make_ref_edit_page.py judge-away <353 페이지 HTML> <출력 HTML>      # task#366 — 엔게디 마주 봄 B1·B2: 4화면(가드는 칼 뺌), 기준+A+B1+B2+B 33장
  $VENV make_ref_edit_page.py judge-backhand <353 페이지 HTML> <출력 HTML>  # task#367 — 엔게디 B′·Bh: 4화면(366 문항 그대로), 기준+A+B+B′+Bh 33장
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
# 358 이후 같은 판정의 변형 — 모드 → (생성 모듈, 섞기 시드, 과제 번호, 설명 틀). 358 judge·preview는 이 표 밖(바이트 동일 유지).
VARIANTS = {"judge2511": ("gen_ref_edit_2511", params.REF_EDIT_2511_SHUFFLE_SEED, 359, "{name} 참조 편집 · q{q} · 전체 편집 → 몸 상자 되붙임"),
            "judge-lightning": ("gen_ref_edit_lightning", params.REF_EDIT_LIGHTNING_SHUFFLE_SEED, 360,
                                "{name} + Lightning 4스텝 참조 편집 · q{q} · 외형 명시 지시문 · 전체 편집 → 몸 상자 되붙임")}


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


# task#361 고정 절(notes/REF-EDIT-COSTUME.md) — C 무너짐 이유 보기
REASONS = [("style", "화풍(연필·수채 결)"), ("dark", "굴 어둠·빛"), ("cloak", "겉옷자락 베기(다윗이 사울 몸에 붙은 겉옷을 벰)"),
           ("pose", "인물 자세·위치"), ("etc", "기타")]
SAME_LOOK = ("▼ 표시된 {name}만 보고, 같은 사람으로 읽히는 쌍을 모두 누르세요. 얼굴·머리·수염·몸집(나이대)만 보고, 옷은 빼고 봅니다. "
             "카드에 실제로 보이는 크기 그대로입니다(확대하지 마세요). 없으면 그대로 「표시 끝」.")


def build_costume(m):
    """task#361 — C-engedi(기준 + 처치 8 + 대조 8) → C-이유(C에서 누른 그림만 보임) → A-saul·A-david(옛 360 처치 ↔ 새 엔게디 처치) → B-engedi."""
    import gen_ref_edit_lightning as N
    assert N.COSTUME, "params.REF_EDIT_LIGHTNING_LOOK_SRC가 image+scene이 아님"
    old = os.path.join(G.ROOT, "ref-edit-lightning")
    NEW = lambda s: os.path.join(N.OUT, "edit", "engedi", f"s{s}.png")
    OLD = lambda k, s: os.path.join(old, "edit", k, f"s{s}.png")
    imgs, ident, sc = {}, {}, []
    m.setdefault("heads", {})

    def img(path):
        assert os.path.exists(path), path
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

    rnd = random.Random(params.REF_EDIT_COSTUME_SHUFFLE_SEED)
    its = [{"kind": "edit", "seed": s, "path": NEW(s)} for s in params.REF_EDIT_SEEDS]
    its += [{"kind": "control", "seed": s, "path": G.base_path("engedi", s)} for s in params.REF_EDIT_SEEDS]
    rnd.shuffle(its)
    ident["C-engedi"] = [{"n": n + 1, "kind": t["kind"], "seed": t["seed"]} for n, t in enumerate(its)]
    sc.append({"id": "C-engedi", "q": f"{SC_NAME['engedi']} · 연필 화풍이나 장면 뜻이 기준보다 크게 무너진 그림을 누르세요",
               "look": "맨 위가 기준 그림입니다. 연필·수채 화풍이 크게 달라졌거나, 장면이 말하는 일이 안 보이게 된 그림을 누르세요. 얼굴은 보지 않아도 됩니다.",
               "ref": {"img": img(REFS["engedi"]), "marks": [], "cap": "기준"},
               "items": [{"key": str(n + 1), "label": f"그림 {n + 1}", "cards": [card(t["path"], "engedi", None, "")]} for n, t in enumerate(its)],
               "mark": "✗ 무너짐"})
    for n, t in enumerate(its):
        sc.append({"id": f"C-why-{n + 1}", "if": ["C-engedi", str(n + 1)], "q": f"그림 {n + 1} · 무엇이 무너졌나요? (여러 개)",
                   "look": "앞 화면에서 무너졌다고 누른 그림입니다. 해당하는 것을 모두 누르세요.",
                   "ref": {"img": img(t["path"]), "marks": [], "cap": f"그림 {n + 1}"},
                   "items": [{"key": k, "label": lab, "cards": []} for k, lab in REASONS], "mark": "✓"})
    ident["C-why"] = {"screen_of": "C-engedi", "keys": [k for k, _ in REASONS]}
    for who, (a, b) in PAIRS.items():
        side = lambda k, s: NEW(s) if k == "engedi" else OLD(k, s)
        pairs = [{"kind": "edit", "seed": s, "a": side(a, s), "b": side(b, s)} for s in params.REF_EDIT_SEEDS]
        pairs += [{"kind": "control", "seed": s, "a": G.base_path(a, s), "b": G.base_path(b, s)} for s in params.LORA_SCENE_CONTROL_SEEDS]
        rnd.shuffle(pairs)
        sid = f"A-{who}"
        ident[sid] = [{"n": n + 1, "kind": p["kind"], "seed": p["seed"]} for n, p in enumerate(pairs)]
        sc.append({"id": sid, "q": f"{NAME[who]} · 두 ▼가 같은 사람으로 읽히는 쌍을 누르세요",
                   "look": f"쌍마다 위는 {SC_NAME[a]}, 아래는 {SC_NAME[b]}입니다. " + SAME_LOOK.format(name=NAME[who]),
                   "items": [{"key": str(n + 1), "label": f"쌍 {n + 1}",
                              "cards": [card(p["a"], a, who, SC_NAME[a]), card(p["b"], b, who, SC_NAME[b])]} for n, p in enumerate(pairs)],
                   "mark": "✓ 같은 사람"})
    whos = params.LORA_SCENE_SCENES["engedi"][1]
    sc.append({"id": "B-engedi", "q": "엔게디 · 두 ▼ 인물이 서로 닮아 구별이 안 되는 그림을 누르세요",
               "look": "다윗·사울이 모두 나오는 그림입니다. 둘이 서로 닮아서 누가 누구인지 구별이 안 되면 누르세요.",
               "items": [{"key": f"s{s}", "label": f"그림 {n + 1}", "cards": [card(NEW(s), "engedi", whos, "엔게디")]}
                         for n, s in enumerate(params.REF_EDIT_SEEDS)], "mark": "✓ 구별 안 됨"})
    ident["B-engedi"] = [{"key": f"s{s}", "kind": "edit", "seed": s} for s in params.REF_EDIT_SEEDS]
    return sc, imgs, ident


# 조건부 화면(`if`: [화면 id, 그 화면에서 눌린 키])은 건너뛰고, 판정 문장에도 넣지 않는다 — 358~360 페이지의 L.JS는 그대로.
COND_JS = [("function step(d) { i = Math.max(0, Math.min(SCREENS.length, i + d)); render() }",
            "function shown(s) { return !s.if || (ans[s.if[0]] || []).includes(s.if[1]) }\n"
            "function step(d) { do { i = Math.max(0, Math.min(SCREENS.length, i + d)) } while (i > 0 && i < SCREENS.length && !shown(SCREENS[i])); render() }"),
           ("SCREENS.map(s =>", "SCREENS.filter(shown).map(s =>"),
           ("<span>${i + 1}/${n}</span></div><h1>${s.q}", "<span>${SCREENS.slice(0, i + 1).filter(shown).length}/${SCREENS.filter(shown).length}</span></div><h1>${s.q}")]


def main_costume(src, dst):
    import gen_ref_edit_lightning as N
    m = json.load(open(N.METRICS))
    html = open(src, encoding="utf-8").read()
    hd = html[html.index("<title>"):html.index("<script>")].replace("<title>인물 정의 판정</title>", "<title>차림 편집 판정</title>")
    hd = hd.replace("</style>", L.CSS + "</style>")
    sc, imgs, ident = build_costume(m)
    data = {k: L.uri(Image.open(p).convert("RGB"), L.CARD * L.DPR) for k, p in imgs.items()}
    picked = (f"{N.NAME} + Lightning 4스텝 참조 편집 · q{m['quantize']} · 정체성은 정본 그림, 차림은 장면 명세 · 전체 편집 → 몸 상자 되붙임"
              f" · 시드 {params.REF_EDIT_SEEDS} · 카드 폭 356px · 기계 거르기 없음")
    js = L.JS.replace("lora-scene-357", "ref-edit-361-judge").replace("task 357 사람 판정", "task 361 사람 판정")
    for a, b in COND_JS:
        assert a in js, a
        js = js.replace(a, b)
    page = (hd + "<script>\nconst SCREENS = " + json.dumps(sc, ensure_ascii=False) + ";\nconst IMGS = " + json.dumps(data)
            + ";\nconst PICKED = " + json.dumps(picked, ensure_ascii=False) + ";\n" + js + "\n</body></html>\n")
    open(dst, "w", encoding="utf-8").write(page)
    m["screens"] = ident
    json.dump(m, open(N.METRICS, "w"), ensure_ascii=False, indent=1)
    print(dst, f"{len(page) / 1e6:.2f}MB, 화면 {len(sc)}, 그림 {len(imgs)}")


# task#362 고정 절(notes/ENGEDI-TEXT.md) — 361 보기 그대로, 「굴 어둠·빛」에만 설명을 붙인다
REASONS_TEXT = [(k, lab + " — 굴 안이 기준처럼 어둡지 않다(벽 전체가 밝거나 어귀가 크고 가까워 바깥처럼 보임)" if k == "dark" else lab)
                for k, lab in REASONS]


def main_text(src, dst):
    """task#362 — C-engedi(기준 + 새 문구 바탕 8 + 353 바탕 8) → C-why(누른 그림만). 361 C 화면과 같은 문구."""
    import gen_engedi_text as T
    m = json.load(open(T.METRICS))
    NEW = lambda s: os.path.join(T.OUT, m["chosen"], f"s{s}.png")
    imgs = {}

    def img(path):
        assert os.path.exists(path), path
        k = f"i{len(imgs)}"
        imgs[k] = path
        return k

    rnd = random.Random(params.ENGEDI_TEXT_SHUFFLE_SEED)
    its = [{"kind": "new", "seed": s, "path": NEW(s)} for s in params.REF_EDIT_SEEDS]
    its += [{"kind": "353", "seed": s, "path": G.base_path("engedi", s)} for s in params.REF_EDIT_SEEDS]
    rnd.shuffle(its)
    keys = [img(t["path"]) for t in its]
    sc = [{"id": "C-engedi", "q": f"{SC_NAME['engedi']} · 연필 화풍이나 장면 뜻이 기준보다 크게 무너진 그림을 누르세요",
           "look": "맨 위가 기준 그림입니다. 연필·수채 화풍이 크게 달라졌거나, 장면이 말하는 일이 안 보이게 된 그림을 누르세요. 얼굴은 보지 않아도 됩니다.",
           "ref": {"img": img(REFS["engedi"]), "marks": [], "cap": "기준"},
           "items": [{"key": str(n + 1), "label": f"그림 {n + 1}", "cards": [{"img": keys[n], "marks": [], "cap": ""}]} for n in range(len(its))],
           "mark": "✗ 무너짐"}]
    for n in range(len(its)):
        sc.append({"id": f"C-why-{n + 1}", "if": ["C-engedi", str(n + 1)], "q": f"그림 {n + 1} · 무엇이 무너졌나요? (여러 개)",
                   "look": "앞 화면에서 무너졌다고 누른 그림입니다. 해당하는 것을 모두 누르세요.",
                   "ref": {"img": keys[n], "marks": [], "cap": f"그림 {n + 1}"},
                   "items": [{"key": k, "label": lab, "cards": []} for k, lab in REASONS_TEXT], "mark": "✓"})
    html = open(src, encoding="utf-8").read()
    hd = html[html.index("<title>"):html.index("<script>")].replace("<title>인물 정의 판정</title>", "<title>엔게디 문구 판정</title>")
    hd = hd.replace("</style>", L.CSS + "</style>")
    data = {k: L.uri(Image.open(p).convert("RGB"), L.CARD * L.DPR) for k, p in imgs.items()}
    picked = f"엔게디 장면 문구 수리 · 문구 {m['chosen']} · 시드 {params.REF_EDIT_SEEDS} · 카드 폭 356px · 기계 거르기 없음"
    js = L.JS.replace("lora-scene-357", "engedi-text-362-judge").replace("task 357 사람 판정", "task 362 사람 판정")
    for a, b in COND_JS:
        assert a in js, a
        js = js.replace(a, b)
    page = (hd + "<script>\nconst SCREENS = " + json.dumps(sc, ensure_ascii=False) + ";\nconst IMGS = " + json.dumps(data)
            + ";\nconst PICKED = " + json.dumps(picked, ensure_ascii=False) + ";\n" + js + "\n</body></html>\n")
    open(dst, "w", encoding="utf-8").write(page)
    m["screens"] = {"C-engedi": [{"n": n + 1, "kind": t["kind"], "seed": t["seed"]} for n, t in enumerate(its)],
                    "C-why": {"screen_of": "C-engedi", "keys": [k for k, _ in REASONS_TEXT]}}
    json.dump(m, open(T.METRICS, "w"), ensure_ascii=False, indent=1)
    print(dst, f"{len(page) / 1e6:.2f}MB, 화면 {len(sc)}, 그림 {len(imgs)}")


# task#363 고정 절(notes/PROMPT-512.md) — 엔게디는 362 보기 그대로, 길갈·라마는 굴·겉옷자락 대신 장면 뜻
REASONS_512 = {"engedi": REASONS_TEXT,
               "gilgal": [("style", "화풍(연필·수채 결)"), ("meaning", "장면 뜻(누가 무엇을 하는지)"), ("pose", "인물 자세·위치"), ("etc", "기타")]}
REASONS_512["ramah"] = REASONS_512["gilgal"]


def main_512(src, dst):
    """task#363 — 장면마다 C(기준 + 새 8 + 이전 8) → C-why(누른 그림만). 엔게디·길갈·라마."""
    import gen_prompt_512 as P
    m = json.load(open(P.METRICS))
    imgs, sc, ident = {}, [], {}

    def img(path):
        assert os.path.exists(path), path
        k = f"i{len(imgs)}"
        imgs[k] = path
        return k

    rnd = random.Random(params.PROMPT_512_SHUFFLE_SEED_R2 if m.get("round") == 2 else params.PROMPT_512_SHUFFLE_SEED)
    for scene in P.SCENES:
        its = [{"kind": "new", "seed": s, "path": P.new_path(scene, s)} for s in params.REF_EDIT_SEEDS]
        its += [{"kind": "old", "seed": s, "path": P.old_path(scene, s)} for s in params.REF_EDIT_SEEDS]
        rnd.shuffle(its)
        keys = [img(t["path"]) for t in its]
        cid = f"C-{scene}"
        ident[cid] = [{"n": n + 1, "kind": t["kind"], "seed": t["seed"]} for n, t in enumerate(its)]
        sc.append({"id": cid, "q": f"{SC_NAME[scene]} · 연필 화풍이나 장면 뜻이 기준보다 크게 무너진 그림을 누르세요",
                   "look": "맨 위가 기준 그림입니다. 연필·수채 화풍이 크게 달라졌거나, 장면이 말하는 일이 안 보이게 된 그림을 누르세요. 얼굴은 보지 않아도 됩니다.",
                   "ref": {"img": img(REFS[scene]), "marks": [], "cap": "기준"},
                   "items": [{"key": str(n + 1), "label": f"그림 {n + 1}", "cards": [{"img": keys[n], "marks": [], "cap": ""}]} for n in range(len(its))],
                   "mark": "✗ 무너짐"})
        for n in range(len(its)):
            sc.append({"id": f"C-why-{scene}-{n + 1}", "if": [cid, str(n + 1)], "q": f"{SC_NAME[scene]} 그림 {n + 1} · 무엇이 무너졌나요? (여러 개)",
                       "look": "앞 화면에서 무너졌다고 누른 그림입니다. 해당하는 것을 모두 누르세요.",
                       "ref": {"img": keys[n], "marks": [], "cap": f"그림 {n + 1}"},
                       "items": [{"key": k, "label": lab, "cards": []} for k, lab in REASONS_512[scene]], "mark": "✓"})
        ident[f"C-why-{scene}"] = {"screen_of": cid, "keys": [k for k, _ in REASONS_512[scene]]}
    html = open(src, encoding="utf-8").read()
    hd = html[html.index("<title>"):html.index("<script>")].replace("<title>인물 정의 판정</title>", "<title>프롬프트 잘림 판정</title>")
    hd = hd.replace("</style>", L.CSS + "</style>")
    data = {k: L.uri(Image.open(p).convert("RGB"), L.CARD * L.DPR) for k, p in imgs.items()}
    picked = f"512토큰 수리 · 장면 {list(P.SCENES)} · 시드 {params.REF_EDIT_SEEDS} · 카드 폭 356px · 기계 거르기 없음"
    js = L.JS.replace("lora-scene-357", "prompt-512-363-judge").replace("task 357 사람 판정", "task 363 사람 판정")
    for a, b in COND_JS:
        assert a in js, a
        js = js.replace(a, b)
    page = (hd + "<script>\nconst SCREENS = " + json.dumps(sc, ensure_ascii=False) + ";\nconst IMGS = " + json.dumps(data)
            + ";\nconst PICKED = " + json.dumps(picked, ensure_ascii=False) + ";\n" + js + "\n</body></html>\n")
    open(dst, "w", encoding="utf-8").write(page)
    m["screens"] = ident
    json.dump(m, open(P.METRICS, "w"), ensure_ascii=False, indent=1)
    print(dst, f"{len(page) / 1e6:.2f}MB, 화면 {len(sc)}, 그림 {len(imgs)}")


# task#364 고정 절(notes/ENGEDI-DARK.md) — 「굴 어둠·빛」을 밝음·입구 둘로 나눔
REASONS_DARK = [("style", "화풍(연필·수채 결)"), ("bright", "굴 안이 기준보다 밝다"), ("mouth", "굴 입구가 가깝거나 크게 보인다"),
                ("cloak", REASONS[2][1]), ("pose", "인물 자세·위치"), ("etc", "기타")]


def main_dark(src, dst):
    """task#364 — C-engedi(기준 + r2 8 + A 8 + B 8) → C-why(누른 그림만). 질문은 363과 같다."""
    import gen_engedi_dark as E
    m = json.load(open(E.METRICS))
    imgs = {}

    def img(path):
        assert os.path.exists(path), path
        k = f"i{len(imgs)}"
        imgs[k] = path
        return k

    its = [{"kind": "r2", "seed": s, "path": E.r2_path(s)} for s in params.REF_EDIT_SEEDS]
    its += [{"kind": t, "seed": s, "path": E.out_path(t, s)} for t in ("A", "B") for s in params.REF_EDIT_SEEDS]
    random.Random(params.ENGEDI_DARK_SHUFFLE_SEED).shuffle(its)
    keys = [img(t["path"]) for t in its]
    sc = [{"id": "C-engedi", "q": f"{SC_NAME['engedi']} · 연필 화풍이나 장면 뜻이 기준보다 크게 무너진 그림을 누르세요",
           "look": "맨 위가 기준 그림입니다. 연필·수채 화풍이 크게 달라졌거나, 장면이 말하는 일이 안 보이게 된 그림을 누르세요. 얼굴은 보지 않아도 됩니다.",
           "ref": {"img": img(REFS["engedi"]), "marks": [], "cap": "기준"},
           "items": [{"key": str(n + 1), "label": f"그림 {n + 1}", "cards": [{"img": keys[n], "marks": [], "cap": ""}]} for n in range(len(its))],
           "mark": "✗ 무너짐"}]
    for n in range(len(its)):
        sc.append({"id": f"C-why-engedi-{n + 1}", "if": ["C-engedi", str(n + 1)], "q": f"{SC_NAME['engedi']} 그림 {n + 1} · 무엇이 무너졌나요? (여러 개)",
                   "look": "앞 화면에서 무너졌다고 누른 그림입니다. 해당하는 것을 모두 누르세요.",
                   "ref": {"img": keys[n], "marks": [], "cap": f"그림 {n + 1}"},
                   "items": [{"key": k, "label": lab, "cards": []} for k, lab in REASONS_DARK], "mark": "✓"})
    html = open(src, encoding="utf-8").read()
    hd = html[html.index("<title>"):html.index("<script>")].replace("<title>인물 정의 판정</title>", "<title>엔게디 굴 어둠 판정</title>")
    hd = hd.replace("</style>", L.CSS + "</style>")
    data = {k: L.uri(Image.open(p).convert("RGB"), L.CARD * L.DPR) for k, p in imgs.items()}
    picked = f"엔게디 굴 어둠·빛 · 처치 A·B + 대조 r2 · 시드 {params.REF_EDIT_SEEDS} · 카드 폭 356px · 기계 거르기 없음"
    js = L.JS.replace("lora-scene-357", "engedi-dark-364-judge").replace("task 357 사람 판정", "task 364 사람 판정")
    for a, b in COND_JS:
        assert a in js, a
        js = js.replace(a, b)
    page = (hd + "<script>\nconst SCREENS = " + json.dumps(sc, ensure_ascii=False) + ";\nconst IMGS = " + json.dumps(data)
            + ";\nconst PICKED = " + json.dumps(picked, ensure_ascii=False) + ";\n" + js + "\n</body></html>\n")
    open(dst, "w", encoding="utf-8").write(page)
    m["screens"] = {"C-engedi": [{"n": n + 1, "kind": t["kind"], "seed": t["seed"]} for n, t in enumerate(its)],
                    "C-why-engedi": {"screen_of": "C-engedi", "keys": [k for k, _ in REASONS_DARK]}}
    json.dump(m, open(E.METRICS, "w"), ensure_ascii=False, indent=1)
    print(dst, f"{len(page) / 1e6:.2f}MB, 화면 {len(sc)}, 그림 {len(imgs)}")


# task#365 고정 절(notes/ENGEDI-GAZE.md) — 한 화면에 축 하나, 모두 「문제 있는 그림을 누르세요」
GAZE_SCREENS = [
    ("G-face", "사울과 다윗이 마주 보는 그림을 누르세요 (사울이 다윗 쪽으로 고개나 몸을 돌림)",
     "사울(오른쪽)이 다윗(왼쪽) 쪽으로 고개나 몸을 돌려 둘이 서로 마주 보는 그림을 누르세요.", False),
    ("G-look", "다윗이 자르는 옷자락(아래)이 아니라 사울이나 앞쪽을 보는 그림을 누르세요",
     "각 그림 아래에 다윗 쪽 확대가 있습니다. 다윗의 눈이 아래 옷자락이 아니라 사울이나 앞쪽을 보는 그림을 누르세요.", True),
    ("G-hand", "다윗의 두 손·칼 위치가 옷자락을 자르는 동작에 맞지 않는 그림을 누르세요",
     "각 그림 아래에 다윗 쪽 확대가 있습니다. 한 손으로 옷자락을 잡고 다른 손의 칼로 자르는 모습이 아닌 그림을 누르세요.", True),
    ("G-guard", "연필 화풍이 무너지거나, 인물·칼·겉옷자락이 사라지거나 엉뚱해진 그림을 누르세요 (굴 어둠은 이번에 보지 않습니다)",
     "연필·수채 화풍이 크게 달라졌거나, 두 인물·칼·겉옷자락 중 하나가 없거나 엉뚱한 그림을 누르세요. 굴 밝기는 보지 않아도 됩니다.", False),
]
ZOOM = (0.0, 0.55)  # 다윗 쪽(왼쪽) 확대 폭 — 같은 그림을 CSS로 키움, 바이트 추가 없음
ZOOM_JS = ("function cardHTML(c) {",
           "function cardHTML(c) {\n  if (c.zoom) { const w = 356 / (c.zoom[1] - c.zoom[0]);"
           " return `<figure class=\"card\"><div class=\"cw\" style=\"height:${Math.round(w * c.ar)}px;overflow:hidden\">"
           "<img src=\"${IMGS[c.img]}\" alt=\"확대\" style=\"width:${w}px;margin-left:${-c.zoom[0] * w}px\"></div>"
           "<figcaption>${c.cap}</figcaption></figure>` }")


def main_gaze(src, dst):
    """task#365 — 화면 4개(G-face·G-look·G-hand·G-guard), 기준 + r2 8 + A 8 + B 8 = 25장을 한 번 섞어 네 화면 같은 순서."""
    import gen_engedi_dark as E
    import gen_engedi_gaze as Z
    m = json.load(open(Z.METRICS))
    imgs = {}

    def img(path):
        assert os.path.exists(path), path
        k = f"i{len(imgs)}"
        imgs[k] = path
        return k

    its = [{"kind": "ref", "seed": None, "path": REFS["engedi"]}]
    its += [{"kind": "r2", "seed": s, "path": E.r2_path(s)} for s in params.REF_EDIT_SEEDS]
    its += [{"kind": t, "seed": s, "path": Z.out_path(t, s)} for t in ("A", "B") for s in params.REF_EDIT_SEEDS]
    random.Random(params.ENGEDI_GAZE_SHUFFLE_SEED).shuffle(its)
    keys = [img(t["path"]) for t in its]
    ar = Z.P.SIZE[1] / Z.P.SIZE[0]
    sc = []
    for sid, q, look, zoom in GAZE_SCREENS:
        cards = lambda n: [{"img": keys[n], "marks": [], "cap": ""}] + (
            [{"img": keys[n], "marks": [], "cap": "다윗 쪽 확대", "zoom": list(ZOOM), "ar": ar}] if zoom else [])
        sc.append({"id": sid, "q": f"{SC_NAME['engedi']} · {q}", "look": look,
                   "items": [{"key": str(n + 1), "label": f"그림 {n + 1}", "cards": cards(n)} for n in range(len(its))],
                   "mark": "✗"})
    html = open(src, encoding="utf-8").read()
    hd = html[html.index("<title>"):html.index("<script>")].replace("<title>인물 정의 판정</title>", "<title>엔게디 시선 판정</title>")
    hd = hd.replace("</style>", L.CSS + "</style>")
    data = {k: L.uri(Image.open(p).convert("RGB"), L.CARD * L.DPR) for k, p in imgs.items()}
    picked = f"엔게디 시선 축 · 처치 A·B + 대조 r2 + 기준 · 시드 {params.REF_EDIT_SEEDS} · 카드 폭 356px · 기계 거르기 없음"
    js = L.JS.replace("lora-scene-357", "engedi-gaze-365-judge").replace("task 357 사람 판정", "task 365 사람 판정")
    assert ZOOM_JS[0] in js
    js = js.replace(*ZOOM_JS)
    page = (hd + "<script>\nconst SCREENS = " + json.dumps(sc, ensure_ascii=False) + ";\nconst IMGS = " + json.dumps(data)
            + ";\nconst PICKED = " + json.dumps(picked, ensure_ascii=False) + ";\n" + js + "\n</body></html>\n")
    open(dst, "w", encoding="utf-8").write(page)
    order = [{"n": n + 1, "kind": t["kind"], "seed": t["seed"]} for n, t in enumerate(its)]
    m["screens"] = {sid: order for sid, *_ in GAZE_SCREENS}
    json.dump(m, open(Z.METRICS, "w"), ensure_ascii=False, indent=1)
    print(dst, f"{len(page) / 1e6:.2f}MB, 화면 {len(sc)}, 그림 {len(imgs)}")


# task#366 고정 절(notes/ENGEDI-AWAY.md) — 앞 세 문항은 365 글자 그대로, 가드만 「칼」을 뺌(손·칼 축과 겹치지 않게)
AWAY_SCREENS = GAZE_SCREENS[:3] + [
    ("G-guard", "연필 화풍이 무너지거나, 인물이나 겉옷자락이 사라지거나 엉뚱해진 그림을 누르세요 (손·칼은 앞 문항에서 봤고, 굴 어둠은 이번에 보지 않습니다)",
     "연필·수채 화풍이 크게 달라졌거나, 두 인물·겉옷자락 중 하나가 없거나 엉뚱한 그림을 누르세요. 손·칼과 굴 밝기는 보지 않아도 됩니다.", False),
]


def main_away(src, dst):
    """task#366 — 화면 4개(G-face·G-look·G-hand·G-guard), 기준 + A 8 + B1 8 + B2 8 + B 8 = 33장을 한 번 섞어 네 화면 같은 순서."""
    import gen_engedi_away as W
    import gen_prompt_512 as P
    m = json.load(open(W.METRICS))
    imgs = {}

    def img(path):
        assert os.path.exists(path), path
        k = f"i{len(imgs)}"
        imgs[k] = path
        return k

    its = [{"kind": "ref", "seed": None, "path": REFS["engedi"]}]
    its += [{"kind": t, "seed": s, "path": W.out_path(t, s)} for t in W.ARMS for s in params.REF_EDIT_SEEDS]
    random.Random(params.ENGEDI_AWAY_SHUFFLE_SEED).shuffle(its)
    keys = [img(t["path"]) for t in its]
    ar = P.SIZE[1] / P.SIZE[0]
    sc = []
    for sid, q, look, zoom in AWAY_SCREENS:
        cards = lambda n: [{"img": keys[n], "marks": [], "cap": ""}] + (
            [{"img": keys[n], "marks": [], "cap": "다윗 쪽 확대", "zoom": list(ZOOM), "ar": ar}] if zoom else [])
        sc.append({"id": sid, "q": f"{SC_NAME['engedi']} · {q}", "look": look,
                   "items": [{"key": str(n + 1), "label": f"그림 {n + 1}", "cards": cards(n)} for n in range(len(its))],
                   "mark": "✗"})
    html = open(src, encoding="utf-8").read()
    hd = html[html.index("<title>"):html.index("<script>")].replace("<title>인물 정의 판정</title>", "<title>엔게디 마주 봄 판정</title>")
    hd = hd.replace("</style>", L.CSS + "</style>")
    data = {k: L.uri(Image.open(p).convert("RGB"), L.CARD * L.DPR) for k, p in imgs.items()}
    picked = f"엔게디 마주 봄 · 처치 B1·B2 + 대조 A + 참고 B + 기준 · 시드 {params.REF_EDIT_SEEDS} · 카드 폭 356px · 기계 거르기 없음"
    js = L.JS.replace("lora-scene-357", "engedi-away-366-judge").replace("task 357 사람 판정", "task 366 사람 판정")
    assert ZOOM_JS[0] in js
    js = js.replace(*ZOOM_JS)
    page = (hd + "<script>\nconst SCREENS = " + json.dumps(sc, ensure_ascii=False) + ";\nconst IMGS = " + json.dumps(data)
            + ";\nconst PICKED = " + json.dumps(picked, ensure_ascii=False) + ";\n" + js + "\n</body></html>\n")
    open(dst, "w", encoding="utf-8").write(page)
    order = [{"n": n + 1, "kind": t["kind"], "seed": t["seed"]} for n, t in enumerate(its)]
    m["screens"] = {sid: order for sid, *_ in AWAY_SCREENS}
    json.dump(m, open(W.METRICS, "w"), ensure_ascii=False, indent=1)
    print(dst, f"{len(page) / 1e6:.2f}MB, 화면 {len(sc)}, 그림 {len(imgs)}")


def main_backhand(src, dst):
    """task#367 — 366 화면 4개 그대로(AWAY_SCREENS), 기준 + A 8 + B 8 + B′ 8 + Bh 8 = 33장을 한 번 섞어 네 화면 같은 순서."""
    import gen_engedi_backhand as W
    import gen_prompt_512 as P
    m = json.load(open(W.METRICS))
    imgs = {}

    def img(path):
        assert os.path.exists(path), path
        k = f"i{len(imgs)}"
        imgs[k] = path
        return k

    its = [{"kind": "ref", "seed": None, "path": REFS["engedi"]}]
    its += [{"kind": t, "seed": s, "path": W.out_path(t, s)} for t in W.ARMS for s in params.REF_EDIT_SEEDS]
    random.Random(params.ENGEDI_BACKHAND_SHUFFLE_SEED).shuffle(its)
    keys = [img(t["path"]) for t in its]
    ar = P.SIZE[1] / P.SIZE[0]
    sc = []
    for sid, q, look, zoom in AWAY_SCREENS:
        cards = lambda n: [{"img": keys[n], "marks": [], "cap": ""}] + (
            [{"img": keys[n], "marks": [], "cap": "다윗 쪽 확대", "zoom": list(ZOOM), "ar": ar}] if zoom else [])
        sc.append({"id": sid, "q": f"{SC_NAME['engedi']} · {q}", "look": look,
                   "items": [{"key": str(n + 1), "label": f"그림 {n + 1}", "cards": cards(n)} for n in range(len(its))],
                   "mark": "✗"})
    html = open(src, encoding="utf-8").read()
    hd = html[html.index("<title>"):html.index("<script>")].replace("<title>인물 정의 판정</title>", "<title>엔게디 등·손 판정</title>")
    hd = hd.replace("</style>", L.CSS + "</style>")
    data = {k: L.uri(Image.open(p).convert("RGB"), L.CARD * L.DPR) for k, p in imgs.items()}
    picked = f"엔게디 마주 봄 귀속·손 · 처치 Bh + 귀속 B′ + 대조 A + 참고 B + 기준 · 시드 {params.REF_EDIT_SEEDS} · 카드 폭 356px · 기계 거르기 없음"
    js = L.JS.replace("lora-scene-357", "engedi-backhand-367-judge").replace("task 357 사람 판정", "task 367 사람 판정")
    assert ZOOM_JS[0] in js
    js = js.replace(*ZOOM_JS)
    page = (hd + "<script>\nconst SCREENS = " + json.dumps(sc, ensure_ascii=False) + ";\nconst IMGS = " + json.dumps(data)
            + ";\nconst PICKED = " + json.dumps(picked, ensure_ascii=False) + ";\n" + js + "\n</body></html>\n")
    open(dst, "w", encoding="utf-8").write(page)
    order = [{"n": n + 1, "kind": t["kind"], "seed": t["seed"]} for n, t in enumerate(its)]
    m["screens"] = {sid: order for sid, *_ in AWAY_SCREENS}
    json.dump(m, open(W.METRICS, "w"), ensure_ascii=False, indent=1)
    print(dst, f"{len(page) / 1e6:.2f}MB, 화면 {len(sc)}, 그림 {len(imgs)}")


def main():
    mode, src, dst = sys.argv[1:4]
    if mode == "judge-backhand":
        return main_backhand(src, dst)
    if mode == "judge-away":
        return main_away(src, dst)
    if mode == "judge-gaze":
        return main_gaze(src, dst)
    if mode == "judge-dark":
        return main_dark(src, dst)
    if mode == "judge-costume":
        return main_costume(src, dst)
    if mode == "judge-text":
        return main_text(src, dst)
    if mode == "judge-512":
        return main_512(src, dst)
    v2511 = mode in VARIANTS
    if v2511:
        mod, shuffle, task, desc = VARIANTS[mode]
        R = __import__(mod)
    metrics = R.METRICS if v2511 else G.METRICS
    m = json.load(open(metrics))
    html = open(src, encoding="utf-8").read()
    title = "편집 세기 고르기" if mode == "preview" else "정본 참조 편집 판정"
    hd = html[html.index("<title>"):html.index("<script>")].replace("<title>인물 정의 판정</title>", f"<title>{title}</title>")
    hd = hd.replace("</style>", L.CSS + "</style>")
    sc, imgs, ident = build(m, mode, R.OUT, shuffle) if v2511 else build(m, mode)
    data = {k: L.uri(Image.open(p).convert("RGB"), L.CARD * L.DPR) for k, p in imgs.items()}
    if v2511:
        picked = desc.format(name=R.NAME, q=m["quantize"]) + f" · 시드 {params.REF_EDIT_SEEDS} · 카드 폭 356px · 기계 거르기 없음"
        js = L.JS.replace("lora-scene-357", f"ref-edit-{task}-judge").replace("task 357 사람 판정", f"task {task} 사람 판정")
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
