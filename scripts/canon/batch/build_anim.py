"""build_anim.py <scene> [명세id]: 장면 명세 + 층 PNG → 데이터 JSON + 단독 HTML. 장면별 손작업 0."""
import sys, os, json, base64, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); CANON = os.path.dirname(HERE)
R = os.path.join(CANON, "..", "..", ".forge", "reports", "scene-batch-pilot")

def area(b): return (b[2] - b[0]) * (b[3] - b[1])

def build(scene, spec_id=None):
    spec = json.load(open(os.path.join(CANON, "scenes", (spec_id or scene) + ".json")))
    reg, figs = spec["regions"], spec["figures"]
    lay = os.path.join(R, scene, "layers")
    files = {os.path.splitext(f)[0].removeprefix("fig-"): f for f in os.listdir(lay) if f.lower().endswith((".png", ".webp"))}
    bg = Image.open(os.path.join(lay, files["bg"]))
    # 단독 인물 판(run_scene.py 산출)은 배경과 크기가 다르다 → 알파 경계로 잘라 명세 상자 안에 바닥 중앙으로 앉힌 전체 화면 층으로 합성
    for f in figs:
        src = files.get(f["cast"])
        im = src and Image.open(os.path.join(lay, src)).convert("RGBA")
        if not im or im.size == bg.size: continue
        im = im.crop(im.getchannel("A").getbbox())
        b = reg[f["region"]]; bx, by = b[0] * bg.width, b[1] * bg.height
        bw_, bh_ = (b[2] - b[0]) * bg.width, (b[3] - b[1]) * bg.height
        k = min(bw_ / im.width, bh_ / im.height)
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        canvas = Image.new("RGBA", bg.size)
        canvas.alpha_composite(im, (round(bx + (bw_ - im.width) / 2), round(by + bh_ - im.height)))
        os.makedirs(os.path.join(R, scene, "anim"), exist_ok=True)
        files[f["cast"]] = os.path.join("..", "anim", f["cast"] + ".webp")
        canvas.save(os.path.join(R, scene, "anim", f["cast"] + ".webp"), quality=90)
    # 주인공 = 다윗이 있으면 다윗, 없으면 명세 첫 인물. 상대 = 나머지 중 상자가 가장 큰 인물.
    pro = next((f for f in figs if f["cast"] == "david"), figs[0])
    foe = max((f for f in figs if f is not pro), key=lambda f: area(reg[f["region"]]))
    casts = [f["cast"] for f in figs]
    # 깊이 순서(뒤→앞): 배경, 이름이 인물이 아닌 층, 명세 순서의 인물 판, 주인공이 맨 앞
    order = ["bg"] + sorted(k for k in files if k != "bg" and k not in casts) \
        + [c for c in casts if c in files and c != pro["cast"]] + ([pro["cast"]] if pro["cast"] in files else [])
    n = len(order) - 1
    def enc(f):
        mime = "image/webp" if f.endswith(".webp") else "image/png"
        return f"data:{mime};base64," + base64.b64encode(open(os.path.join(lay, f), "rb").read()).decode()
    layers = [{"src": enc(files[k]), "p": round(0.6 + 0.4 * i / max(n, 1), 2)} for i, k in enumerate(order)]
    w, h = Image.open(os.path.join(lay, files["bg"])).size
    def cam(f):
        b = reg[f["region"]]
        return {"c": (b[0] + b[2]) / 2, "y": (b[1] + b[3]) / 2, "s": round(min(1.8, max(1.1, 0.85 / (b[3] - b[1]))), 2)}
    data = {"title": spec["title"], "verse": spec["verses"]["range"], "aspect": w / h, "dur": 9000,
            "layers": layers, "cam": [cam(pro), cam(foe)]}
    out = os.path.join(R, scene, "anim.html")
    html = open(os.path.join(HERE, "anim_template.html")).read().replace("__DATA__", json.dumps(data, ensure_ascii=False))
    open(out, "w").write(html)
    json.dump({**data, "layers": [{**l, "src": k} for l, k in zip(layers, order)]}, open(os.path.join(R, scene, "anim.json"), "w"), ensure_ascii=False, indent=1)
    return out

RW = os.path.join(CANON, "..", "..", ".forge", "reports", "scene-whole-pilot")
VW, VH, MARGIN = 390, 844, 0.96   # 녹화 뷰포트(템플릿 draw()와 같은 식으로 보이는 영역을 계산)

def view(cam, aspect):
    """템플릿 draw()의 층 1장(p=1) 클램프를 그대로 옮겨 보이는 영역 [x0,y0,x1,y1](이미지 비율)을 낸다."""
    bw = VH * aspect; s = cam["s"]
    cx = min(max(cam["c"], VW / 2 / (bw * s)), 1 - VW / 2 / (bw * s)); cy = .5 if s < 1 else min(max(cam["y"], .5 / s), 1 - .5 / s)
    return [cx - VW / 2 / (bw * s), cy - .5 / s, cx + VW / 2 / (bw * s), cy + .5 / s]

