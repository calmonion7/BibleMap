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


def body_prompt(cid, pose):
    """look()는 머리 초상용이라 카드 층 체격(silhouette)·키(heightRel)가 없다 — 전신은 체격을 실어야 하므로 더한다."""
    card = ds.load_cast(cid)["card"]
    body = [card["silhouette"]["text"]] + ([ds.HEIGHT[card["heightRel"]]] if card["heightRel"] in ds.HEIGHT else [])
    return (f"{g.STYLE}, full body, single figure, {params.LORA_SHEET_POSES[pose]}, plain light background. "
            f"{g.look(cid)}, {', '.join(body)}, whole figure from head to feet.")


def body_items(cid):
    """→ [(파일 키, 경로, 캡션 꼬리)] 전신 후보, 시드 순(자세 묶음 안에서)."""
    return [(f"{pose}-s{s}", os.path.join(SRC, cid, f"{pose}-s{s}.png"),
             f"full body, single figure, {params.LORA_SHEET_POSES[pose]}, plain light background")
            for pose in params.LORA_SHEET_POSES for s in params.LORA_SHEET_BODY_SEEDS]


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
        bodies.sort(key=lambda it: (order[int(it[0].split("-s")[1])], it[0]))
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
    ap.add_argument("cmd", choices=("gen", "write"))
    ap.add_argument("--who", nargs="+", default=list(params.LORA_SHEET_WHO))
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--drop", help="drop.json 또는 판정 문장 텍스트 파일")
    a = ap.parse_args()
    if a.cmd == "gen":
        gen(a.who, a.test)
    else:
        t = open(a.drop).read() if a.drop else "{}"
        write(json.loads(t) if t.lstrip().startswith("{") else parse_answer(t))
