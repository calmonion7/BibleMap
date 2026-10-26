#!/usr/bin/env python3
"""task 354 — 로컬 영상 모델 파일럿: 승인 장면 그림 한 장 → 3초 영상(Wan 2.2 TI2V-5B·LTX-2.3 int4, 둘 다 MLX).

  python3 gen_video_pilot.py --prep                    # 입력 2장(1280×704 덮기+가운데 자르기)
  nohup python3 gen_video_pilot.py > ~/.local/biblemap-imggen/video-pilot.log 2>&1 &   # 8클립, 있으면 건너뜀
  ~/.local/biblemap-imggen/.venv-video/bin/python gen_video_pilot.py --metrics       # 기계 측정

고정 절은 notes/VIDEO-PILOT.md. 클립마다 별 프로세스로 띄워(/usr/bin/time -l) 끝나면 메모리를 반환한다 — 한 번에 하나.
산출 mp4·입력은 레포 밖 OUT(대량 커밋 안 함), metrics.json과 대표 클립 하나만 samples/video-pilot/.
"""
import argparse, glob, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, "samples", "video-pilot")
METRICS = os.path.join(SAMPLES, "metrics.json")
RT = os.path.expanduser("~/.local/biblemap-imggen")
OUT = os.path.join(RT, "video-pilot")
VENV = os.path.join(RT, ".venv-video", "bin")
WAN_DIR = os.path.join(RT, "models-video", "Wan2.2-TI2V-5B-MLX")
# 저장소 id를 넘기면 일부러 뺀 transformer-distilled.safetensors(안 씀)까지 받으려 하므로 로컬 스냅숏을 넘긴다.
LTX_MODEL = (glob.glob(os.path.expanduser("~/.cache/huggingface/hub/models--dgrauet--ltx-2.3-mlx-q4/snapshots/*"))
             or ["dgrauet/ltx-2.3-mlx-q4"])[0]

W, H, FRAMES, FPS = 1280, 704, 73, 24
SEEDS = [42, 23]
SCENES = {
    "gilgal": ("samples/face-widen/approved-gilgal.png",
               "Slow gentle camera push-in. The crowd's raised hands sway slightly, the thin smoke rises and curls "
               "from the stone altar, robes stir in a light breeze. The two men in front stay still and calm. "
               "Pencil line drawing with watercolor wash on cream paper, hand-drawn texture kept throughout."),
    "engedi": ("samples/engedi-final/approved-engedi-c.png",
               "Slow gentle camera push-in. The kneeling man on the left slowly lifts the cut corner of the cloak "
               "with his knife; the crouching man on the right keeps looking toward the bright cave mouth and "
               "breathes slowly. Dust drifts in the light from the cave mouth. Pencil line drawing with sepia wash, "
               "hand-drawn texture kept throughout."),
}
# 두 모델 기본 부정문은 화풍을 밀어낸다(Wan 「风格·作品·画作·画面」, LTX 「cartoonish rendering, stylized filters,
# grainy texture」) → 결함 전용 하나를 두 모델에 같이 쓴다(고정 절).
NEGATIVE = ("blurry, flickering, jittery movement, morphing, deformed face, distorted proportions, extra limbs, "
            "disfigured hands, scene cut, photorealistic, 3D CGI look")
# Wan은 공식 기본값(config: 40단계·unipc·guide 5·shift 5) — S0 시험 실측 49.8 s/단계로 클립당 약 42분, 감당 가능.
# Turbo LoRA(4단계)는 라이선스 미표기라 쓰지 않는다(notes 「설치」).
WAN_ARGS = []
LTX_ARGS = ["--two-stage", "--low-ram", "--no-audio"]


def input_path(scene):
    return os.path.join(OUT, f"input-{scene}.png")   # --prep로 재현 — 레포에 두지 않는다


def prep():
    from PIL import Image
    os.makedirs(SAMPLES, exist_ok=True)
    for scene, (src, _) in SCENES.items():
        im = Image.open(os.path.join(HERE, src)).convert("RGB")
        s = max(W / im.width, H / im.height)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        x, y = (im.width - W) // 2, (im.height - H) // 2
        os.makedirs(OUT, exist_ok=True)
        im.crop((x, y, x + W, y + H)).save(input_path(scene))
        print(f"[VideoPilot] {scene}: {src} → {input_path(scene)}")


def clips():
    return [(m, sc, sd) for m in ("ltx", "wan") for sc in SCENES for sd in SEEDS]


def clip_path(model, scene, seed):
    return os.path.join(OUT, f"{model}-{scene}-s{seed}.mp4")


def command(model, scene, seed, out):
    prompt = SCENES[scene][1]
    if model == "wan":
        return [os.path.join(VENV, "python"), "-m", "mlx_video.models.wan_2.generate", "--model-dir", WAN_DIR,
                "--prompt", prompt, "--negative-prompt", NEGATIVE, "--image", input_path(scene),
                "--width", str(W), "--height", str(H), "--num-frames", str(FRAMES), "--seed", str(seed),
                "--output-path", out, *WAN_ARGS]
    return [os.path.join(VENV, "ltx-2-mlx"), "generate", "-p", prompt, "--negative-prompt", NEGATIVE,
            "-o", out, "-H", str(H), "-W", str(W), "-f", str(FRAMES), "--frame-rate", str(FPS),
            "-s", str(seed), "--image", input_path(scene), "0", "1.0", "--model", LTX_MODEL, *LTX_ARGS]


