#!/usr/bin/env python3
"""task#356 — 인물 LoRA 학습 시트: 353 정본 초상 6장 + 정의 문구로 새로 그린 전신 단독 16장(사울·다윗·사무엘).

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV gen_lora_sheet.py gen [--who saul] [--test]        # 전신 생성(--test = 인물당 1장만)
  $VENV gen_lora_sheet.py write --drop drop.json           # 사람이 뺀 그림을 제외하고 캡션 쌍을 lora-sheet-v2/<id>/에 쓴다

전신 문구는 gen_face_canon.look(cid)(카드+얼굴 층, head_text 경유라 `bare head` 없음)에 전신·단독·자세를 붙인다.
캡션에는 트리거 낱말 + 「a man」 + 구도·자세·배경 낱말만 — 수염·나이·체격 같은 정체성 낱말은 넣지 않는다.
산출은 레포 밖(~/.local/biblemap-imggen/lora-sheet-v2-src/·lora-sheet-v2/). 생성은 한 번에 하나.
"""
import argparse, json, os, shutil, sys

import params
import derive_scene as ds
import gen_face_canon as g

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "batch"))
ROOT = os.path.expanduser("~/.local/biblemap-imggen")
SRC = os.path.join(ROOT, "lora-sheet-v2-src")     # 전신 후보(거르기 전)
SHEET = os.path.join(ROOT, "lora-sheet-v2")       # mflux 학습 데이터(NN.png + NN.txt)
FACE = os.path.join(ROOT, "cast-v2-pilot", "face")
PORTRAIT_CAP = {"front": "close-up head portrait, facing forward, plain cream background",
                "34": "close-up head portrait, three-quarter view, plain cream background"}


def body_prompt(cid, pose, extra=""):
    """look()는 머리 초상용이라 카드 층 체격(silhouette)·키(heightRel)가 없다 — 전신은 체격을 실어야 하므로 더한다."""
    card = ds.load_cast(cid)["card"]
    body = [card["silhouette"]["text"]] + ([ds.HEIGHT[card["heightRel"]]] if card["heightRel"] in ds.HEIGHT else [])
    pose_t = params.LORA_SHEET_POSES[pose] + (f", {extra}" if extra else "")
    return (f"{g.STYLE}, full body, single figure, {pose_t}, plain light background. "
            f"{g.look(cid)}, {', '.join(body)}, whole figure from head to feet.")


def body_items(cid):
    """→ [(파일 키, 경로, 캡션 꼬리)] 전신 후보, 시드 순(자세 묶음 안에서). 수리 r1의 되붙인 전신(paste-*)은 있으면 뒤에 붙는다."""
    cap = lambda pose: f"full body, single figure, {params.LORA_SHEET_POSES[pose]}, plain light background"
    items = [(f"{pose}-s{s}", os.path.join(SRC, cid, f"{pose}-s{s}.png"), cap(pose))
             for pose in params.LORA_SHEET_POSES for s in params.LORA_SHEET_BODY_SEEDS]
    pose = params.LORA_SHEET_PASTE_POSE
    items += [(f"paste-{pose}-s{s}", p, cap(pose)) for s in params.LORA_SHEET_BODY_SEEDS
              if os.path.exists(p := os.path.join(SRC, cid, f"paste-{pose}-s{s}.png"))]
    return items + [(f"paste-{pose}2-s{s}", p, cap(pose)) for s in params.LORA_SHEET_R2_SEEDS.get(cid, [])   # 수리 r2
                    if os.path.exists(p := os.path.join(SRC, cid, f"paste-{pose}2-s{s}.png"))]


def _face(path):
    """단독 인물 그림의 얼굴 상자(OWLv2 최고 점수 「a face/head」) → (x0,y0,x1,y1)."""
    from face_ab_heads import _faces
    from PIL import Image
    im = Image.open(path).convert("RGB")
    return max(_faces(im), key=lambda f: f[1])[0], im


