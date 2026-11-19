"""task 662 — 비교 문항(장면 뿔 크롭 ↔ 기름 뿔 정본) 검증: 결함 그림을 잡고 정본 꼴 그림은 통과시키는지 먼저 본다.
  python3 batch/horn_compare_check.py crops   # 크롭 모아 보기(눈 확인) → $CLAUDE_JOB_DIR/tmp 또는 /tmp
  python3 batch/horn_compare_check.py judge   # claude -p Sonnet × 3회 → samples/horn-compare/metrics.json
  python3 batch/horn_compare_check.py report
  python3 batch/horn_compare_check.py scene <고정 절> <그림> <시드> <x,y,w,h>   # 정본 얹은 장면: 장면 문항 + t.horn-canon"""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "batch"))
from PIL import Image
import judge_items as J
REF = "frozen/props/oil-horn.png"
Q = {"id": "t.horn-canon", "who": "horn", "ref": REF,
     "q": "크롭 속 기름 뿔이 기준 그림의 기름 뿔과 같은 물건(같은 꼴)인가? 크기·방향·각도·쥔 손에 가려진 부분은 달라도 된다.",
     "what": "맞음 = 굵고 완만하게 굽은, 윤기 나는 짙은 갈색 숫양 뿔(옅은 호박색 줄무늬·잔 골)이고, 넓은 밑동은 평평한 나무판으로 막힌 바닥이며(손에 가려질 수 있음 · task 673 정본), "
             "끝으로 갈수록 가늘어져 잘린 끝에 작은 구멍(마개는 빠졌거나 너무 작아 안 보일 수 있음)이 있고 기름은 그 끝에서 나온다. 틀림 = 금속·황동 나팔이나 깔때기, 옅은 상아색·흰 뿔, 매끈한 원뿔·관, 양 끝이 열린 U자 관, "
             "넓은 입이 열려 있음, 병·잔·항아리 등 다른 물건, 또는 뿔이 안 보임."}
SAMPLES = {   # 이름: (그림, 크롭 비율 x,y,w,h, 기대) — 기대: 틀림 = 결함을 잡아야 함 · 맞음 = 정본 꼴
    "beth-s42": ("samples/bethlehem-step23-t14/composition-A-s42.png", (0.28, 0.28, 0.18, 0.26), "틀림"),
    "beth-s7": ("samples/bethlehem-step23-t14/composition-A-s7.png", (0.32, 0.30, 0.20, 0.27), "틀림"),
    "beth-s5": ("samples/bethlehem-step23-t14/composition-A-s5.png", (0.31, 0.28, 0.18, 0.24), "틀림"),
    "beth-s11": ("samples/bethlehem-step23-t14/composition-A-s11.png", (0.34, 0.26, 0.15, 0.24), "틀림"),
    "beth-s23": ("samples/bethlehem-step23-t14/composition-A-s23.png", (0.33, 0.26, 0.16, 0.26), "틀림"),
    "beth-s101": ("samples/bethlehem-step23-t14/composition-A-s101.png", (0.35, 0.32, 0.16, 0.22), "틀림"),
    "beth-s202": ("samples/bethlehem-step23-t14/composition-A-s202.png", (0.28, 0.26, 0.17, 0.25), "틀림"),
    "beth-s303": ("samples/bethlehem-step23-t14/composition-A-s303.png", (0.33, 0.24, 0.17, 0.24), "틀림"),
    "gihon-s101": ("samples/gihon-step23-t15/composition-A-s101.png", (0.37, 0.38, 0.16, 0.26), "틀림"),
    "prop-snug4": ("samples/prop-oil-horn-lying/mouth-linensnug-s4.png", (0, 0, 1, 1), "맞음"),
    "prop-fix20": ("samples/prop-oil-horn-lying/fix-0.2.png", (0, 0, 1, 1), "맞음"),
    "prop-s23": ("samples/prop-oil-horn-lying/sheet-s23.png", (0, 0, 1, 1), None),
}
OUT = os.path.join(HERE, "samples", "horn-compare"); METRICS = os.path.join(OUT, "metrics.json")


def item(name):
    src, box, _ = SAMPLES[name]
    q = dict(Q, crop={"0": list(box)})
    return {"task": "horn-compare", "scene": name, "title": "기름 뿔 비교", "range": "삼상 16:13", "seed": 0,
            "src": os.path.join(HERE, src), "qs": [q], "qids": [q["id"]]}


