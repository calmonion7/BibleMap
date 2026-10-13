"""build_anim.py <scene> [명세id]: 장면 명세 + 층 PNG → 데이터 JSON + 단독 HTML. 장면별 손작업 0."""
import sys, os, json, base64, glob
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); CANON = os.path.dirname(HERE)
R = os.path.join(CANON, "..", "..", ".forge", "reports", "scene-batch-pilot")

def area(b): return (b[2] - b[0]) * (b[3] - b[1])

def build(scene, spec_id=None):
    spec = json.load(open(os.path.join(CANON, "scenes", (spec_id or scene) + ".json")))
    reg, figs = spec["regions"], spec["figures"]
    lay = os.path.join(R, scene, "layers")
    files = {os.path.splitext(f)[0]: f for f in os.listdir(lay) if f.lower().endswith((".png", ".webp"))}
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

if __name__ == "__main__":
    print(build(*sys.argv[1:3]))