def gen_r2(who, test):
    """수리 r2 — 사실 비율 문구로 정면 서기 전신을 새 시드로 그린다 → <pose>2-s<시드>.png."""
    import run_scene
    w, h = params.LORA_SHEET_BODY_SIZE
    pose = params.LORA_SHEET_PASTE_POSE
    jobs = [{"prompt": body_prompt(cid, pose, params.LORA_SHEET_R2_PROP), "seed": s, "w": w, "h": h,
             "out": os.path.join(SRC, cid, f"{pose}2-s{s}.png")} for cid in who
            for s in (params.LORA_SHEET_R2_SEEDS[cid][:1] if test else params.LORA_SHEET_R2_SEEDS[cid])
            if not os.path.exists(os.path.join(SRC, cid, f"{pose}2-s{s}.png"))]
    print(f"[LoraSheet] r2 {body_prompt(who[0], pose, params.LORA_SHEET_R2_PROP)}\n  {len(jobs)}장 생성", flush=True)
    if jobs:
        secs = run_scene.gen_zimage(jobs, SRC)
        print(f"[LoraSheet] r2 완료 {len(secs)}장 합 {sum(secs):.0f}s", flush=True)


def paste(who, r2=False):
    """수리 r1(r2) — 문구 전신(정면 서기)의 머리 자리에 정본 정면 머리를 크기·위치 맞춰 옮긴 뒤 347 R1(paste_heads)로 붙인다."""
    from PIL import Image
    import face_ab_heads as fh
    from gen_face_style import paste_heads
    pose = params.LORA_SHEET_PASTE_POSE + ("2" if r2 else "")
    for cid in who:
        for n, s in enumerate(params.LORA_SHEET_R2_SEEDS[cid] if r2 else params.LORA_SHEET_BODY_SEEDS):
            if not os.path.exists(os.path.join(SRC, cid, f"{pose}-s{s}.png")):
                continue
            cs = params.LORA_SHEET_PASTE_CANON_SEEDS[n % len(params.LORA_SHEET_PASTE_CANON_SEEDS)]
            (bx0, by0, bx1, by1), body = _face(os.path.join(SRC, cid, f"{pose}-s{s}.png"))
            (cx0, cy0, cx1, cy1), canon = _face(os.path.join(FACE, cid, f"s{cs}-front.png"))
            k = (bx1 - bx0) / (cx1 - cx0)                       # 얼굴 폭을 맞춘다
            small = canon.resize((round(canon.width * k), round(canon.height * k)), Image.LANCZOS)
            aligned = body.copy()                                # 정본 얼굴 중심을 전신 얼굴 중심에 둔다
            aligned.paste(small, (round((bx0 + bx1) / 2 - (cx0 + cx1) / 2 * k), round((by0 + by1) / 2 - (cy0 + cy1) / 2 * k)))
            fx, fy, fw, fh_ = (bx0 + bx1) / 2, (by0 + by1) / 2 - fh.LIFT * (by1 - by0), (bx1 - bx0) * fh.GROW, (by1 - by0) * fh.GROW
            hb = {cid: (fx - fw / 2, fy - fh_ / 2, fx + fw / 2, fy + fh_ / 2)}
            out = os.path.join(SRC, cid, f"paste-{pose}-s{s}.png")
            paste_heads(body, aligned, hb, [cid], params.LORA_SHEET_PASTE_GROW, f"{cid} s{s}").save(out)
            print(f"[LoraSheet] 되붙임 {cid} s{s} ← 정본 s{cs} 배율 {k:.3f}", flush=True)


def portrait_items(cid):
    return [(f"face-s{s}-{v}", os.path.join(FACE, cid, f"s{s}-{v}.png"), PORTRAIT_CAP[v])
            for s in params.LORA_SHEET_PORTRAIT_SEEDS for v in ("front", "34")]


