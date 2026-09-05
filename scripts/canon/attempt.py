#!/usr/bin/env python3
"""[[단계 시도]] 실행기 — 한 단계를 한 번 그린다 (2026-09-05, task 338).

승인된 앞 단계 그림 **위에서** 이어 그리고, 무엇을 어떤 입력으로 그렸는지 곁파일에 적는다.
곁파일이 있어야 나중에 「이 승인은 지금 명세와 어긋난다」를 계산할 수 있다(`scene_state.stale`).

venv 파이썬으로 돈다(생성기와 토크나이저가 거기 있다):
  /Users/calmonion/.local/biblemap-imggen/.venv314/bin/python attempt.py --scene <id> --stage S1 --seeds 11

시드 규약(중요):
  · 배경·구역·능선 단계 — 시도 시드가 곧 장면 시드다. `--seeds <시드>`로 넘긴다.
  · **판 단계** — 장면 시드는 곁파일의 `sceneSeed`로 **고정**하고(접지가 그것을 쓴다),
    시도 시드는 판 시드로 `--plate-seeds <단계>=<시드>`에 넣는다.
  파일 이름이 겹치지 않게 라벨에 시도 시드를 실어 `t<시드>`로 준다.

거절하는 것:
  · `from`이 있는 단계(다듬기·지물) — 앞 단계 실루엣 기억(`drawn`)에 기대는데 재개는 그 기억을 잇지 못한다.
  · 앞 단계에 승인이 없는데 첫 단계가 아닌 경우 — 얹힐 캔버스가 없다.
  · 프롬프트가 77토큰을 넘는 경우 — 뒤가 조용히 잘린다(GPU를 쓰기 전에 막는다).
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import params  # noqa: E402
import derive_scene as ds  # noqa: E402
import scene_state as ss  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SIDE_DIR = os.path.join(HERE, "attempts")          # 명세와 섞이면 check_scenes.py가 명세로 읽는다
OUT = os.path.join(params.OUT_ROOT, "scene-tool")   # 이름은 params 정본과 겹치지 않게(게이트가 잡는다)


def side_path(scene):
    return os.path.join(SIDE_DIR, f"{scene}.json")


def load_side(scene, scene_seed=None):
    try:
        with open(side_path(scene), encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {"scene": scene, "sceneSeed": scene_seed, "attempts": []}


def save_side(side):
    os.makedirs(SIDE_DIR, exist_ok=True)
    with open(side_path(side["scene"]), "w", encoding="utf-8") as fh:
        json.dump(side, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def next_id(side):
    return f"a{len(side['attempts']) + 1:03d}"


def upstream_of(spec, stage_id):
    """직전 비건너뜀 단계의 **지금 승인** → {stage, attempt, seed} 또는 None(빈 종이).

    `scene_state.stale`이 재검토를 재는 기준과 같은 것을 본다 — 어긋나면 갓 그린 시도가 곧바로 재검토가 된다."""
    prev = None
    for st in ss.live_stages(spec):
        if st["id"] == stage_id:
            if prev is None:
                return None
            ap = prev.get("approved")
            if ap is None:
                sys.exit(f"앞 단계 {prev['id']}에 승인이 없다 — 얹힐 캔버스가 없다. 먼저 그 단계를 승인하라")
            return {"stage": prev["id"], "attempt": ap["attempt"], "seed": ap["seed"]}
        prev = st
    sys.exit(f"단계 {stage_id}를 명세에서 못 찾았다(건너뜀 단계일 수 있다)")


def canvas_of(side, up):
    by_id = {a["id"]: a for a in side["attempts"]}
    a = by_id.get(up["attempt"])
    if a is None:
        sys.exit(f"앞 단계 승인이 가리키는 시도 {up['attempt']}가 곁파일에 없다")
    img = (a.get("images") or {}).get(str(up["seed"]), {}).get("canvas")
    if not img or not os.path.exists(os.path.join(params.REPO_ROOT, img)):
        sys.exit(f"앞 단계 승인본 그림이 없다: {img}")
    return os.path.join(params.REPO_ROOT, img)


def check_tokens(derived):
    from transformers import CLIPTokenizer
    tok = CLIPTokenizer.from_pretrained(params.SDXL_BASE, subfolder="tokenizer")
    n, lim = len(tok(derived["prompt"]).input_ids), tok.model_max_length
    if n > lim:
        sys.exit(f"프롬프트가 한도를 넘었다({n}/{lim}, {n - lim}토큰 초과) — 조용히 잘리므로 그리지 않는다\n"
                 f"  + {derived['prompt']}")
    return {"n": n, "lim": lim}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--seeds", default="11", help="쉼표로 여러 시드. 판 단계면 판 시드다")
    ap.add_argument("--scene-seed", type=int, default=None,
                    help="곁파일이 없을 때 장면 시드를 정한다(기본 11). 이미 있으면 그 값을 쓴다")
    ap.add_argument("--by", default="cli")
    a = ap.parse_args()

    spec = ds.load(a.scene)
    stage = next((s for s in spec["stages"] if s["id"] == a.stage), None)
    if stage is None:
        sys.exit(f"단계 {a.stage}가 명세에 없다")
    if "from" in stage:
        sys.exit(f"단계 {a.stage}는 `from: {stage['from']}`이라 앞 단계 실루엣 기억에 기댄다 — "
                 f"재개로는 그릴 수 없다(계획 「하지 않을 것」)")
    if stage.get("skip"):
        sys.exit(f"단계 {a.stage}는 건너뜀이다")

    side = load_side(a.scene, a.scene_seed if a.scene_seed is not None else 11)
    if side.get("sceneSeed") is None:
        side["sceneSeed"] = a.scene_seed if a.scene_seed is not None else 11
    scene_seed = side["sceneSeed"]

    # 순서가 중요하다 — 앞 단계 승인부터 본다. 토크나이저 로드는 몇 초라, 얹힐 캔버스가 없는
    # 장면에서 그 값을 먼저 치르게 하지 않는다(계획 S3의 차례).
    up = upstream_of(spec, a.stage)
    canvas = canvas_of(side, up) if up else None

    derived = next(s for s in ds.stages(spec) if s["id"] == a.stage)
    tokens = check_tokens(derived)

    aid = next_id(side)
    out_dir = os.path.join(OUT, a.scene, aid)
    os.makedirs(out_dir, exist_ok=True)
    venv = sys.executable
    images, t0 = {}, time.time()
    for seed in [int(s) for s in a.seeds.split(",")]:
        label = f"t{seed}"     # 한 시도에 여러 시드를 돌려도 파일이 겹치지 않게 라벨에 싣는다
        cmd = [venv, "gen_scripture_scene.py", "--scene", a.scene, "--stages", a.stage,
               "--label", label, "--out", out_dir]
        if stage["kind"] == "plate":
            cmd += ["--seeds", str(scene_seed), "--plate-seeds", f"{a.stage}={seed}"]
        else:
            cmd += ["--seeds", str(seed)]
        if canvas:
            cmd += ["--canvas", canvas]
        print("· " + " ".join(cmd), flush=True)
        r = subprocess.run(cmd, cwd=HERE)
        if r.returncode != 0:
            sys.exit(f"생성기가 실패했다(종료코드 {r.returncode}) — 시도를 기록하지 않는다")
        canvas_seed = scene_seed if stage["kind"] == "plate" else seed
        rel = os.path.relpath(os.path.join(out_dir, f"{label}-{a.stage}-s{canvas_seed}.png"),
                              params.REPO_ROOT)
        one = {"canvas": rel}
        plate = os.path.join(out_dir, f"{label}-plate-{a.stage}-s{seed}.png")
        if os.path.exists(plate):
            one["plate"] = os.path.relpath(plate, params.REPO_ROOT)
        images[str(seed)] = one

    side["attempts"].append({
        "id": aid, "stage": a.stage, "seeds": [int(s) for s in a.seeds.split(",")],
        "prompt": stage["prompt"], "neg": list(stage.get("neg") or []),
        "region": list(spec["regions"][stage["region"]]),
        "upstream": up, "tokens": tokens,
        "startedAt": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "seconds": round(time.time() - t0, 1), "by": a.by, "images": images,
    })
    save_side(side)
    print(f"시도 {aid} 기록 · {a.stage} · 시드 {a.seeds} · {round(time.time() - t0)}s "
          f"· {tokens['n']}/{tokens['lim']}토큰 -> {os.path.relpath(side_path(a.scene), params.REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