def locate(scene, png, figs):
    """한 장 생성은 명세 상자를 따르지 않는다 → 실제 그림에서 인물별 상자(이미지 비율)를 `claude -p`로 읽어 캐시한다."""
    from judge_vlm import _claude, _json
    cache = os.path.join(os.path.dirname(png), "figboxes.json")
    if os.path.exists(cache): return json.load(open(cache))
    want = ", ".join(f"{f['cast']}({f['role']})" for f in figs)
    for _ in range(3):
        r = _json(_claude(f"Read 도구로 이미지 {png} 를 보고, 다음 인물 각각의 몸 전체(머리끝~발끝, 손에 쥔 큰 지물 제외, 땅에 엎드렸으면 그 몸 전체)를 감싸는 상자를 이미지 폭·높이에 대한 비율 [x0,y0,x1,y1]로 답하라: {want}. 설명 없이 JSON 한 개만: " + '{"<cast>": [x0,y0,x1,y1], ...}', png))
        if r and all(f["cast"] in r and len(r[f["cast"]]) == 4 for f in figs):
            json.dump(r, open(cache, "w"), ensure_ascii=False); return r
    raise SystemExit("인물 상자를 읽지 못함")

def build_whole(scene):
    """한 장 final.png를 층 1장으로 쓴다. 카메라 = 주인공 상자 → 상대 상자(상대 = 주인공이 gaze한 인물), 상자가 뷰포트에 온전히 들게 s를 정한다."""
    spec = json.load(open(os.path.join(CANON, "scenes", scene + ".json")))
    reg, figs = spec["regions"], spec["figures"]
    d = os.path.join(RW, scene); png = os.path.join(d, "final.png")
    w, h = Image.open(png).size; aspect = w / h; bw = VH * aspect
    pro = next((f for f in figs if f["cast"] == "david"), figs[0])
    foe = next((f for f in figs if f["cast"] == pro.get("gaze")), None) or max((f for f in figs if f is not pro), key=lambda f: area(reg[f["region"]]))
    boxes = locate(scene, png, figs)
    def cam(f):
        b = boxes[f["cast"]]
        # 폭 기준 맞춤 + 높이 기준 맞춤 중 작은 쪽, 하한 .5(1216×640 한 장은 인물 상자가 폰 폭보다 넓어 .85로는 잘림 — 남는 여백은 템플릿 배경색), 상한 1.8
        s = min(MARGIN * VW / (bw * (b[2] - b[0])), MARGIN / (b[3] - b[1]))
        return {"fig": f["cast"], "box": b, "c": (b[0] + b[2]) / 2, "y": (b[1] + b[3]) / 2, "s": round(max(.5, min(1.8, s)), 3)}
    cams = [cam(pro), cam(foe)]
    # 검사: 시작·중간·끝 키프레임(e=0, .5, 1)에서 카메라가 겨눈 인물 상자가 보이는 영역 안에 드는가
    res = []
    for e, name in ((0, "시작"), (.5, "중간"), (1, "끝")):
        a, b = cams
        c = {k: a[k] + (b[k] - a[k]) * e for k in ("c", "y", "s")}
        tgt = a if e < .5 else b if e > .5 else None
        v = view(c, aspect)
        for t in ([tgt] if tgt else [a]):   # 중간은 이동 중이라 상자 포함 대신 화면 중심이 두 인물 사이인지만 본다
            bx = t["box"]
            if e == .5: ok = min(a["c"], b["c"]) <= (v[0] + v[2]) / 2 <= max(a["c"], b["c"]); why = "중간(이동 중) 화면 중심이 두 인물 사이를 벗어남"
            else: ok = bx[0] >= v[0] - 1e-3 and bx[2] <= v[2] + 1e-3 and bx[1] >= v[1] - 1e-3 and bx[3] <= v[3] + 1e-3; why = f"{t['fig']} 상자가 뷰포트를 벗어남 (상자 {bx}, 보임 {[round(x, 3) for x in v]})"
            res.append({"t": name, "fig": t["fig"], "ok": ok, "why": "" if ok else why})
    data = {"title": spec["title"], "verse": spec["verses"]["range"], "aspect": aspect, "dur": 9000,
            "layers": [{"src": "data:image/png;base64," + base64.b64encode(open(png, "rb").read()).decode(), "p": 1}],
            "cam": [{k: c[k] for k in ("c", "y", "s")} for c in cams]}
    open(os.path.join(d, "anim.html"), "w").write(open(os.path.join(HERE, "anim_template.html")).read().replace("__DATA__", json.dumps(data, ensure_ascii=False)))
    json.dump({**data, "layers": [{"p": 1, "src": "final.png"}], "cams": cams, "check": res}, open(os.path.join(d, "anim.json"), "w"), ensure_ascii=False, indent=1)
    return res

if __name__ == "__main__":
    if sys.argv[1] == "--whole": print(build_whole(sys.argv[2]))
    else: print(build(*sys.argv[1:3]))
