#!/usr/bin/env python3
"""task#350 — 얼굴 인식 판정자(ArcFace)를 `.identity` 사람 라벨로 교정: 정본 얼굴과 사람이 본 머리 크롭의 코사인.

  ~/.local/biblemap-imggen/.venv314/bin/python judge_face_id.py controls   # 음성·양성 대조 → metrics controls
  ~/.local/biblemap-imggen/.venv314/bin/python judge_face_id.py judge      # 다듬기로 τ → 검증 판정 → metrics + notes 결과 절

규칙은 notes/FACE-ID-JUDGE.md 고정 절, 상수는 params.FACE_ID_*. 문항·라벨·머리 크롭은 사람 페이지 identity 문항 그대로
(batch/judge_items.py와 같은 페이지·라벨 규칙). 얼굴을 못 찾으면 점수 없음 = 기계 답 「다른 사람」."""
import glob, json, math, os, sys

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "batch"))
import judge_items as J  # noqa: E402
import params as P  # noqa: E402

METRICS = os.path.join(HERE, "samples", "face-id", "metrics.json")
NOTES = os.path.join(HERE, "notes", "FACE-ID-JUDGE.md")
FROZEN = os.path.join(HERE, "frozen")
EMBEDDER = "insightface buffalo_l (det_10g + 5점 정렬 + w600k_r50 ArcFace), 긴 변 512px로 맞춘 뒤 검출, 가장 큰 얼굴"
LONG = 512
_app = None


def app():
    global _app
    if _app is None:
        from insightface.app import FaceAnalysis
        _app = FaceAnalysis(name="buffalo_l", allowed_modules=["detection", "recognition"], providers=["CPUExecutionProvider"])
        _app.prepare(ctx_id=-1, det_size=(640, 640))
    return _app


def largest(im):
    """PIL → (가장 큰 얼굴, 맞춘 배율) 또는 (None, 배율). 긴 변 512px로 맞춘 뒤 검출."""
    k = LONG / max(im.size)
    im = im.convert("RGB").resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    faces = app().get(cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR))
    if not faces:
        return None, k
    return max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])), k


def embed(im):
    f, _ = largest(im)
    return None if f is None else f.normed_embedding


def cos(a, b):
    return None if a is None or b is None else round(float(np.dot(a, b)), 4)


def canon_embed(name, cache={}):
    if name not in cache:
        cache[name] = embed(Image.open(os.path.join(FROZEN, f"{name}.png")))
    return cache[name]


def variants(name):
    im = Image.open(os.path.join(FROZEN, f"{name}.png")).convert("RGB")
    out = {"flip": ImageOps.mirror(im), "bright+20": ImageEnhance.Brightness(im).enhance(1.2),
           "bright-20": ImageEnhance.Brightness(im).enhance(0.8)}
    f, k = largest(im)
    if f is not None:   # 검출된 얼굴 높이(원본 화소)가 장면 머리 크기가 되게 줄였다가 되돌림
        s = P.FACE_ID_SCENE_HEAD_PX / ((f.bbox[3] - f.bbox[1]) / k)
        small = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
        out["down48"] = small.resize(im.size, Image.LANCZOS)
    return out


def same_person(a, b):
    return any(a in g and b in g for g in P.FACE_ID_SAME_PERSON)


def labels(set_name):
    """→ [{key, task, scene, qid, canon, seed, label}] — label = 「다른 사람」(사람이 틀림으로 누름) / 「같은 사람」."""
    out = []
    for task in P.FACE_ID_SETS[set_name]:
        d, fn, edited = J.TASKS[task]
        m = json.load(open(os.path.join(HERE, "samples", d, "metrics.json")))
        for s in J.page_scenes(fn):
            sc = m["scenes"][s["id"]]
            rec = sc.get("items") or {}
            by = {x["seed"]: x for x in sc["seeds"]}
            for q in s["qs"]:
                r = rec.get(q["id"])
                if not q["id"].endswith(".identity") or q.get("grp") == "plate" or not r or r.get("unsure") or r.get("skipped") or r.get("auto"):
                    continue
                for seed in s["seeds"]:
                    x = by[seed]
                    out.append({"key": f"{task}:{s['id']}:{q['id']}:{seed}", "task": task, "scene": s["id"], "qid": q["id"],
                                "canon": q["canon"], "seed": seed, "src": x["edits"][sc["who"][-1]] if edited else x["base"],
                                "crop": q["crop"][str(seed)], "label": "다른 사람" if seed in r["wrong"] else "같은 사람"})
    return out


def head(it):
    im = Image.open(it["src"]).convert("RGB")
    x, y, w, h = it["crop"]
    if max(x, y, w, h) > 1.0 or min(x, y, w, h) < 0:
        raise ValueError(f"[FaceId] crop은 그림 크기 비율(0~1)이어야 한다: {it['key']} {it['crop']}")
    W, H = im.size
    return im.crop((round(x * W), round(y * H), round((x + w) * W), round((y + h) * H)))