def gen(who, test):
    import run_scene
    w, h = params.LORA_SHEET_BODY_SIZE
    jobs = []
    for cid in who:
        os.makedirs(os.path.join(SRC, cid), exist_ok=True)
        poses = list(params.LORA_SHEET_POSES)[:1] if test else params.LORA_SHEET_POSES
        seeds = params.LORA_SHEET_BODY_SEEDS[:1] if test else params.LORA_SHEET_BODY_SEEDS
        for pose in poses:
            for s in seeds:
                out = os.path.join(SRC, cid, f"{pose}-s{s}.png")
                if not os.path.exists(out):
                    jobs.append({"prompt": body_prompt(cid, pose), "seed": s, "w": w, "h": h, "out": out})
        print(f"[LoraSheet] {cid}: {body_prompt(cid, 'stand')}", flush=True)
    print(f"[LoraSheet] {len(jobs)}장 생성", flush=True)
    if jobs:
        secs = run_scene.gen_zimage(jobs, SRC)
        print(f"[LoraSheet] 완료 {len(secs)}장 합 {sum(secs):.0f}s", flush=True)


def parse_answer(text):
    """판정 페이지 문장(「- 사울 · … → 뺌: face-s11-34, stand-s42」 / 「→ 모두 맞음」) → drop dict. 미답이 있으면 멈춘다."""
    name = {"사울": "saul", "다윗": "david", "사무엘": "samuel"}
    drop = {}
    for line in text.splitlines():
        if not line.startswith("- ") or "→" not in line:
            continue
        who = name[line[2:].split(" ·")[0].strip()]
        ans = line.split("→", 1)[1].strip()
        assert ans != "(미답)", f"{who} 미답"
        drop[who] = [k.strip() for k in ans[len("뺌:"):].split(",")] if ans.startswith("뺌:") else []
    assert set(drop) == set(params.LORA_SHEET_WHO), drop
    return drop


def write(drop):
    """drop = {id: [파일 키, ...]} — 사람이 「안 맞음」으로 표시한 것. 남은 전신은 시드 순 최대 BODY_MAX장."""
    report = {}
    for cid in params.LORA_SHEET_WHO:
        bad = set(drop.get(cid, []))
        faces = [it for it in portrait_items(cid) if it[0] not in bad]
        bodies = [it for it in body_items(cid) if it[0] not in bad and os.path.exists(it[1])]
        # 시드 순(자세 번갈아) — 한 자세로만 채워지지 않게
        order = {s: i for i, s in enumerate(params.LORA_SHEET_BODY_SEEDS)}
        seed = lambda k: int(k.rsplit("-s", 1)[1])
        bodies.sort(key=lambda it: (order.get(seed(it[0]), len(order) + seed(it[0])), it[0]))
        kept = bodies[:params.LORA_SHEET_BODY_MAX]
        d = os.path.join(SHEET, cid)
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
        trig = params.LORA_SHEET_TRIGGER[cid]
        for n, (key, path, tail) in enumerate(faces + kept, 1):
            shutil.copy(path, os.path.join(d, f"{n:02d}.png"))
            open(os.path.join(d, f"{n:02d}.txt"), "w").write(f"{trig}, a man, {tail}")
        report[cid] = {"portraits": len(faces), "bodies_left": len(bodies), "bodies_used": len(kept),
                       "under_min": len(bodies) < params.LORA_SHEET_BODY_MIN, "files": [k for k, _, _ in faces + kept]}
        print(f"[LoraSheet] {cid}: 초상 {len(faces)} + 전신 {len(kept)}(남은 {len(bodies)})", flush=True)
    json.dump(report, open(os.path.join(SHEET, "sheet.json"), "w"), ensure_ascii=False, indent=1)
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("gen", "gen2", "paste", "paste2", "write"))
    ap.add_argument("--who", nargs="+", default=list(params.LORA_SHEET_WHO))
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--drop", help="drop.json 또는 판정 문장 텍스트 파일")
    a = ap.parse_args()
    if a.cmd == "gen":
        gen(a.who, a.test)
    elif a.cmd == "gen2":
        gen_r2([w for w in a.who if w in params.LORA_SHEET_PASTE_WHO], a.test)
    elif a.cmd in ("paste", "paste2"):
        paste([w for w in a.who if w in params.LORA_SHEET_PASTE_WHO], a.cmd == "paste2")
    else:
        t = open(a.drop).read() if a.drop else "{}"
        write(json.loads(t) if t.lstrip().startswith("{") else parse_answer(t))