def load():
    if os.path.exists(METRICS):
        return json.load(open(METRICS))
    return {"fixed": {"size": [W, H], "frames": FRAMES, "fps": FPS, "seeds": SEEDS, "negative": NEGATIVE,
                      "wan_args": WAN_ARGS, "ltx_args": LTX_ARGS, "ltx_model": LTX_MODEL},
            "clips": [{"model": m, "scene": sc, "seed": sd, "status": "pending"} for m, sc, sd in clips()]}


def save(m):
    os.makedirs(SAMPLES, exist_ok=True)
    json.dump(m, open(METRICS, "w"), ensure_ascii=False, indent=1)


def generate(only=None):
    os.makedirs(OUT, exist_ok=True)
    m = load()
    for c in m["clips"]:
        out = clip_path(c["model"], c["scene"], c["seed"])
        if only and c["model"] != only:
            continue
        if os.path.exists(out):
            print(f"[VideoPilot] 있음, 건너뜀: {out}")
            continue
        log = out[:-4] + ".log"
        print(f"[VideoPilot] 생성: {os.path.basename(out)}", flush=True)
        t0 = time.time()
        with open(log, "w") as f:
            r = subprocess.run(["/usr/bin/time", "-l", *command(c["model"], c["scene"], c["seed"], out)],
                               stdout=f, stderr=subprocess.STDOUT, cwd=OUT)
        sec = round(time.time() - t0, 1)
        text = open(log, errors="replace").read()
        rss = re.search(r"(\d+)\s+maximum resident set size", text)
        peak = re.search(r"(\d+)\s+peak memory footprint", text)
        c.update(sec=sec, peak_rss_gb=round(int(rss.group(1)) / 2**30, 2) if rss else None,
                 peak_footprint_gb=round(int(peak.group(1)) / 2**30, 2) if peak else None)
        if r.returncode == 0 and os.path.exists(out):
            c["status"] = "ok"
            c.pop("reason", None)
        else:
            c["status"] = "failed"
            c["reason"] = f"exit {r.returncode}: " + " | ".join(text.strip().splitlines()[-3:])[-300:]
        print(f"[VideoPilot] {c['status']} {sec}s", flush=True)
        save(m)


def frames_of(path):
    import cv2
    import numpy as np
    cap, out = cv2.VideoCapture(path), []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        out.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
    return np.stack(out)


def ink(rgb):
    import tempfile
    from PIL import Image
    import judge_style
    with tempfile.NamedTemporaryFile(suffix=".png") as t:
        Image.fromarray(rgb).save(t.name)
        return judge_style.style_metrics(t.name)["ink"]


def metrics():
    import numpy as np
    m = load()
    last = {}
    for c in m["clips"]:
        out = clip_path(c["model"], c["scene"], c["seed"])
        if c["status"] != "ok":
            continue
        fr = frames_of(out)
        gray = fr.mean(axis=3) / 255.0
        std = gray.reshape(len(gray), -1).std(axis=1)
        diff = np.abs(np.diff(gray, axis=0)).reshape(len(gray) - 1, -1).mean(axis=1)
        med = float(np.median(diff))
        broken = set(np.where(std < 0.7 * std[0])[0].tolist())
        broken |= {i + 1 for i in np.where((diff > 5 * med) | (diff > 0.25))[0].tolist()}
        i0, i1 = ink(fr[0]), ink(fr[-1])
        last[(c["model"], c["scene"], c["seed"])] = i1
        c.update(n_frames=len(fr), std_first=round(float(std[0]), 4), std_min=round(float(std.min()), 4),
                 diff_median=round(med, 4), diff_max=round(float(diff.max()), 4), broken_frames=len(broken),
                 ink_first=round(i0, 4), ink_last=round(i1, 4), ink_drift=round(abs(i1 - i0), 4))
    for c in m["clips"]:
        k = [v for (mo, sc, sd), v in last.items() if mo == c["model"] and sc == c["scene"]]
        if c["status"] == "ok" and len(k) == 2:
            c["ink_seed_gap"] = round(abs(k[0] - k[1]), 4)
    ok = [c["sec"] for c in m["clips"] if c["status"] == "ok"]
    m["throughput"] = {mo: {"mean_sec": round(sum(s) / len(s), 1), "hours_275": round(275 * sum(s) / len(s) / 3600, 1)}
                       for mo in ("wan", "ltx")
                       for s in [[c["sec"] for c in m["clips"] if c["model"] == mo and c["status"] == "ok"]] if s}
    save(m)
    print(json.dumps(m["throughput"], ensure_ascii=False))
    for c in m["clips"]:
        print(c["model"], c["scene"], c["seed"], c["status"], c.get("sec"), c.get("broken_frames"),
              c.get("ink_drift"), c.get("ink_seed_gap"))
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prep", action="store_true")
    ap.add_argument("--metrics", action="store_true")
    ap.add_argument("--only", choices=["wan", "ltx"])
    a = ap.parse_args()
    if a.prep:
        prep()
    elif a.metrics:
        sys.path.insert(0, HERE)
        metrics()
    else:
        generate(a.only)