def score_set(set_name):
    out = []
    for it in labels(set_name):
        e = embed(head(it))
        out.append({k: it[k] for k in ("key", "task", "scene", "qid", "canon", "seed", "label")} | {"score": cos(canon_embed(it["canon"]), e)})
    return out


def load():
    return json.load(open(METRICS)) if os.path.exists(METRICS) else {}


def save(m):
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    json.dump(m, open(METRICS, "w"), ensure_ascii=False, indent=1)


def controls():
    canons = sorted({it["canon"] for s in P.FACE_ID_SETS for it in labels(s)})
    others = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(FROZEN, "*.png")))
    neg = [{"canon": c, "other": o, "score": cos(canon_embed(c), canon_embed(o))}
           for c in canons for o in others if o != c and not same_person(c, o)]
    pos = []
    for c in canons:
        vs = variants(c)
        pos += [{"canon": c, "variant": v, "score": cos(canon_embed(c), embed(vs[v])) if v in vs else None} for v in P.FACE_ID_POS_VARIANTS]
    m = load()
    m.update({"task": 350, "embedder": EMBEDDER, "controls": {
        "neg": neg, "pos": pos,
        "det_fail": {"canon": [n for n in others if canon_embed(n) is None],
                     "pos": sum(1 for x in pos if x["score"] is None)}}})
    save(m)
    print(f"[FaceId] 대조: 음성 {len(neg)}쌍 · 양성 {len(pos)}쌍 · 정본 검출 실패 {m['controls']['det_fail']['canon']} · 양성 검출 실패 {m['controls']['det_fail']['pos']}")


def machine(score, tau):
    return "다른 사람" if score is None or score < tau else "같은 사람"


def rates(rows, tau):
    d = [r for r in rows if r["label"] == "다른 사람"]
    s = [r for r in rows if r["label"] == "같은 사람"]
    c = sum(1 for r in d if machine(r["score"], tau) == "다른 사람")
    p = sum(1 for r in s if machine(r["score"], tau) == "같은 사람")
    return {"catch": round(c / len(d), 4) if d else None, "pass": round(p / len(s), 4) if s else None,
            "catch_n": f"{c}/{len(d)}", "pass_n": f"{p}/{len(s)}",
            "machine_diff": round(sum(1 for r in rows if machine(r["score"], tau) == "다른 사람") / len(rows), 4)}


def pick_tau(rows):
    xs = sorted({r["score"] for r in rows if r["score"] is not None})
    cands = [xs[0] - 1e-4] + [(a + b) / 2 for a, b in zip(xs, xs[1:])] + [xs[-1] + 1e-4]
    best = max(cands, key=lambda t: (min(rates(rows, t)["catch"], rates(rows, t)["pass"]), rates(rows, t)["catch"]))
    return round(best, 4)


def auc(rows):
    """「다른 사람」을 낮은 점수로 가르는 AUC(점수 없음 = 가장 낮음)."""
    v = lambda r: -9 if r["score"] is None else r["score"]
    d = [v(r) for r in rows if r["label"] == "다른 사람"]
    s = [v(r) for r in rows if r["label"] == "같은 사람"]
    return round(sum((a < b) + 0.5 * (a == b) for a in d for b in s) / (len(d) * len(s)), 4)


def wilson_low(n_str, z=1.96):
    k, n = map(int, n_str.split("/"))
    if not n:
        return None
    p = k / n
    return round((p + z * z / (2 * n) - z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n), 4)


def by_canon(rows, tau):
    out = {}
    for c in sorted({r["canon"] for r in rows}):
        x = rates([r for r in rows if r["canon"] == c], tau)
        out[c] = {"catch_n": x["catch_n"], "pass_n": x["pass_n"]}
    return out