def crops():
    tiles = []
    for n, (src, (x, y, w, h), _) in SAMPLES.items():
        im = Image.open(os.path.join(HERE, src)).convert("RGB"); W, H = im.size
        c = im.crop((round(x * W), round(y * H), round((x + w) * W), round((y + h) * H))); c.thumbnail((300, 300)); tiles.append(c)
    sheet = Image.new("RGB", (1200, 300 * ((len(tiles) + 3) // 4)), (255, 255, 255))
    for i, c in enumerate(tiles):
        sheet.paste(c, ((i % 4) * 300, (i // 4) * 300))
    p = os.path.join(os.environ.get("CLAUDE_JOB_DIR", "/tmp"), "tmp", "horn-crops.png") if os.environ.get("CLAUDE_JOB_DIR") else "/tmp/horn-crops.png"
    sheet.save(p); print(p)


def ask(name, rep, m):
    it = item(name); d, files = J.prepare(it, "horn-compare")
    o = J.call(J.prompt(it, files, J.HEADERS["v2"]), d, "sonnet")
    got = None if o.get("is_error") else J.parse(o.get("result"), it["qids"])
    m.setdefault(name, {})[str(rep)] = got or {"answers": None}


def judge():
    os.makedirs(OUT, exist_ok=True)
    m = json.load(open(METRICS)) if os.path.exists(METRICS) else {}
    todo = [(n, r) for n in SAMPLES for r in (1, 2, 3) if not ((m.get(n) or {}).get(str(r)) or {}).get("answers")]
    with ThreadPoolExecutor(6) as ex:
        list(ex.map(lambda j: ask(*j, m), todo))
    json.dump(m, open(METRICS, "w"), ensure_ascii=False, indent=1); report()


def report():
    m = json.load(open(METRICS))
    for n, (_, _, want) in SAMPLES.items():
        reps = [r for r in (m.get(n) or {}).values() if r.get("answers")]
        ok = sum(r["answers"][Q["id"]] == "맞음" for r in reps)
        why = next((r["reasons"].get(Q["id"]) for r in reps if r.get("reasons")), "")
        print(f"{n:11} 맞음 {ok}/{len(reps)} 기대 {want or '-'} · {str(why)[:110]}")

def scene(fixed_n, src, seed, box, reps=3):
    """task 663 — 정본을 얹은 장면 한 장: 고정 절 fixed_n의 장면 문항 전부 + t.horn-canon(크롭 box) × reps → 거르기 문항 다수결 틀림 목록."""
    import rule_ab as R
    R.use(int(fixed_n)); case = R.FX["cases"][0]
    qs = [dict(q) for q in case["qs"]] + [dict(Q, crop={str(seed): list(box)})]
    for q in qs:
        if q.get("who") and str(seed) not in q.get("crop", {}):
            sys.exit(f"[HornCompare] {q['id']} 크롭에 시드 {seed} 없음")
    spec = R.D.load(case["scene"])
    import hashlib   # 판정 폴더를 그림마다 따로 — 장면·시드만으로 이름 지으면 같은 장면 두 그림이 full.jpg를 나눠 씀(663 원본 기준 판정이 out-0.2를 봄)
    tag = hashlib.sha1(src.encode()).hexdigest()[:8]
    it = {"task": "horn-canon-scene-" + tag, "scene": spec["id"], "title": spec["title"], "range": spec["verses"]["range"], "seed": seed,
          "src": os.path.join(HERE, src), "qs": qs, "qids": [q["id"] for q in qs]}
    d, files = J.prepare(it, "horn-compare")
    text = J.prompt(it, files, J.HEADERS["v2"])
    with ThreadPoolExecutor(reps) as ex:
        outs = list(ex.map(lambda _: J.call(text, d, "sonnet"), range(reps)))
    got = [g for g in (None if o.get("is_error") else J.parse(o.get("result"), it["qids"]) for o in outs) if g]
    gated = [q["id"] for q in J.gating(qs)]
    bad = [q for q in gated if 2 * sum(g["answers"][q] == "맞음" for g in got) <= len(got)]
    m = json.load(open(METRICS)) if os.path.exists(METRICS) else {}
    m["scene:" + src] = {"answers": got, "bad": bad}
    json.dump(m, open(METRICS, "w"), ensure_ascii=False, indent=1)
    print(f"[HornCompare] 판정 {len(got)}/{reps} · 틀린 거르기 {len(bad)}: {bad}")
    for q in bad:
        print(" ", q, "·", next((g["reasons"].get(q) for g in got if g["answers"][q] == "틀림" and g.get("reasons")), ""))


if sys.argv[1] == "scene":
    scene(sys.argv[2], sys.argv[3], int(sys.argv[4]), tuple(float(v) for v in sys.argv[5].split(",")))
else:
    {"crops": crops, "judge": judge, "report": report}[sys.argv[1]]()