def judge():
    m = load()
    if "controls" not in m:
        sys.exit("[FaceId] controls를 먼저 돌린다")
    dev, hold = score_set("dev"), score_set("holdout")
    tau = pick_tau(dev)
    ds, hs = rates(dev, tau), rates(hold, tau)
    pos, neg = m["controls"]["pos"], m["controls"]["neg"]
    go = {"1_pos_all_ge_tau": all(x["score"] is not None and x["score"] >= tau for x in pos),
          "2_neg_all_lt_tau": all(x["score"] is None or x["score"] < tau for x in neg),
          "3_holdout_catch_ge_80": hs["catch"] >= P.FACE_ID_PASS_LINE,
          "4_holdout_pass_ge_80": hs["pass"] >= P.FACE_ID_PASS_LINE}
    m.update({"dev": dev, "holdout": hold, "tau": tau, "dev_score": ds, "holdout_score": hs, "go": go,
              "verdict": "go" if all(go.values()) else "no-go",
              "ref": {"dev_auc": auc(dev), "holdout_auc": auc(hold),
                      "holdout_wilson_low": {"catch": wilson_low(hs["catch_n"]), "pass": wilson_low(hs["pass_n"])},
                      "det_fail": {"dev": sum(1 for r in dev if r["score"] is None), "holdout": sum(1 for r in hold if r["score"] is None)},
                      "by_canon": {"dev": by_canon(dev, tau), "holdout": by_canon(hold, tau)},
                      "pos_min": min((x["score"] for x in pos if x["score"] is not None), default=None),
                      "neg_max": max((x["score"] for x in neg if x["score"] is not None), default=None),
                      "neg_over_tau": [f"{x['canon']}~{x['other']} {x['score']}" for x in neg if x["score"] is not None and x["score"] >= tau],
                      "pos_under_tau": [f"{x['canon']} {x['variant']} {x['score']}" for x in pos if x["score"] is None or x["score"] < tau]}})
    save(m)
    write_notes(m)
    print(f"[FaceId] τ={tau} · 다듬기 잡기 {ds['catch_n']} 통과 {ds['pass_n']} · 검증 잡기 {hs['catch_n']} 통과 {hs['pass_n']} · 판정 {m['verdict']}")


def pct(x):
    return "—" if x is None else f"{x * 100:.1f}%"


def write_notes(m):
    ds, hs, r, g = m["dev_score"], m["holdout_score"], m["ref"], m["go"]
    ok = lambda b: "✅" if b else "❌"
    lines = [
        "## 결과", "",
        f"- 판정자: {m['embedder']}",
        f"- **τ = {m['tau']}** (다듬기 묶음 min(잡기, 통과) 최대)",
        "",
        "| 묶음 | 잡기 | 통과 | 기계 「다른 사람」 비율 | AUC | 검출 실패 |",
        "|---|---|---|---|---|---|",
        f"| 다듬기 | {ds['catch_n']} {pct(ds['catch'])} | {ds['pass_n']} {pct(ds['pass'])} | {pct(ds['machine_diff'])} | {r['dev_auc']} | {r['det_fail']['dev']} |",
        f"| 검증 | {hs['catch_n']} {pct(hs['catch'])} | {hs['pass_n']} {pct(hs['pass'])} | {pct(hs['machine_diff'])} | {r['holdout_auc']} | {r['det_fail']['holdout']} |",
        "",
        "go 조건:",
        f"- ① 양성 대조 전부 ≥ τ — {ok(g['1_pos_all_ge_tau'])} (양성 최소 {r['pos_min']}, τ 밑: {', '.join(r['pos_under_tau']) or '없음'})",
        f"- ② 음성 대조 전부 < τ — {ok(g['2_neg_all_lt_tau'])} (음성 최대 {r['neg_max']}, τ 이상 {len(r['neg_over_tau'])}쌍{': ' + ', '.join(r['neg_over_tau'][:8]) if r['neg_over_tau'] else ''})",
        f"- ③ 검증 잡기 ≥ 80% — {ok(g['3_holdout_catch_ge_80'])} ({hs['catch_n']} {pct(hs['catch'])})",
        f"- ④ 검증 통과 ≥ 80% — {ok(g['4_holdout_pass_ge_80'])} ({hs['pass_n']} {pct(hs['pass'])})",
        "",
        "참고값(결론에 쓰지 않음):",
        f"- 검증 Wilson 95% 하한: 잡기 {pct(r['holdout_wilson_low']['catch'])} · 통과 {pct(r['holdout_wilson_low']['pass'])} (믿음 관문 80%)",
        f"- 한쪽 예측 확인: 기계 「다른 사람」 비율 다듬기 {pct(ds['machine_diff'])} · 검증 {pct(hs['machine_diff'])}"
        f" (사람 비율 다듬기 22/96 22.9% · 검증 27/96 28.1%) — {'한쪽으로만 예측함' if hs['machine_diff'] in (0, 1) or ds['machine_diff'] in (0, 1) else '양쪽 모두 예측함'}",
        f"- 정본 검출 실패: {', '.join(m['controls']['det_fail']['canon']) or '없음'} · 양성 검출 실패 {m['controls']['det_fail']['pos']}",
        "- 인물별(검증): " + " · ".join(f"{c} 잡기 {v['catch_n']} 통과 {v['pass_n']}" for c, v in r["by_canon"]["holdout"].items()),
        "- 인물별(다듬기): " + " · ".join(f"{c} 잡기 {v['catch_n']} 통과 {v['pass_n']}" for c, v in r["by_canon"]["dev"].items()),
        "",
        f"판정: {m['verdict']}",
        "",
    ]
    t = open(NOTES, encoding="utf-8").read()
    head_, _, _ = t.partition("## 결과")
    open(NOTES, "w", encoding="utf-8").write(head_ + "\n".join(lines))


if __name__ == "__main__":
    {"controls": controls, "judge": judge}[sys.argv[1]]()
